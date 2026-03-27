"""Notices Blueprint."""
from flask import Blueprint, request
from app import db
from app.models import Notice
from app.utils.response import ok, created, not_found
from app.utils.jwt_helper import admin_required, require_session
from app import cache

notices_bp = Blueprint('notices', __name__)


@notices_bp.get('')
@require_session
@cache.cached(timeout=300, query_string=True)
def list_notices():
    category = request.args.get('category', '')
    q = Notice.query
    if category:
        q = q.filter_by(category=category)
    notices = q.order_by(Notice.created_at.desc(), Notice.id.desc()).all()
    return ok([n.to_dict() for n in notices])


@notices_bp.get('/<int:nid>')
@require_session
@cache.cached(timeout=300)
def get_notice(nid: int):
    notice = Notice.query.get(nid)
    if not notice:
        return not_found('Notice')
    return ok(notice.to_dict())


@notices_bp.post('')
@admin_required
def create_notice():
    data = request.get_json(silent=True) or {}
    notice = Notice(
        title=data.get('title', 'Untitled'),
        body=data.get('body', ''),
        category=data.get('category', 'general'),
        department=data.get('department', ''),
        link_url=data.get('link_url', ''),
        is_pinned=data.get('is_pinned', False),
    )
    db.session.add(notice)
    db.session.commit()
    return created(notice.to_dict())


@notices_bp.patch('/<int:nid>')
@admin_required
def update_notice(nid: int):
    notice = Notice.query.get(nid)
    if not notice:
        return not_found('Notice')
    data = request.get_json(silent=True) or {}
    for f in ('title', 'body', 'category', 'department', 'link_url', 'is_pinned'):
        if f in data:
            setattr(notice, f, data[f])
    db.session.commit()
    return ok(notice.to_dict(), 'Notice updated')


@notices_bp.delete('/<int:nid>')
@admin_required
def delete_notice(nid: int):
    notice = Notice.query.get(nid)
    if not notice:
        return not_found('Notice')
    db.session.delete(notice)
    db.session.commit()
    return ok(message='Notice deleted')
