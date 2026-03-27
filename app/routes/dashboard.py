"""Dashboard Blueprint — aggregated data for the student dashboard."""
from flask import Blueprint
from app.models import WeeklyTestAttempt, LiveClassAttendance, LiveClass
from app.utils.response import ok
from app.utils.jwt_helper import current_user_id, require_session
from app.utils.cache_helper import cache_key_with_user
from app import cache
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.get('/me')
@require_session
@cache.cached(timeout=300, make_cache_key=cache_key_with_user)
def my_dashboard():
    uid = current_user_id()

    # Weekly tests appeared
    tests_count = WeeklyTestAttempt.query.filter_by(user_id=uid).count()

    # Homework attempted (mock: each live class attended counts as homework done conceptually)
    # For demo we add a fixed offset
    homework_count = LiveClassAttendance.query.filter_by(user_id=uid).count()

    # Daily study hours — last 7 days (mock: generate based on attendance)
    today = datetime.utcnow().date()
    daily_hours = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime('%a')
        # Each attendance record on that day = 1.5h (demo)
        count = LiveClassAttendance.query.filter(
            LiveClassAttendance.user_id == uid,
            LiveClassAttendance.joined_at >= datetime.combine(day, datetime.min.time()),
            LiveClassAttendance.joined_at < datetime.combine(day + timedelta(days=1), datetime.min.time()),
        ).count()
        daily_hours.append({'day': label, 'hours': round(count * 1.5, 1)})

    # Current live class (if any)
    live_class = LiveClass.query.filter_by(status='live').first()
    if not live_class:
        live_class = LiveClass.query.filter(
            LiveClass.status == 'upcoming',
            LiveClass.scheduled_at != None
        ).order_by(LiveClass.scheduled_at.asc()).first()

    return ok({
        'tests_appeared':   tests_count,
        'homework_attempted': homework_count,
        'daily_hours':      daily_hours,
        'live_class':       live_class.to_dict() if live_class else None,
    })
