"""Model Sets Blueprint."""
import json
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import ModelSet, ModelSetAttempt, ModelSetQuestion, Question
from app.utils.response import ok, error, created, not_found, paginate
from app.utils.jwt_helper import admin_required, current_user_id, current_user_role
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

model_sets_bp = Blueprint('model_sets', __name__)


@model_sets_bp.get('/targets')
@jwt_required()
@cache.cached(timeout=300, query_string=True)
def list_targets():
    """Return distinct target exam values across all model sets, plus defaults."""
    default_exams = ['St. Xavier\'s', 'SOS', 'KMC', 'CCRC', 'NIST']
    rows = ModelSet.query.with_entities(ModelSet.targets).all()
    seen = set(default_exams)
    for (targets_str,) in rows:
        try:
            for exam in json.loads(targets_str or '[]'):
                if exam:
                    seen.add(exam.strip())
        except Exception:
            pass
    return ok(sorted(seen))


@model_sets_bp.get('')
@jwt_required()
@cache.cached(timeout=300, query_string=True)
def list_model_sets():
    tab    = request.args.get('tab', 'all')
    sort   = request.args.get('sort', 'newest')
    search = request.args.get('search', '').strip()
    page   = int(request.args.get('page', 1))
    limit  = int(request.args.get('limit', 20))
    # admin can request status=all or status=draft; default: published only
    status_filter = request.args.get('status', 'published')

    q = ModelSet.query
    if status_filter != 'all':
        q = q.filter_by(status=status_filter)

    if tab and tab != 'all':
        q = q.filter(ModelSet.targets.ilike(f'%{tab.upper()}%'))

    if search:
        q = q.filter(ModelSet.title.ilike(f'%{search}%'))

    if sort == 'oldest':
        q = q.order_by(ModelSet.created_at.asc())
    else:
        q = q.order_by(ModelSet.created_at.desc())

    return paginate(q, page, limit)


@model_sets_bp.get('/<int:mid>')
@jwt_required()
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def get_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    return ok(ms.to_dict(include_questions=True, include_google=current_user_role() == 'admin'))


@model_sets_bp.post('')
@admin_required
def create_model_set():
    data = request.get_json(silent=True) or {}
    forms_edit_url = data.get('forms_edit_url') if 'forms_edit_url' in data else data.get('forms_url')
    forms_view_url = data.get('forms_view_url')
    ms = ModelSet(
        title=data.get('title', 'Untitled'),
        difficulty=data.get('difficulty', 'Medium'),
        duration_min=data.get('duration_min', 120),
        total_questions=data.get('total_questions', 100),
        status=data.get('status', 'draft'),
        targets=json.dumps(data.get('targets', ['IOE'])),
        forms_url=forms_edit_url or None,
        forms_view_url=forms_view_url or None,
        google_match_mode=data.get('google_match_mode') or 'email_then_student_id',
        google_student_id_question_id=data.get('google_student_id_question_id') or None,
    )
    db.session.add(ms)
    db.session.flush()
    
    for idx, q in enumerate(data.get('questions', [])):
        if 'question_id' in q:
            q_id = q['question_id']
        else:
            new_q = Question(
                subject=q.get('subject', 'General'),
                text=q.get('text', ''),
                options=json.dumps(q.get('options', [])),
                answer_index=q.get('answer_index', 0),
            )
            db.session.add(new_q)
            db.session.flush()
            q_id = new_q.id
            
        qobj = ModelSetQuestion(
            model_set_id=ms.id,
            question_id=q_id,
            order_index=idx
        )
        db.session.add(qobj)
    
    db.session.commit()
    cache.clear()
    return created(ms.to_dict(include_questions=True, include_google=True))


@model_sets_bp.patch('/<int:mid>')
@admin_required
def update_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    data = request.get_json(silent=True) or {}
    previous_forms_url = ms.forms_url or ''
    for field in ('title', 'difficulty', 'duration_min', 'total_questions', 'status', 'forms_url', 'forms_view_url', 'google_match_mode', 'google_student_id_question_id'):
        if field in data:
            if field in ('forms_url', 'forms_view_url'):
                setattr(ms, field, data[field] or None)
            else:
                setattr(ms, field, data[field])
    if 'forms_edit_url' in data:
        ms.forms_url = data.get('forms_edit_url') or None
    if 'targets' in data:
        ms.targets = json.dumps(data['targets'])
    try:
        previous_form_id = parse_google_form_id(previous_forms_url) if previous_forms_url else ''
        next_form_id = parse_google_form_id(ms.forms_url) if ms.forms_url else ''
    except GoogleFormsError:
        previous_form_id = ''
        next_form_id = ''
    if previous_forms_url and previous_form_id != next_form_id:
        reset_google_entity_state('model_set', ms)
    if not ms.forms_url:
        ms.google_student_id_question_id = None
    db.session.commit()
    cache.clear()
    return ok(ms.to_dict(include_questions=True, include_google=True), 'Model Set updated')


@model_sets_bp.delete('/<int:mid>')
@admin_required
def delete_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    db.session.delete(ms)
    db.session.commit()
    cache.clear()
    return ok(message='Model Set deleted')


@model_sets_bp.post('/<int:mid>/attempts')
@jwt_required()
def submit_attempt(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    data = request.get_json(silent=True) or {}
    answers = data.get('answers', [])
    attempt = ModelSetAttempt(
        user_id=current_user_id(),
        model_set_id=mid,
        score=data.get('score', 0),
        total=data.get('total', ms.total_questions),
        answers=json.dumps(answers),
        source='internal',
        review_payload=json.dumps(build_internal_review_payload(ms, answers)),
    )
    db.session.add(attempt)
    db.session.commit()
    return created(attempt.to_dict(), 'Attempt saved')


@model_sets_bp.get('/<int:mid>/attempts/me')
@jwt_required()
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def my_attempts(mid: int):
    attempts = ModelSetAttempt.query.filter_by(
        user_id=current_user_id(), model_set_id=mid
    ).order_by(ModelSetAttempt.completed_at.desc()).all()
    return ok([a.to_dict() for a in attempts])


@model_sets_bp.post('/<int:mid>/google/import-questions')
@admin_required
def import_google_questions(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    try:
        summary = import_google_form_questions('model_set', ms)
    except GoogleFormsError as err:
        db.session.rollback()
        return error(str(err))
    cache.clear()
    return ok({
        'item': ms.to_dict(include_questions=True, include_google=True),
        'summary': summary,
    }, 'Google Form questions imported')


@model_sets_bp.post('/<int:mid>/google/sync-results')
@admin_required
def sync_google_results(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    try:
        summary = sync_google_form_results('model_set', ms)
    except GoogleFormsError as err:
        db.session.rollback()
        return error(str(err))
    cache.clear()
    return ok({
        'item': ms.to_dict(include_questions=True, include_google=True),
        'summary': summary,
    }, 'Google Form results synced')


@model_sets_bp.get('/<int:mid>/results/me')
@jwt_required()
def my_result(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    return ok(get_result_for_user('model_set', ms, current_user_id()))
