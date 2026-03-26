"""Admin settings endpoints."""
from __future__ import annotations

from flask import Blueprint, request

from app import db
from app.models import PlatformSetting
from app.utils.jwt_helper import admin_required
from app.utils.response import error, ok

settings_bp = Blueprint('settings', __name__)

GOOGLE_FORMS_SETTING_KEYS = {
    'client_id': 'google_forms_client_id',
    'client_secret': 'google_forms_client_secret',
    'refresh_token': 'google_forms_refresh_token',
}


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
