"""Live Classes Blueprint."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import LiveClass, LiveClassAttendance, LiveClassMessage
from app.utils.response import ok, created, not_found, paginate
from app.utils.jwt_helper import admin_required, current_user_id
from app.utils.cache_helper import cache_key_with_user
from app import cache
from datetime import datetime
from sqlalchemy import case

live_classes_bp = Blueprint('live_classes', __name__)


@live_classes_bp.get('')
@jwt_required()
@cache.cached(timeout=300, query_string=True)
def list_classes():
    status = request.args.get('status', '')
    page   = int(request.args.get('page', 1))
    q = LiveClass.query
    if status:
        if status == 'upcoming':
            q = q.filter(LiveClass.status.in_(['scheduled', 'upcoming']))
        else:
            q = q.filter_by(status=status)
    return paginate(q.order_by(
        case(
            (LiveClass.status == 'live', 0),
            (LiveClass.status.in_(['scheduled', 'upcoming']), 1),
            (LiveClass.status == 'completed', 2),
            else_=3,
        ),
        LiveClass.created_at.desc(),
        LiveClass.scheduled_at.desc(),
        LiveClass.id.desc(),
    ), page, 20)


@live_classes_bp.get('/<int:cid>')
@jwt_required()
@cache.cached(timeout=300)
def get_class(cid: int):
    cls = LiveClass.query.get(cid)
    if not cls:
        return not_found('Live Class')
    return ok(cls.to_dict())


@live_classes_bp.post('')
@admin_required
def create_class():
    data = request.get_json(silent=True) or {}
    cls = LiveClass(
        title=data.get('title', 'Untitled'),
        teacher=data.get('teacher', 'TBD'),
        subject=data.get('subject', 'General'),
        duration_min=data.get('duration_min', 60),
        status=data.get('status', 'scheduled'),
        stream_url=data.get('stream_url'),
        scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
    )
    db.session.add(cls)
    db.session.commit()
    cache.clear()
    return created(cls.to_dict())


@live_classes_bp.patch('/<int:cid>')
@admin_required
def update_class(cid: int):
    cls = LiveClass.query.get(cid)
    if not cls:
        return not_found('Live Class')
    data = request.get_json(silent=True) or {}
    for f in ('title', 'teacher', 'subject', 'duration_min', 'status', 'watchers', 'stream_url'):
        if f in data:
            setattr(cls, f, data[f])
    if 'scheduled_at' in data:
        cls.scheduled_at = datetime.fromisoformat(data['scheduled_at']) if data['scheduled_at'] else None
    db.session.commit()
    cache.clear()
    return ok(cls.to_dict(), 'Live class updated')


@live_classes_bp.post('/<int:cid>/join')
@jwt_required()
def join_class(cid: int):
    cls = LiveClass.query.get(cid)
    if not cls:
        return not_found('Live Class')
    existing = LiveClassAttendance.query.filter_by(
        user_id=current_user_id(), class_id=cid
    ).first()
    if not existing:
        attendance = LiveClassAttendance(user_id=current_user_id(), class_id=cid)
        cls.watchers = (cls.watchers or 0) + 1
        db.session.add(attendance)
        db.session.commit()
        cache.clear()
    return ok({'class_id': cid, 'joined': True})


@live_classes_bp.get('/attendance/me')
@jwt_required()
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def my_attendance():
    records = LiveClassAttendance.query.filter_by(user_id=current_user_id()).all()
    return ok([{'class_id': r.class_id, 'joined_at': r.joined_at.isoformat()} for r in records])


@live_classes_bp.get('/<int:cid>/messages')
@jwt_required()
@cache.cached(timeout=30, make_cache_key=cache_key_with_user)
def get_messages(cid: int):
    # Verify the class exists
    cls = LiveClass.query.get(cid)
    if not cls:
        return not_found('Live Class')

    limit  = int(request.args.get('limit', 30))
    before = request.args.get('before')   # message id cursor
    q = LiveClassMessage.query.filter_by(class_id=cid)
    if before:
        q = q.filter(LiveClassMessage.id < int(before))
        
    messages = q.order_by(LiveClassMessage.created_at.desc()).limit(limit).all()
    return ok([m.to_dict() for m in reversed(messages)])
