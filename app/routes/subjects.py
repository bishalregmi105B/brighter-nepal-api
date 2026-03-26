"""Subjects Blueprint — shared subject metadata across the platform."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app import cache, db
from app.models import LiveClass, Question, Resource, WeeklyTest
from app.utils.response import ok

subjects_bp = Blueprint('subjects', __name__)


def _normalize_subjects(values):
    normalized = {}
    for value in values:
        subject = (value or '').strip()
        if not subject:
            continue
        key = subject.lower()
        if key not in normalized:
            normalized[key] = subject
    return [normalized[key] for key in sorted(normalized.keys())]


@subjects_bp.get('')
@jwt_required()
@cache.cached(timeout=300)
def list_subjects():
    rows = []
    rows.extend(value for (value,) in db.session.query(Resource.subject).distinct().all())
    rows.extend(value for (value,) in db.session.query(LiveClass.subject).distinct().all())
    rows.extend(value for (value,) in db.session.query(WeeklyTest.subject).distinct().all())
    rows.extend(value for (value,) in db.session.query(Question.subject).distinct().all())
    return ok(_normalize_subjects(rows))
