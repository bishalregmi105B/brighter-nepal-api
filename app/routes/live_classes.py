"""Live Classes Blueprint."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import LiveClass, LiveClassAttendance
from app.utils.response import ok, created, not_found, paginate
from app.utils.jwt_helper import admin_required, current_user_id
from datetime import datetime

live_classes_bp = Blueprint('live_classes', __name__)


@live_classes_bp.get('')
@jwt_required()
def list_classes():
    status = request.args.get('status', '')
    page   = int(request.args.get('page', 1))
    q = LiveClass.query
    if status:
        q = q.filter_by(status=status)
    return paginate(q.order_by(LiveClass.scheduled_at.desc()), page, 20)


@live_classes_bp.get('/<int:cid>')
@jwt_required()
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
        cls.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    db.session.commit()
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
    return ok({'class_id': cid, 'joined': True})


@live_classes_bp.get('/attendance/me')
@jwt_required()
def my_attendance():
    records = LiveClassAttendance.query.filter_by(user_id=current_user_id()).all()
    return ok([{'class_id': r.class_id, 'joined_at': r.joined_at.isoformat()} for r in records])
