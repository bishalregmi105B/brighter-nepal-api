"""Users Blueprint — admin CRUD for user accounts."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import User
from app.utils.response import ok, error, not_found, paginate
from app.utils.jwt_helper import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.get('')
@admin_required
def list_users():
    tab    = request.args.get('tab', 'all')       # all | paid | trial
    search = request.args.get('search', '').strip()
    page   = int(request.args.get('page', 1))
    limit  = int(request.args.get('limit', 20))

    q = User.query
    if tab in ('paid', 'trial'):
        q = q.filter_by(plan=tab)
    if search:
        q = q.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))
    return paginate(q.order_by(User.created_at.desc()), page, limit)


@users_bp.get('/<int:uid>')
@admin_required
def get_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    return ok(user.to_dict(include_email=True))


@users_bp.patch('/<int:uid>')
@admin_required
def update_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    data = request.get_json(silent=True) or {}
    for field in ('plan', 'status', 'admin_note', 'group_id'):
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return ok(user.to_dict(include_email=True), 'User updated')


@users_bp.delete('/<int:uid>')
@admin_required
def delete_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    db.session.delete(user)
    db.session.commit()
    return ok(message='User deleted')


@users_bp.post('/bulk')
@admin_required
def bulk_create():
    data  = request.get_json(silent=True) or {}
    users_data = data.get('users', [])
    created_ids = []
    for u in users_data:
        if not u.get('email'):
            continue
        if User.query.filter_by(email=u['email'].lower()).first():
            continue
        user = User(name=u.get('name', ''), email=u['email'].lower())
        user.set_password(u.get('password', 'Brighter@123'))
        user.plan = u.get('plan', 'trial')
        db.session.add(user)
        db.session.flush()
        created_ids.append(user.id)
    db.session.commit()
    return ok({'created': len(created_ids), 'ids': created_ids}, 'Bulk accounts created', 201)
