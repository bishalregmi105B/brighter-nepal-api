"""JWT helper utilities — now enforces single-device login via session_token.

Flow:
  - make_token(): JSON-encodes {id, role, session_token} as JWT sub string.
  - verify_session(): called by require_session() decorator — checks that the
    session_token in the JWT still matches what's stored in the DB.
    If not (user logged in elsewhere), returns 401 SESSION_EXPIRED.
  - Every @jwt_required() route that needs single-device enforcement should
    use @require_session instead (or in addition to @jwt_required).
"""
import json
from functools import wraps
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, verify_jwt_in_request
)
from app.utils.response import forbidden, error


def make_token(user_id: int, role: str, session_token: str) -> str:
    """Return a signed JWT whose sub is a JSON-encoded identity dict."""
    identity = json.dumps({'id': user_id, 'role': role, 'st': session_token})
    return create_access_token(identity=identity)


def _parse_identity() -> dict:
    raw = get_jwt_identity()
    if isinstance(raw, dict):
        return raw          # backwards-compat
    return json.loads(raw)


def current_user_id() -> int:
    return _parse_identity()['id']


def current_user_role() -> str:
    return _parse_identity().get('role', 'student')


def current_session_token() -> str | None:
    return _parse_identity().get('st')


def _check_session():
    """Returns (user, error_response) tuple. error_response is None if valid."""
    from app.models import User
    uid = current_user_id()
    st  = current_session_token()
    user = User.query.get(uid)
    if not user:
        return None, (error('User not found', 404))
    if user.status == 'suspended':
        return None, (error('Account suspended', 403))
    # Single-device enforcement: if session_token doesn't match DB, reject
    if st and user.session_token and user.session_token != st:
        return None, (error('Session expired — logged in on another device', 401))
    return user, None


def require_session(fn):
    """Decorator: jwt_required + single-device session validation."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        _, err = _check_session()
        if err:
            return err
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Decorator: jwt_required + single-device session validation + admin role check."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user, err = _check_session()
        if err:
            return err
        if not user or user.role != 'admin':
            return forbidden()
        return fn(*args, **kwargs)
    return wrapper
