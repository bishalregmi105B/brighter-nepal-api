"""Weekly Tests Blueprint."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import WeeklyTest, WeeklyTestQuestion, WeeklyTestAttempt
from app.utils.response import ok, created, not_found, paginate
from app.utils.jwt_helper import admin_required, current_user_id
from datetime import datetime
import json

weekly_tests_bp = Blueprint('weekly_tests', __name__)


@weekly_tests_bp.get('')
@jwt_required()
def list_tests():
    subject = request.args.get('subject', '')
    page    = int(request.args.get('page', 1))
    q = WeeklyTest.query
    if subject:
        q = q.filter(WeeklyTest.subject.ilike(f'%{subject}%'))
    return paginate(q.order_by(WeeklyTest.scheduled_at.desc()), page, 20)


@weekly_tests_bp.get('/<int:tid>')
@jwt_required()
def get_test(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    return ok(test.to_dict(include_questions=True))


@weekly_tests_bp.post('')
@admin_required
def create_test():
    data = request.get_json(silent=True) or {}
    test = WeeklyTest(
        title=data.get('title', 'Untitled'),
        subject=data.get('subject', 'General'),
        duration_min=data.get('duration_min', 60),
        status=data.get('status', 'scheduled'),
        scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
    )
    db.session.add(test)
    db.session.flush()
    for q in data.get('questions', []):
        qobj = WeeklyTestQuestion(
            test_id=test.id,
            text=q.get('text', ''),
            options=json.dumps(q.get('options', [])),
            answer_index=q.get('answer_index', 0),
        )
        db.session.add(qobj)
    db.session.commit()
    return created(test.to_dict(include_questions=True))


@weekly_tests_bp.patch('/<int:tid>')
@admin_required
def update_test(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    data = request.get_json(silent=True) or {}
    for f in ('title', 'subject', 'duration_min', 'status'):
        if f in data:
            setattr(test, f, data[f])
    if 'scheduled_at' in data:
        test.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    db.session.commit()
    return ok(test.to_dict(), 'Test updated')


@weekly_tests_bp.get('/<int:tid>/participants')
@admin_required
def get_participants(tid: int):
    attempts = WeeklyTestAttempt.query.filter_by(test_id=tid).all()
    return ok([a.to_dict() for a in attempts])


@weekly_tests_bp.post('/<int:tid>/attempts')
@jwt_required()
def submit_attempt(tid: int):
    test = WeeklyTest.query.get(tid)
    if not test:
        return not_found('Weekly Test')
    data = request.get_json(silent=True) or {}
    attempt = WeeklyTestAttempt(
        user_id=current_user_id(),
        test_id=tid,
        score=data.get('score', 0),
        total=data.get('total', len(test.questions)),
        answers=json.dumps(data.get('answers', [])),
    )
    db.session.add(attempt)
    db.session.commit()
    return created(attempt.to_dict())


@weekly_tests_bp.get('/<int:tid>/attempts/me')
@jwt_required()
def my_attempt(tid: int):
    attempt = WeeklyTestAttempt.query.filter_by(
        user_id=current_user_id(), test_id=tid
    ).order_by(WeeklyTestAttempt.submitted_at.desc()).first()
    if not attempt:
        return not_found('Attempt')
    return ok(attempt.to_dict())
