"""Payments Blueprint — admin only."""
from flask import Blueprint, request
from app.models import Payment
from app.utils.response import not_found, paginate, ok
from app.utils.jwt_helper import admin_required
from app import cache

payments_bp = Blueprint('payments', __name__)


@payments_bp.get('')
@admin_required
@cache.cached(timeout=60, query_string=True)
def list_payments():
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    page   = int(request.args.get('page', 1))

    q = Payment.query
    if status:
        q = q.filter_by(status=status)
    if search:
        from app.models import User
        user_ids = [u.id for u in User.query.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%')).all()]
        q = q.filter(Payment.user_id.in_(user_ids))
    return paginate(q.order_by(Payment.created_at.desc()), page, 25)


@payments_bp.get('/<int:pid>')
@admin_required
@cache.cached(timeout=60)
def get_payment(pid: int):
    payment = Payment.query.get(pid)
    if not payment:
        return not_found('Payment')
    return ok(payment.to_dict())
