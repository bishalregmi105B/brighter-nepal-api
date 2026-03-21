"""Groups Blueprint."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import Group, GroupMessage, User
from app.utils.response import ok, created, not_found, error, forbidden
from app.utils.jwt_helper import admin_required, current_user_id

groups_bp = Blueprint('groups', __name__)


@groups_bp.get('/mine')
@jwt_required()
def my_group():
    """Returns the single group the student is assigned to by admin."""
    user = User.query.get(current_user_id())
    if not user or not user.group_id:
        return not_found('Group')
    group = Group.query.get(user.group_id)
    if not group:
        return not_found('Group')
    return ok(group.to_dict())


def __check_group_access(gid: int) -> bool:
    user = User.query.get(current_user_id())
    if not user:
        return False
    if user.role == 'admin':
        return True
    return user.group_id == gid


@groups_bp.get('/<int:gid>')
@jwt_required()
def get_group(gid: int):
    if not __check_group_access(gid):
        return forbidden()
    group = Group.query.get(gid)
    if not group:
        return not_found('Group')
    return ok(group.to_dict())


@groups_bp.get('/<int:gid>/messages')
@jwt_required()
def get_messages(gid: int):
    if not __check_group_access(gid):
        return forbidden()
    limit  = int(request.args.get('limit', 30))
    before = request.args.get('before')   # message id cursor
    q = GroupMessage.query.filter_by(group_id=gid)
    if before:
        q = q.filter(GroupMessage.id < int(before))
    messages = q.order_by(GroupMessage.created_at.desc()).limit(limit).all()
    return ok([m.to_dict() for m in reversed(messages)])


@groups_bp.post('/<int:gid>/messages')
@jwt_required()
def send_message(gid: int):
    if not __check_group_access(gid):
        return forbidden()
    group = Group.query.get(gid)
    if not group:
        return not_found('Group')
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return error('Message text required')
    msg = GroupMessage(group_id=gid, user_id=current_user_id(), text=text)
    db.session.add(msg)
    db.session.commit()
    return created(msg.to_dict())


@groups_bp.post('/<int:gid>/messages/image')
@jwt_required()
def send_image(gid: int):
    """Stores an image URL (client uploads to cloud, sends URL here)."""
    if not __check_group_access(gid):
        return forbidden()
    group = Group.query.get(gid)
    if not group:
        return not_found('Group')
    data = request.get_json(silent=True) or {}
    image_url = data.get('image_url', '')
    if not image_url:
        return error('image_url required')
    msg = GroupMessage(group_id=gid, user_id=current_user_id(), image_url=image_url)
    db.session.add(msg)
    db.session.commit()
    return created(msg.to_dict())


@groups_bp.get('')
@admin_required
def get_all_groups():
    groups = Group.query.order_by(Group.created_at.desc()).all()
    return ok({'items': [g.to_dict() for g in groups]})


# Admin: assign a group to a student
@groups_bp.post('')
@admin_required
def create_group():
    data = request.get_json(silent=True) or {}
    group = Group(
        name=data.get('name', 'New Group'),
        description=data.get('description', ''),
        member_count=data.get('member_count', 0),
    )
    db.session.add(group)
    db.session.commit()
    return created(group.to_dict())
