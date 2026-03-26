"""Resources (Study Materials) Blueprint."""
from flask import Blueprint, request, send_from_directory
from flask_jwt_extended import jwt_required
from app import db
from app.models import Resource
from app.utils.response import ok, created, not_found, paginate, error
from app.utils.jwt_helper import admin_required
from app import cache
from werkzeug.utils import secure_filename
from pathlib import Path
from uuid import uuid4
import subprocess
import json

resources_bp = Blueprint('resources', __name__)
UPLOAD_DIR = Path(__file__).resolve().parents[2] / 'uploads' / 'resources'
THUMBNAIL_DIR = UPLOAD_DIR / 'thumbnails'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


def _generate_thumbnail(pdf_path: Path) -> str:
    """Render the first PDF page to a PNG thumbnail and return the filename."""
    stem = uuid4().hex
    output_base = THUMBNAIL_DIR / stem
    output_path = output_base.with_suffix('.png')

    subprocess.run(
        ['pdftoppm', '-f', '1', '-singlefile', '-png', '-scale-to', '900', str(pdf_path), str(output_base)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not output_path.exists():
        raise FileNotFoundError('Thumbnail was not created')
    return output_path.name


@resources_bp.get('')
@jwt_required()
@cache.cached(timeout=300, query_string=True)
def list_resources():
    subject      = request.args.get('subject', '')
    fmt          = request.args.get('format', '')
    section      = request.args.get('section', '')
    search       = request.args.get('search', '').strip()
    live_class_id = request.args.get('live_class_id', type=int)
    page         = int(request.args.get('page', 1))
    per_page     = max(1, min(int(request.args.get('per_page', 20)), 200))

    q = Resource.query
    if subject:
        q = q.filter_by(subject=subject)
    if fmt:
        q = q.filter_by(format=fmt)
    if section:
        q = q.filter_by(section=section)
    if live_class_id:
        q = q.filter_by(live_class_id=live_class_id)
    if search:
        q = q.filter(Resource.title.ilike(f'%{search}%') | Resource.subject.ilike(f'%{search}%'))
    return paginate(q.order_by(Resource.created_at.desc()), page, per_page)


@resources_bp.get('/subjects')
@jwt_required()
@cache.cached(timeout=300)
def list_subjects():
    """Return all distinct subjects that exist in the resources table."""
    rows = db.session.query(Resource.subject).distinct().order_by(Resource.subject).all()
    subjects = sorted({r[0] for r in rows if r[0]})
    return ok(subjects)



@resources_bp.get('/<int:rid>')
@jwt_required()
@cache.cached(timeout=300)
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
        description=data.get('description', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
    )
    db.session.add(res)
    db.session.commit()
    return created(res.to_dict())


@resources_bp.post('/upload-pdf')
@admin_required
def upload_pdf():
    """Upload a PDF file to local server storage and return hosted URL."""
    file = request.files.get('file')
    if not file or not file.filename:
        return error('PDF file is required')

    original_name = secure_filename(file.filename)
    ext = Path(original_name).suffix.lower()
    if ext != '.pdf':
        return error('Only PDF files are allowed')

    filename = f'{uuid4().hex}.pdf'
    target = UPLOAD_DIR / filename
    file.save(target)
    size_bytes = target.stat().st_size if target.exists() else 0
    thumbnail_url = ''

    try:
        thumbnail_name = _generate_thumbnail(target)
        thumbnail_url = f"{request.host_url.rstrip('/')}/api/resources/thumbnails/{thumbnail_name}"
    except Exception:
        thumbnail_url = ''

    file_url = f"{request.host_url.rstrip('/')}/api/resources/files/{filename}"
    return created({
        'file_url': file_url,
        'filename': filename,
        'original_name': original_name,
        'size_bytes': size_bytes,
        'thumbnail_url': thumbnail_url,
    }, 'PDF uploaded')


@resources_bp.get('/files/<path:filename>')
def serve_uploaded_file(filename: str):
    """Serve uploaded resource files (PDF) from local storage."""
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return not_found('File')
    path = UPLOAD_DIR / safe_name
    if not path.exists() or not path.is_file():
        return not_found('File')
    return send_from_directory(str(UPLOAD_DIR), safe_name, mimetype='application/pdf', as_attachment=False, conditional=True)


@resources_bp.get('/thumbnails/<path:filename>')
def serve_uploaded_thumbnail(filename: str):
    """Serve generated PDF thumbnails from local storage."""
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return not_found('File')
    path = THUMBNAIL_DIR / safe_name
    if not path.exists() or not path.is_file():
        return not_found('File')
    return send_from_directory(str(THUMBNAIL_DIR), safe_name, mimetype='image/png', as_attachment=False, conditional=True)


@resources_bp.patch('/<int:rid>')
@admin_required
def update_resource(rid: int):
    res = Resource.query.get(rid)
    if not res:
        return not_found('Resource')
    data = request.get_json(silent=True) or {}
    for f in ('title', 'subject', 'format', 'section', 'file_url', 'size_label', 'description', 'thumbnail_url'):
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
