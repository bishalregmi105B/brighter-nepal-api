"""Users Blueprint — admin CRUD for user accounts."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import User, Payment
from app.utils.response import ok, error, not_found, paginate
from app.utils.jwt_helper import admin_required
from datetime import datetime, date

users_bp = Blueprint('users', __name__)


@users_bp.get('')
@admin_required
def list_users():
    tab    = request.args.get('tab', 'all')       # all | paid | trial
    search = request.args.get('search', '').strip()
    page   = int(request.args.get('page', 1))
    limit  = int(request.args.get('limit', 20))

    q = User.query
    if tab in ('paid', 'trial'):
        q = q.filter_by(plan=tab)
    if search:
        q = q.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))

    total  = q.count()
    items  = q.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok({
        'items': [u.to_dict(admin=True) for u in items],
        'total': total,
        'page':  page,
        'pages': max(1, -(-total // limit)),   # ceil division
    })


@users_bp.get('/stats')
@admin_required
def get_stats():
    """Returns quick stats for the admin dashboard."""
    total_users  = User.query.filter(User.role != 'admin').count()
    paid_users   = User.query.filter_by(plan='paid').count()
    trial_users  = User.query.filter_by(plan='trial').count()

    today_start  = datetime.combine(date.today(), datetime.min.time())
    today_enroll = User.query.filter(User.created_at >= today_start).count()

    total_payment = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    today_payment = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed',
        Payment.created_at >= today_start
    ).scalar() or 0

    return ok({
        'total_users':    total_users,
        'paid_users':     paid_users,
        'trial_users':    trial_users,
        'total_payment':  int(total_payment),
        'today_payment':  int(today_payment),
        'today_enroll':   today_enroll,
    })


@users_bp.get('/<int:uid>')
@admin_required
def get_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    return ok(user.to_dict(admin=True))


@users_bp.patch('/<int:uid>')
@admin_required
def update_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    data = request.get_json(silent=True) or {}
    for field in ('plan', 'status', 'admin_note', 'group_id', 'whatsapp', 'joined_method'):
        if field in data:
            setattr(user, field, data[field])
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    db.session.commit()
    return ok(user.to_dict(admin=True), 'User updated')


@users_bp.get('/recent-activity')
@admin_required
def recent_activity():
    """Returns the 10 most recent exam attempts (model sets + weekly tests) for the activity feed."""
    from app.models import ModelSetAttempt, WeeklyTestAttempt, ModelSet, WeeklyTest
    ms_attempts = (
        db.session.query(ModelSetAttempt, User, ModelSet)
        .join(User, User.id == ModelSetAttempt.user_id)
        .join(ModelSet, ModelSet.id == ModelSetAttempt.model_set_id)
        .order_by(ModelSetAttempt.completed_at.desc())
        .limit(5).all()
    )
    wt_attempts = (
        db.session.query(WeeklyTestAttempt, User, WeeklyTest)
        .join(User, User.id == WeeklyTestAttempt.user_id)
        .join(WeeklyTest, WeeklyTest.id == WeeklyTestAttempt.test_id)
        .order_by(WeeklyTestAttempt.submitted_at.desc())
        .limit(5).all()
    )

    rows = []
    for attempt, user, ms in ms_attempts:
        rows.append({
            'user': user.name,
            'action': f'Completed Model Set — {ms.title[:40]}',
            'score': f'{attempt.score}/{attempt.total}',
            'tier': 'Premium' if user.plan == 'paid' else '7-Day Trial',
            'time': attempt.completed_at.isoformat(),
        })
    for attempt, user, wt in wt_attempts:
        rows.append({
            'user': user.name,
            'action': f'Submitted Weekly Test — {wt.title[:40]}',
            'score': f'{attempt.score}/{attempt.total}',
            'tier': 'Premium' if user.plan == 'paid' else '7-Day Trial',
            'time': attempt.submitted_at.isoformat(),
        })

    # Sort all by time descending
    rows.sort(key=lambda r: r['time'], reverse=True)
    return ok(rows[:10])


@users_bp.post('/<int:uid>/shift-to-paid')
@admin_required
def shift_to_paid(uid: int):
    """Shift a trial user to paid plan and create a payment record."""
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    data   = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    if amount <= 0:
        return error('amount must be positive')

    user.plan        = 'paid'
    user.paid_amount = amount

    payment = Payment(
        user_id  = user.id,
        user_name= user.name,
        amount   = amount,
        method   = data.get('method', 'cash'),
        status   = 'completed',
    )
    db.session.add(payment)
    db.session.commit()
    return ok(user.to_dict(admin=True), 'User shifted to paid')


@users_bp.delete('/<int:uid>')
@admin_required
def delete_user(uid: int):
    user = User.query.get(uid)
    if not user:
        return not_found('User')
    db.session.delete(user)
    db.session.commit()
    return ok(message='User deleted')


@users_bp.post('/bulk')
@admin_required
def bulk_create():
    data  = request.get_json(silent=True) or {}
    users_data = data.get('users', [])
    created_ids = []
    for u in users_data:
        if not u.get('email'):
            continue
        if User.query.filter_by(email=u['email'].lower()).first():
            continue
        user = User(name=u.get('name', ''), email=u['email'].lower())
        user.whatsapp = u.get('whatsapp')
        user.set_password(u.get('password', 'Brighter@123'))
        user.plan = u.get('plan', 'trial')
        db.session.add(user)
        db.session.flush()
        created_ids.append(user.id)
    db.session.commit()
    return ok({'created': len(created_ids), 'ids': created_ids}, 'Bulk accounts created', 201)
