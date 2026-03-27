"""Weekly Tests Blueprint."""
import json
from datetime import datetime
from flask import Blueprint, request
from app import db
from app.models import WeeklyTest, WeeklyTestQuestion, WeeklyTestAttempt, Question
from app.utils.response import ok, created, not_found, paginate, error
from app.utils.jwt_helper import admin_required, current_user_id, current_user_role, require_session
from app.utils.cache_helper import cache_key_with_user
from app.utils.google_forms import GoogleFormsError, parse_google_form_id
from app.utils.google_forms_sync import (
    build_internal_review_payload,
    get_result_for_user,
    import_google_form_questions,
    reset_google_entity_state,
    sync_google_form_results,
)
from app import cache

weekly_tests_bp = Blueprint('weekly_tests', __name__)

@weekly_tests_bp.get('')
@require_session
@cache.cached(timeout=300, query_string=True)
def list_tests():
    subject = request.args.get('subject', '')
    page    = int(request.args.get('page', 1))
    q = WeeklyTest.query
    if subject:
        q = q.filter(WeeklyTest.subject.ilike(f'%{subject}%'))
    return paginate(q.order_by(WeeklyTest.scheduled_at.desc()), page, 20)


@weekly_tests_bp.get('/<int:tid>')
@require_session
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def get_test(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    return ok(test.to_dict(include_questions=True, include_google=current_user_role() == 'admin'))


@weekly_tests_bp.post('')
@admin_required
def create_test():
    data = request.get_json(silent=True) or {}
    forms_edit_url = data.get('forms_edit_url') if 'forms_edit_url' in data else data.get('forms_url')
    forms_view_url = data.get('forms_view_url')
    test = WeeklyTest(
        title=data.get('title', 'Untitled'),
        subject=data.get('subject', 'General'),
        duration_min=data.get('duration_min', 60),
        status=data.get('status', 'scheduled'),
        forms_url=(forms_edit_url or None),
        forms_view_url=(forms_view_url or None),
        google_match_mode=data.get('google_match_mode') or 'email_then_student_id',
        google_student_id_question_id=data.get('google_student_id_question_id') or None,
        scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
    )
    db.session.add(test)
    db.session.flush()
    for idx, q in enumerate(data.get('questions', [])):
        # Provide Question creation or linking
        if 'question_id' in q:
            q_id = q['question_id']
        else:
            new_q = Question(
                subject=data.get('subject', 'General'),
                text=q.get('text', ''),
                options=json.dumps(q.get('options', [])),
                answer_index=q.get('answer_index', 0),
            )
            db.session.add(new_q)
            db.session.flush()
            q_id = new_q.id
            
        qobj = WeeklyTestQuestion(
            test_id=test.id,
            question_id=q_id,
            order_index=idx
        )
        db.session.add(qobj)
    db.session.commit()
    cache.clear()
    return created(test.to_dict(include_questions=True, include_google=True))


@weekly_tests_bp.patch('/<int:tid>')
@admin_required
def update_test(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    data = request.get_json(silent=True) or {}
    previous_forms_url = test.forms_url or ''
    for f in ('title', 'subject', 'duration_min', 'status', 'forms_url', 'forms_view_url', 'google_match_mode', 'google_student_id_question_id'):
        if f in data:
            if f in ('forms_url', 'forms_view_url'):
                setattr(test, f, data[f] or None)
            else:
                setattr(test, f, data[f])
    if 'forms_edit_url' in data:
        test.forms_url = data.get('forms_edit_url') or None
    if 'scheduled_at' in data:
        test.scheduled_at = datetime.fromisoformat(data['scheduled_at']) if data['scheduled_at'] else None
    try:
        previous_form_id = parse_google_form_id(previous_forms_url) if previous_forms_url else ''
        next_form_id = parse_google_form_id(test.forms_url) if test.forms_url else ''
    except GoogleFormsError:
        previous_form_id = ''
        next_form_id = ''
    if previous_forms_url and previous_form_id != next_form_id:
        reset_google_entity_state('weekly_test', test)
    if not test.forms_url:
        test.google_student_id_question_id = None
    if 'questions' in data and not (test.forms_url or '').strip():
        WeeklyTestQuestion.query.filter_by(test_id=test.id).delete(synchronize_session=False)
        for idx, q in enumerate(data.get('questions', [])):
            new_q = Question(
                subject=test.subject or 'General',
                text=q.get('text', ''),
                options=json.dumps(q.get('options', [])),
                answer_index=q.get('answer_index', 0),
            )
            db.session.add(new_q)
            db.session.flush()
            db.session.add(WeeklyTestQuestion(
                test_id=test.id,
                question_id=new_q.id,
                order_index=idx,
            ))
    db.session.commit()
    cache.clear()
    return ok(test.to_dict(include_questions=True, include_google=True), 'Test updated')


@weekly_tests_bp.get('/<int:tid>/participants')
@admin_required
def get_participants(tid: int):
    attempts = WeeklyTestAttempt.query.filter_by(test_id=tid).order_by(WeeklyTestAttempt.submitted_at.desc()).all()
    return ok([a.to_dict() for a in attempts])


@weekly_tests_bp.post('/<int:tid>/attempts')
@require_session
def submit_attempt(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    data = request.get_json(silent=True) or {}
    answers = data.get('answers', [])
    attempt = WeeklyTestAttempt(
        user_id=current_user_id(),
        test_id=tid,
        score=data.get('score', 0),
        total=data.get('total', len(test.questions)),
        answers=json.dumps(answers),
        source='internal',
        review_payload=json.dumps(build_internal_review_payload(test, answers)),
    )
    db.session.add(attempt)
    db.session.commit()
    return created(attempt.to_dict())


@weekly_tests_bp.get('/<int:tid>/attempts/me')
@require_session
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def my_attempt(tid: int):
    attempt = WeeklyTestAttempt.query.filter_by(
        user_id=current_user_id(), test_id=tid
    ).order_by(WeeklyTestAttempt.submitted_at.desc()).first()
    if not attempt:
        return not_found('Attempt')
    return ok(attempt.to_dict())


@weekly_tests_bp.post('/<int:tid>/google/import-questions')
@admin_required
def import_google_questions(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    try:
        summary = import_google_form_questions('weekly_test', test)
    except GoogleFormsError as err:
        db.session.rollback()
        return error(str(err))
    cache.clear()
    return ok({
        'item': test.to_dict(include_questions=True, include_google=True),
        'summary': summary,
    }, 'Google Form questions imported')


@weekly_tests_bp.post('/<int:tid>/google/sync-results')
@admin_required
def sync_google_results(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    try:
        summary = sync_google_form_results('weekly_test', test)
    except GoogleFormsError as err:
        db.session.rollback()
        return error(str(err))
    cache.clear()
    return ok({
        'item': test.to_dict(include_questions=True, include_google=True),
        'summary': summary,
    }, 'Google Form results synced')


@weekly_tests_bp.get('/<int:tid>/results/me')
@require_session
def my_result(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    return ok(get_result_for_user('weekly_test', test, current_user_id()))
