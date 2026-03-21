"""Shared response helpers for consistent JSON API responses."""
from flask import jsonify
from typing import Any


def ok(data: Any = None, message: str = 'success', status: int = 200):
    payload = {'success': True, 'message': message}
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status


def created(data: Any = None, message: str = 'Created'):
    return ok(data, message, 201)


def error(message: str = 'An error occurred', status: int = 400, errors: Any = None):
    payload = {'success': False, 'message': message}
    if errors:
        payload['errors'] = errors
    return jsonify(payload), status


def not_found(resource: str = 'Resource'):
    return error(f'{resource} not found', 404)


def forbidden():
    return error('Forbidden', 403)


def paginate(query, page: int = 1, per_page: int = 20, serializer=None):
    """Helper to paginate a SQLAlchemy query and return standardised response."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [serializer(i) if serializer else i.to_dict() for i in paginated.items]
    return ok({
        'items':    items,
        'total':    paginated.total,
        'page':     paginated.page,
        'pages':    paginated.pages,
        'per_page': paginated.per_page,
    })
