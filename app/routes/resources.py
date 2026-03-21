"""Resources (Study Materials) Blueprint."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import Resource
from app.utils.response import ok, created, not_found, paginate
from app.utils.jwt_helper import admin_required
import json

resources_bp = Blueprint('resources', __name__)


@resources_bp.get('')
@jwt_required()
def list_resources():
    subject = request.args.get('subject', '')
    fmt     = request.args.get('format', '')
    section = request.args.get('section', '')
    search  = request.args.get('search', '').strip()
    page    = int(request.args.get('page', 1))

    q = Resource.query
    if subject:
        q = q.filter_by(subject=subject)
    if fmt:
        q = q.filter_by(format=fmt)
    if section:
        q = q.filter_by(section=section)
    if search:
        q = q.filter(Resource.title.ilike(f'%{search}%') | Resource.subject.ilike(f'%{search}%'))
    return paginate(q.order_by(Resource.created_at.desc()), page, 20)


@resources_bp.get('/<int:rid>')
@jwt_required()
def get_resource(rid: int):
    res = Resource.query.get(rid)
    if not res:
        return not_found('Resource')
    return ok(res.to_dict())


@resources_bp.post('')
@admin_required
def create_resource():
    data = request.get_json(silent=True) or {}
    res = Resource(
        title=data.get('title', 'Untitled'),
        subject=data.get('subject', 'General'),
        format=data.get('format', 'pdf'),
        section=data.get('section', ''),
        file_url=data.get('file_url', ''),
        size_label=data.get('size_label', ''),
        tags=json.dumps(data.get('tags', [])),
    )
    db.session.add(res)
    db.session.commit()
    return created(res.to_dict())


@resources_bp.patch('/<int:rid>')
@admin_required
def update_resource(rid: int):
    res = Resource.query.get(rid)
    if not res:
        return not_found('Resource')
    data = request.get_json(silent=True) or {}
    for f in ('title', 'subject', 'format', 'section', 'file_url', 'size_label'):
        if f in data:
            setattr(res, f, data[f])
    if 'tags' in data:
        res.tags = json.dumps(data['tags'])
    db.session.commit()
    return ok(res.to_dict(), 'Resource updated')


@resources_bp.delete('/<int:rid>')
@admin_required
def delete_resource(rid: int):
    res = Resource.query.get(rid)
    if not res:
        return not_found('Resource')
    db.session.delete(res)
    db.session.commit()
    return ok(message='Resource deleted')


@resources_bp.post('/<int:rid>/download')
@jwt_required()
def log_download(rid: int):
    res = Resource.query.get(rid)
    if not res:
        return not_found('Resource')
    res.downloads += 1
    db.session.commit()
    return ok({'file_url': res.file_url, 'downloads': res.downloads})
