"""Model Sets Blueprint."""
import json
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import ModelSet, ModelSetAttempt, ModelSetQuestion, Question
from app.utils.response import ok, error, created, not_found, paginate
from app.utils.jwt_helper import admin_required, current_user_id

model_sets_bp = Blueprint('model_sets', __name__)


@model_sets_bp.get('/targets')
@jwt_required()
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
def get_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    return ok(ms.to_dict(include_questions=True))


@model_sets_bp.post('')
@admin_required
def create_model_set():
    data = request.get_json(silent=True) or {}
    ms = ModelSet(
        title=data.get('title', 'Untitled'),
        difficulty=data.get('difficulty', 'Medium'),
        duration_min=data.get('duration_min', 120),
        total_questions=data.get('total_questions', 100),
        status=data.get('status', 'draft'),
        targets=json.dumps(data.get('targets', ['IOE'])),
        forms_url=data.get('forms_url') or None,
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
    return created(ms.to_dict(include_questions=True))


@model_sets_bp.patch('/<int:mid>')
@admin_required
def update_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    data = request.get_json(silent=True) or {}
    for field in ('title', 'difficulty', 'duration_min', 'total_questions', 'status', 'forms_url'):
        if field in data:
            if field == 'forms_url':
                setattr(ms, field, data[field] or None)
            else:
                setattr(ms, field, data[field])
    if 'targets' in data:
        ms.targets = json.dumps(data['targets'])
    db.session.commit()
    return ok(ms.to_dict(), 'Model Set updated')


@model_sets_bp.delete('/<int:mid>')
@admin_required
def delete_model_set(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    db.session.delete(ms)
    db.session.commit()
    return ok(message='Model Set deleted')


@model_sets_bp.post('/<int:mid>/attempts')
@jwt_required()
def submit_attempt(mid: int):
    ms = ModelSet.query.get(mid)
    if not ms:
        return not_found('Model Set')
    data = request.get_json(silent=True) or {}
    attempt = ModelSetAttempt(
        user_id=current_user_id(),
        model_set_id=mid,
        score=data.get('score', 0),
        total=data.get('total', ms.total_questions),
        answers=json.dumps(data.get('answers', [])),
    )
    db.session.add(attempt)
    db.session.commit()
    return created(attempt.to_dict(), 'Attempt saved')


@model_sets_bp.get('/<int:mid>/attempts/me')
@jwt_required()
def my_attempts(mid: int):
    attempts = ModelSetAttempt.query.filter_by(
        user_id=current_user_id(), model_set_id=mid
    ).order_by(ModelSetAttempt.completed_at.desc()).all()
    return ok([a.to_dict() for a in attempts])
