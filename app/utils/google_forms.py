"""Helpers for Google Forms API access via refresh-token OAuth."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest


GOOGLE_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_FORMS_API_BASE = 'https://forms.googleapis.com/v1'


class GoogleFormsError(Exception):
    """Raised when Google Forms integration cannot continue."""


def parse_google_form_id(value: str | None) -> str:
    raw = (value or '').strip()
    if not raw:
        raise GoogleFormsError('Google Forms URL is required before import or sync.')

    if '/forms/d/e/' in raw:
        raise GoogleFormsError(
            'Use the Google Form editor URL for import/sync: '
            'https://docs.google.com/forms/d/<FORM_ID>/edit. '
            'Responder links (/forms/d/e/.../viewform) are not supported by Google Forms API.'
        )

    if '/' not in raw and re.fullmatch(r'[A-Za-z0-9_-]{20,}', raw):
        return raw

    match = re.search(r'/forms/d/([A-Za-z0-9_-]+)', raw)
    if match:
        return match.group(1)

    parsed = urlparse.urlparse(raw)
    if parsed.netloc.endswith('google.com'):
        path_parts = [part for part in parsed.path.split('/') if part]
        if len(path_parts) >= 3 and path_parts[0] == 'forms' and path_parts[1] == 'd' and path_parts[2] != 'e':
            return path_parts[2]

    raise GoogleFormsError('Could not extract a Google Form ID from the provided URL.')


def _load_google_credentials_from_db() -> tuple[str, str, str]:
    try:
        from app.models import PlatformSetting
        key_map = {
            'google_forms_client_id': 'client_id',
            'google_forms_client_secret': 'client_secret',
            'google_forms_refresh_token': 'refresh_token',
        }
        rows = PlatformSetting.query.filter(PlatformSetting.key.in_(list(key_map.keys()))).all()
    except Exception:
        return '', '', ''

    values = {'client_id': '', 'client_secret': '', 'refresh_token': ''}
    for row in rows:
        mapped_key = key_map.get((row.key or '').strip())
        if not mapped_key:
            continue
        values[mapped_key] = (row.value or '').strip()
    return values['client_id'], values['client_secret'], values['refresh_token']


def _require_google_env() -> tuple[str, str, str]:
    client_id, client_secret, refresh_token = _load_google_credentials_from_db()

    if not client_id or not client_secret or not refresh_token:
        raise GoogleFormsError(
            'Google Forms OAuth is not configured in database settings. '
            'Open Admin Settings and save Client ID, Client Secret, and Refresh Token.'
        )
    return client_id, client_secret, refresh_token


def _request_json(url: str, *, method: str = 'GET', headers: dict[str, str] | None = None, body: bytes | None = None) -> dict[str, Any]:
    req = urlrequest.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            payload = response.read().decode('utf-8')
            return json.loads(payload) if payload else {}
    except urlerror.HTTPError as err:
        detail = ''
        try:
            body_text = err.read().decode('utf-8')
            parsed = json.loads(body_text) if body_text else {}
            detail = parsed.get('error', {}).get('message') or parsed.get('message') or body_text
        except Exception:
            detail = err.reason if getattr(err, 'reason', None) else str(err)
        raise GoogleFormsError(detail or 'Google Forms API request failed.') from err
    except urlerror.URLError as err:
        raise GoogleFormsError(f'Google Forms API request failed: {err.reason}') from err


def get_google_access_token() -> str:
    client_id, client_secret, refresh_token = _require_google_env()
    payload = urlparse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode('utf-8')
    data = _request_json(
        GOOGLE_OAUTH_TOKEN_URL,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        body=payload,
    )
    access_token = (data.get('access_token') or '').strip()
    if not access_token:
        raise GoogleFormsError('Google OAuth token refresh succeeded without returning an access token.')
    return access_token


def google_forms_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = f"?{urlparse.urlencode(params)}" if params else ''
    token = get_google_access_token()
    return _request_json(
        f'{GOOGLE_FORMS_API_BASE}{path}{query}',
        headers={'Authorization': f'Bearer {token}'},
    )


def fetch_form(form_id: str) -> dict[str, Any]:
    return google_forms_get(f'/forms/{form_id}')


def _rfc3339_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace('+00:00', 'Z')


def list_form_responses(form_id: str, *, submitted_after: datetime | None = None) -> list[dict[str, Any]]:
    responses: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        params: dict[str, Any] = {'pageSize': 500}
        if page_token:
            params['pageToken'] = page_token
        if submitted_after:
            params['filter'] = f'timestamp > {_rfc3339_utc(submitted_after)}'
        payload = google_forms_get(f'/forms/{form_id}/responses', params)
        responses.extend(payload.get('responses') or [])
        page_token = (payload.get('nextPageToken') or '').strip() or None
        if not page_token:
            break
    return responses


def extract_answer_text(answer: dict[str, Any] | None) -> str:
    if not answer:
        return ''
    text_answers = (answer.get('textAnswers') or {}).get('answers') or []
    values = [(item.get('value') or '').strip() for item in text_answers if (item.get('value') or '').strip()]
    return ', '.join(values)


def normalize_student_id_value(value: str | None) -> str:
    raw = (value or '').strip().upper()
    if not raw:
        return ''
    if raw.startswith('BC'):
        raw = raw[2:]
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if digits:
        return digits[-6:] if len(digits) >= 6 else digits
    return raw
