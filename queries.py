from sqlalchemy import func, and_, or_
from database import get_session, Policy, Bill, Payment
from datetime import datetime, timedelta


def get_policy_by_number(session, policy_number):
    return session.query(Policy).filter(Policy.policy_number == policy_number).first()


def get_policies_by_type(session, policy_type):
    return (
        session.query(Policy).filter(Policy.policy_type.ilike(f"%{policy_type}%")).all()
    )


def get_active_policies(session):
    return session.query(Policy).filter(Policy.status == "Active").all()


def get_policy_bills(session, policy_number):
    policy = get_policy_by_number(session, policy_number)
    if not policy:
        return []
    return session.query(Bill).filter(Bill.policy_id == policy.id).all()


def get_overdue_bills(session):
    return (
        session.query(Bill)
        .filter(and_(Bill.status == "Overdue", Bill.due_date < datetime.now()))
        .all()
    )


def get_pending_bills(session):
    return session.query(Bill).filter(Bill.status == "Pending").all()


def get_bills_by_date_range(session, start_date, end_date):
    return (
        session.query(Bill)
        .filter(and_(Bill.bill_date >= start_date, Bill.bill_date <= end_date))
        .all()
    )


def get_payment_history(session, policy_number):
    policy = get_policy_by_number(session, policy_number)
    if not policy:
        return []
    return session.query(Payment).join(Bill).filter(Bill.policy_id == policy.id).all()


def get_revenue_summary(session, period="month"):
    now = datetime.now()
    if period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    payments = session.query(Payment).filter(Payment.payment_date >= start_date).all()

    total_revenue = sum(p.amount for p in payments)
    payment_count = len(payments)
    avg_payment = total_revenue / payment_count if payment_count > 0 else 0

    revenue_by_method = {}
    for p in payments:
        if p.payment_method not in revenue_by_method:
            revenue_by_method[p.payment_method] = 0
        revenue_by_method[p.payment_method] += p.amount

    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "payment_count": payment_count,
        "average_payment": round(avg_payment, 2),
        "revenue_by_method": {k: round(v, 2) for k, v in revenue_by_method.items()},
    }


def get_policy_summary(session, policy_number):
    policy = get_policy_by_number(session, policy_number)
    if not policy:
        return None

    bills = get_policy_bills(session, policy_number)
    payments = get_payment_history(session, policy_number)

    total_billed = sum(b.amount_due for b in bills)
    total_paid = sum(b.amount_paid for b in bills)
    total_outstanding = total_billed - total_paid

    return {
        "policy_number": policy.policy_number,
        "policy_type": policy.policy_type,
        "insured_name": policy.insured_name,
        "status": policy.status,
        "effective_date": policy.effective_date.strftime("%Y-%m-%d"),
        "expiration_date": policy.expiration_date.strftime("%Y-%m-%d"),
        "premium_amount": policy.premium_amount,
        "total_billed": round(total_billed, 2),
        "total_paid": round(total_paid, 2),
        "outstanding_balance": round(total_outstanding, 2),
        "bill_count": len(bills),
        "payment_count": len(payments),
    }


def get_billing_dashboard(session):
    total_policies = session.query(func.count(Policy.id)).scalar()
    active_policies = (
        session.query(func.count(Policy.id)).filter(Policy.status == "Active").scalar()
    )

    total_bills = session.query(func.count(Bill.id)).scalar()
    paid_bills = (
        session.query(func.count(Bill.id)).filter(Bill.status == "Paid").scalar()
    )
    pending_bills = (
        session.query(func.count(Bill.id)).filter(Bill.status == "Pending").scalar()
    )
    overdue_bills = (
        session.query(func.count(Bill.id)).filter(Bill.status == "Overdue").scalar()
    )

    total_premium = session.query(func.sum(Policy.premium_amount)).scalar() or 0
    total_collected = session.query(func.sum(Bill.amount_paid)).scalar() or 0
    total_outstanding = (
        session.query(func.sum(Bill.amount_due))
        .filter(or_(Bill.status == "Pending", Bill.status == "Overdue"))
        .with_entities(func.sum(Bill.amount_due))
        .scalar()
        or 0
    )

    overdue_details = session.query(Bill).filter(Bill.status == "Overdue").all()
    overdue_amount = sum(b.amount_due - b.amount_paid for b in overdue_details)

    return {
        "policies": {"total": total_policies, "active": active_policies},
        "billing": {
            "total_bills": total_bills,
            "paid_bills": paid_bills,
            "pending_bills": pending_bills,
            "overdue_bills": overdue_bills,
        },
        "financials": {
            "total_premium": round(total_premium, 2),
            "total_collected": round(total_collected, 2),
            "total_outstanding": round(total_outstanding, 2),
            "overdue_amount": round(overdue_amount, 2),
        },
    }


def search_policies(session, search_term):
    return (
        session.query(Policy)
        .filter(
            or_(
                Policy.policy_number.ilike(f"%{search_term}%"),
                Policy.insured_name.ilike(f"%{search_term}%"),
                Policy.policy_type.ilike(f"%{search_term}%"),
            )
        )
        .all()
    )
