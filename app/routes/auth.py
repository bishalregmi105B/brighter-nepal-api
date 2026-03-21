"""Auth Blueprint — login, signup, me."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import User
from app.utils.response import ok, error, created
from app.utils.jwt_helper import make_token, current_user_id, require_session

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/login')
def login():
    data  = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    pw    = data.get('password', '')
    user  = User.query.filter_by(email=email).first()
    if not user or not user.check_password(pw):
        return error('Invalid email or password', 401)
    if user.status == 'suspended':
        return error('Account suspended. Contact support.', 403)
    # Rotate session token — invalidates all previously issued tokens
    session_token = user.on_login()
    db.session.commit()
    token = make_token(user.id, user.role, session_token)
    return ok({'token': token, 'user': user.to_dict(include_email=True)})


@auth_bp.post('/signup')
def signup():
    data  = request.get_json(silent=True) or {}
    name  = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    pw    = data.get('password', '')
    if not name or not email or not pw:
        return error('name, email and password are required')
    if User.query.filter_by(email=email).first():
        return error('An account with this email already exists', 409)
    user = User(name=name, email=email)
    user.set_password(pw)
    db.session.add(user)
    db.session.flush()
    session_token = user.on_login()
    db.session.commit()
    token = make_token(user.id, user.role, session_token)
    return created({'token': token, 'user': user.to_dict(include_email=True)}, 'Account created')


@auth_bp.get('/me')
@require_session
def me():
    user = User.query.get(current_user_id())
    if not user:
        return error('User not found', 404)
    return ok(user.to_dict(include_email=True))


@auth_bp.post('/logout')
@jwt_required()
def logout():
    """Invalidate the current session by clearing the session token."""
    user = User.query.get(current_user_id())
    if user:
        user.session_token = None
        db.session.commit()
    return ok(message='Logged out successfully')
