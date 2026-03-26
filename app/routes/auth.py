"""Auth Blueprint — login, signup, me."""
import json
import re
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import User
from app.utils.response import ok, error, created
from app.utils.jwt_helper import make_token, current_user_id, require_session
from app.utils.student_id import generate_unique_student_id

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/login')
def login():
    data       = request.get_json(silent=True) or {}
    # Accept either 'identifier' (new) or legacy 'email' key
    identifier = (data.get('identifier') or data.get('email') or '').strip()
    pw         = data.get('password', '')

    # Student ID login:
    # - Current format: BC123456 (stored in users.student_id)
    # - Also accepts BC-123456 for backward compatibility
    normalized = re.sub(r'[\s-]', '', identifier).upper()
    user = None
    if normalized.startswith('BC') and normalized[2:].isdigit():
        sid = normalized[2:]
        user = User.query.filter_by(student_id=sid).first()
        if not user:
            user = User.query.get(int(sid))
    elif normalized.isdigit():
        if len(normalized) == 6:
            user = User.query.filter_by(student_id=normalized).first()
        if not user:
            user = User.query.get(int(normalized))
    else:
        user = User.query.filter_by(email=identifier.lower()).first()

    if not user or not user.check_password(pw):
        return error('Invalid credentials', 401)
    if user.status == 'suspended':
        return error('Account suspended. Contact support.', 403)
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
    user = User(
        name=name,
        email=email,
        student_id=generate_unique_student_id(),
        onboarding_completed=False,
        joined_method='Self Signup',
    )
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


@auth_bp.post('/complete-onboarding')
@require_session
def complete_onboarding():
    user = User.query.get(current_user_id())
    if not user:
        return error('User not found', 404)

    data = request.get_json(silent=True) or {}

    def _clean_text(value, max_len=200):
        if value is None:
            return ''
        text = str(value).strip()
        return text[:max_len]

    target_exams = data.get('target_exams') or []
    if not isinstance(target_exams, list):
        target_exams = []
    clean_exams = []
    for exam in target_exams:
        text = _clean_text(exam, 80)
        if text and text not in clean_exams:
            clean_exams.append(text)
    onboarding_payload = {
        'previous_school': _clean_text(data.get('previous_school'), 200),
        'location': _clean_text(data.get('location'), 120),
        'stream': _clean_text(data.get('stream'), 60),
        'heard_from': _clean_text(data.get('heard_from'), 120),
        'target_exams': clean_exams,
    }
    user.onboarding_data = json.dumps(onboarding_payload, ensure_ascii=False)
    user.onboarding_completed = True
    db.session.commit()
    return ok(user.to_dict(include_email=True), 'Onboarding completed')


@auth_bp.post('/logout')
@jwt_required()
def logout():
    """Invalidate the current session by clearing the session token."""
    user = User.query.get(current_user_id())
    if user:
        user.session_token = None
        db.session.commit()
    return ok(message='Logged out successfully')
