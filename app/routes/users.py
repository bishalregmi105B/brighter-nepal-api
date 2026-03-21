"""Users Blueprint — admin CRUD for user accounts."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import User, Payment, ContactMethod
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
    if 'paid_amount' in data and data['paid_amount'] is not None:
        user.paid_amount = int(data['paid_amount'])
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    db.session.commit()
    return ok(user.to_dict(admin=True), 'User updated')


# ── Contact Methods CRUD ──────────────────────────────────────────────────────
@users_bp.get('/contact-methods')
@admin_required
def list_contact_methods():
    """List all active contact methods for the joined_via dropdown."""
    methods = ContactMethod.query.filter_by(is_active=True).order_by(ContactMethod.name).all()
    return ok([m.to_dict() for m in methods])


@users_bp.post('/contact-methods')
@admin_required
def create_contact_method():
    data = request.get_json(silent=True) or {}
    if not data.get('name', '').strip():
        return error('name is required')
    m = ContactMethod(name=data['name'].strip(), channel=data.get('channel', 'other'))
    db.session.add(m)
    db.session.commit()
    return ok(m.to_dict(), 'Contact method created')


@users_bp.delete('/contact-methods/<int:mid>')
@admin_required
def delete_contact_method(mid: int):
    m = ContactMethod.query.get(mid)
    if not m:
        return not_found('ContactMethod')
    m.is_active = False      # soft-delete
    db.session.commit()
    return ok(message='Contact method removed')


@users_bp.patch('/contact-methods/<int:mid>')
@admin_required
def update_contact_method(mid: int):
    m = ContactMethod.query.get(mid)
    if not m:
        return not_found('ContactMethod')
    data = request.get_json(silent=True) or {}
    if 'name' in data:
        m.name = data['name'].strip()
    if 'channel' in data:
        m.channel = data['channel']
    db.session.commit()
    return ok(m.to_dict(), 'Updated')


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
        user_id = user.id,
        amount  = amount,
        method  = data.get('method', 'cash'),
        status  = 'completed',
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
    data       = request.get_json(silent=True) or {}
    users_data = data.get('users', [])
    created    = []
    for u in users_data:
        name = (u.get('name') or '').strip()
        if not name:
            continue
        raw_email = (u.get('email') or '').strip().lower()
        pw        = u.get('password') or 'Brighter@123'
        # Skip if email given and already taken
        if raw_email and User.query.filter_by(email=raw_email).first():
            continue
        placeholder = f'pending_{id(u)}@placeholder.local'
        user = User(name=name, email=raw_email or placeholder)
        user.set_password(pw)
        user.plan     = u.get('plan', 'trial')
        user.whatsapp = u.get('whatsapp')
        db.session.add(user)
        db.session.flush()   # get user.id
        # Replace placeholder email with BC-based one if no real email given
        if not raw_email:
            user.email = f'bc{str(user.id).zfill(4)}@brighternepal.local'
        db.session.flush()
        created.append({
            'id':       user.id,
            'bc_id':    f'BC-{str(user.id).zfill(4)}',
            'name':     user.name,
            'email':    user.email,
            'password': pw,
            'plan':     user.plan,
        })
    db.session.commit()
    return ok({'created': len(created), 'users': created}, 'Bulk accounts created', 201)
