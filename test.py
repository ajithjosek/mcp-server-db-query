#!/usr/bin/env python3
"""Test suite for the Insurance Billing MCP Server"""

import sys
from database import (
    create_database,
    populate_sample_data,
    get_engine,
    get_session,
    Policy,
    Bill,
    Payment,
)
from queries import (
    get_billing_dashboard,
    get_policy_summary,
    search_policies,
    get_overdue_bills,
    get_revenue_summary,
    get_active_policies,
    get_policy_by_number,
    get_policies_by_type,
    get_policy_bills,
    get_pending_bills,
    get_payment_history,
    get_bills_by_date_range,
)
from config import DATABASE_PATH
import json


def test_database_creation():
    print("Testing database creation...")
    engine = create_database(DATABASE_PATH)
    assert engine is not None
    print("  OK: Database engine created")


def test_sample_data():
    print("Testing sample data population...")
    engine = create_database(DATABASE_PATH)
    populate_sample_data(engine)
    session = get_session(engine)
    policy_count = session.query(Policy).count()
    bill_count = session.query(Bill).count()
    payment_count = session.query(Payment).count()
    session.close()

    assert policy_count >= 10, f"Expected at least 10 policies, got {policy_count}"
    assert bill_count >= 20, f"Expected at least 20 bills, got {bill_count}"
    print(
        f"  OK: Created {policy_count} policies, {bill_count} bills, {payment_count} payments"
    )


def test_queries():
    print("Testing query functions...")
    engine = get_engine(DATABASE_PATH)
    session = get_session(engine)

    # Test get_active_policies
    active = get_active_policies(session)
    assert isinstance(active, list)
    print(f"  OK: get_active_policies returned {len(active)} policies")

    # Test search_policies
    results = search_policies(session, "Auto")
    assert isinstance(results, list)
    print(f"  OK: search_policies found {len(results)} policies")

    # Test get_policy_summary
    if active:
        summary = get_policy_summary(session, active[0].policy_number)
        assert summary is not None
        assert "policy_number" in summary
        print(f"  OK: get_policy_summary works")

    # Test get_billing_dashboard
    dashboard = get_billing_dashboard(session)
    assert "policies" in dashboard
    assert "billing" in dashboard
    assert "financials" in dashboard
    print(f"  OK: get_billing_dashboard returned metrics")

    # Test get_overdue_bills
    overdue = get_overdue_bills(session)
    assert isinstance(overdue, list)
    print(f"  OK: get_overdue_bills returned {len(overdue)} bills")

    # Test get_revenue_summary
    for period in ["month", "quarter", "year"]:
        revenue = get_revenue_summary(session, period)
        assert "total_revenue" in revenue
        assert "payment_count" in revenue
    print(f"  OK: get_revenue_summary works for all periods")

    session.close()


def test_policy_lookup():
    print("Testing policy lookup and related data...")
    engine = get_engine(DATABASE_PATH)
    session = get_session(engine)

    # Find a policy
    policies = get_active_policies(session)
    if not policies:
        print("  WARNING: No active policies found, skipping")
        return

    policy = policies[0]

    # Test get_policy_bills
    bills = get_policy_bills(session, policy.policy_number)
    assert isinstance(bills, list)
    print(f"  OK: get_policy_bills returned {len(bills)} bills")

    # Test get_payment_history
    payments = get_payment_history(session, policy.policy_number)
    assert isinstance(payments, list)
    print(f"  OK: get_payment_history returned {len(payments)} payments")

    session.close()


def run_all_tests():
    print("=" * 60)
    print("  INSURANCE BILLING MCP SERVER - TEST SUITE")
    print("=" * 60)

    tests = [test_database_creation, test_sample_data, test_queries, test_policy_lookup]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
