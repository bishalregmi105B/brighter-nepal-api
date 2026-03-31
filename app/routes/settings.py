"""Admin settings endpoints."""
from __future__ import annotations

import json
from urllib import parse as urlparse
from urllib import request as urlrequest
from urllib import error as urlerror

from flask import Blueprint, current_app, redirect, request, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import db
from app.models import PlatformSetting
from app.utils.jwt_helper import admin_required, current_user_id
from app.utils.response import error, ok

settings_bp = Blueprint('settings', __name__)

GOOGLE_FORMS_SETTING_KEYS = {
    'client_id': 'google_forms_client_id',
    'client_secret': 'google_forms_client_secret',
    'refresh_token': 'google_forms_refresh_token',
}
GOOGLE_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_FORMS_SCOPES = [
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/forms.responses.readonly',
]


def _read_settings_map(keys: list[str]) -> dict[str, str]:
    rows = PlatformSetting.query.filter(PlatformSetting.key.in_(keys)).all()
    return {
        row.key: (row.value or '').strip()
        for row in rows
        if row.key
    }


def _resolve_google_forms_values() -> dict[str, str]:
    key_names = list(GOOGLE_FORMS_SETTING_KEYS.values())
    db_values = _read_settings_map(key_names)

    return {
        short_key: db_values.get(db_key, '')
        for short_key, db_key in GOOGLE_FORMS_SETTING_KEYS.items()
    }


def _upsert_setting(key: str, value: str) -> None:
    setting = PlatformSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        db.session.add(PlatformSetting(key=key, value=value))


def _oauth_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config.get('SECRET_KEY', 'change-me'),
        salt='google-forms-oauth',
    )


def _frontend_settings_url(**query: str) -> str:
    base = (current_app.config.get('FRONTEND_URL') or '').rstrip('/')
    if not base:
        base = request.host_url.rstrip('/')
    url = f'{base}/admin/settings'
    if not query:
        return url
    return f'{url}?{urlparse.urlencode(query)}'


def _exchange_google_oauth_code(*, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
    payload = urlparse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    req = urlrequest.Request(
        GOOGLE_TOKEN_ENDPOINT,
        data=payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = (resp.read() or b'').decode('utf-8')
            return json.loads(body) if body else {}
    except urlerror.HTTPError as err:
        detail = ''
        try:
            body = (err.read() or b'').decode('utf-8')
            parsed = json.loads(body) if body else {}
            detail = parsed.get('error_description') or parsed.get('error') or body
        except Exception:
            detail = str(err)
        raise RuntimeError(detail or 'Google token exchange failed.') from err
    except Exception as err:
        raise RuntimeError(str(err)) from err


@settings_bp.get('/google-forms')
@admin_required
def get_google_forms_settings():
    values = _resolve_google_forms_values()
    return ok({
        'client_id': values['client_id'],
        'client_secret': values['client_secret'],
        'refresh_token': values['refresh_token'],
        'configured': bool(values['client_id'] and values['client_secret'] and values['refresh_token']),
    })


@settings_bp.patch('/google-forms')
@admin_required
def update_google_forms_settings():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error('Invalid payload')

    accepted = {'client_id', 'client_secret', 'refresh_token'}
    received = [key for key in accepted if key in payload]
    if not received:
        return error('No fields provided to update')

    for key in received:
        value = payload.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            return error(f'{key} must be a string')
        _upsert_setting(GOOGLE_FORMS_SETTING_KEYS[key], value.strip())

    db.session.commit()
    return get_google_forms_settings()


@settings_bp.get('/google-forms/oauth/url')
@admin_required
def get_google_forms_oauth_url():
    values = _resolve_google_forms_values()
    client_id = (values.get('client_id') or '').strip()
    client_secret = (values.get('client_secret') or '').strip()
    if not client_id or not client_secret:
        return error('Save Client ID and Client Secret first, then authenticate to generate refresh token.')

    redirect_uri = url_for('settings.google_forms_oauth_callback', _external=True)
    state = _oauth_serializer().dumps({
        'uid': current_user_id(),
        'rt': redirect_uri,
    })
    query = urlparse.urlencode({
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(GOOGLE_FORMS_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    })
    return ok({
        'auth_url': f'{GOOGLE_AUTH_ENDPOINT}?{query}',
        'redirect_uri': redirect_uri,
    })


@settings_bp.get('/google-forms/oauth/callback')
def google_forms_oauth_callback():
    err = (request.args.get('error') or '').strip()
    code = (request.args.get('code') or '').strip()
    state = (request.args.get('state') or '').strip()
    if err:
        return redirect(_frontend_settings_url(google_oauth='error', reason=err))
    if not code or not state:
        return redirect(_frontend_settings_url(google_oauth='error', reason='missing_code_or_state'))

    try:
        state_data = _oauth_serializer().loads(state, max_age=900)
    except SignatureExpired:
        return redirect(_frontend_settings_url(google_oauth='error', reason='state_expired'))
    except BadSignature:
        return redirect(_frontend_settings_url(google_oauth='error', reason='invalid_state'))
    except Exception:
        return redirect(_frontend_settings_url(google_oauth='error', reason='invalid_state'))

    redirect_uri = (state_data.get('rt') or '').strip() or url_for('settings.google_forms_oauth_callback', _external=True)
    values = _resolve_google_forms_values()
    client_id = (values.get('client_id') or '').strip()
    client_secret = (values.get('client_secret') or '').strip()
    if not client_id or not client_secret:
        return redirect(_frontend_settings_url(google_oauth='error', reason='missing_client_credentials'))

    try:
        token_payload = _exchange_google_oauth_code(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
        )
    except Exception as exchange_err:
        return redirect(_frontend_settings_url(google_oauth='error', reason=str(exchange_err)[:200]))

    refresh_token = (token_payload.get('refresh_token') or '').strip()
    if not refresh_token:
        return redirect(_frontend_settings_url(
            google_oauth='error',
            reason='no_refresh_token_returned_use_prompt_consent_and_revoke_previous_access_if_needed',
        ))

    _upsert_setting(GOOGLE_FORMS_SETTING_KEYS['refresh_token'], refresh_token)
    db.session.commit()
    return redirect(_frontend_settings_url(google_oauth='success'))


# ── Chat Settings ─────────────────────────────────────────────────────────────
_CHAT_SETTING_KEYS = ['chat_rate_limit_count', 'chat_rate_limit_window_secs']
_CHAT_DEFAULTS = {'chat_rate_limit_count': 20, 'chat_rate_limit_window_secs': 60}


@settings_bp.get('/chat')
@admin_required
def get_chat_settings():
    rows = PlatformSetting.query.filter(PlatformSetting.key.in_(_CHAT_SETTING_KEYS)).all()
    db_vals = {r.key: r.value for r in rows}
    return ok({
        'chat_rate_limit_count': int(db_vals.get('chat_rate_limit_count') or _CHAT_DEFAULTS['chat_rate_limit_count']),
        'chat_rate_limit_window_secs': int(db_vals.get('chat_rate_limit_window_secs') or _CHAT_DEFAULTS['chat_rate_limit_window_secs']),
    })


@settings_bp.patch('/chat')
@admin_required
def update_chat_settings():
    payload = request.get_json(silent=True) or {}
    updated = []
    for key in _CHAT_SETTING_KEYS:
        if key in payload:
            val = payload[key]
            try:
                int_val = int(val)
                if int_val < 0:
                    return error(f'{key} must be >= 0')
            except (TypeError, ValueError):
                return error(f'{key} must be a number')
            _upsert_setting(key, str(int_val))
            updated.append(key)
    if not updated:
        return error('No valid fields provided')
    db.session.commit()
    return get_chat_settings()


# ── Subject Management ────────────────────────────────────────────────────────
_SUBJECTS_KEY = 'custom_subjects'


@settings_bp.get('/subjects')
@admin_required
def get_subjects():
    setting = PlatformSetting.query.filter_by(key=_SUBJECTS_KEY).first()
    subjects = json.loads(setting.value) if setting and setting.value else []
    return ok(subjects)


@settings_bp.put('/subjects')
@admin_required
def update_subjects():
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return error('Expected a list of subject strings')
    cleaned = []
    for s in payload:
        val = str(s).strip()
        if val and val not in cleaned:
            cleaned.append(val)
    _upsert_setting(_SUBJECTS_KEY, json.dumps(cleaned, ensure_ascii=False))
    db.session.commit()
    return ok(cleaned)
