#!/usr/bin/env python3
"""
Demonstration script for the P&C Insurance Billing MCP Server.
This script creates the database, populates it with sample data,
and runs some example queries to show the system in action.
"""

from database import create_database, populate_sample_data, get_engine, get_session
from queries import (
    get_billing_dashboard,
    get_policy_summary,
    search_policies,
    get_overdue_bills,
    get_revenue_summary,
    get_active_policies,
)
from config import DATABASE_PATH
import json


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    print_section("P&C Insurance Billing System - Demonstration")

    print("\n1. Creating database and populating with sample data...")
    engine = create_database(DATABASE_PATH)
    populate_sample_data(engine)
    print("   Database created successfully!")

    session = get_session(engine)

    print_section("2. Billing Dashboard Overview")
    dashboard = get_billing_dashboard(session)
    print(json.dumps(dashboard, indent=2))

    print_section("3. Active Policies")
    active_policies = get_active_policies(session)
    print(f"\n   Found {len(active_policies)} active policies\n")
    for policy in active_policies[:5]:
        print(
            f"   - {policy.policy_number}: {policy.insured_name} ({policy.policy_type})"
        )
    if len(active_policies) > 5:
        print(f"   ... and {len(active_policies) - 5} more")

    print_section("4. Policy Summary Example")
    sample_policy = active_policies[0] if active_policies else None
    if sample_policy:
        summary = get_policy_summary(session, sample_policy.policy_number)
        print(json.dumps(summary, indent=2))

    print_section("5. Search Policies")
    search_results = search_policies(session, "Auto")
    print(f"\n   Found {len(search_results)} policies matching 'Auto'\n")
    for policy in search_results[:3]:
        print(f"   - {policy.policy_number}: {policy.insured_name}")

    print_section("6. Overdue Bills")
    overdue = get_overdue_bills(session)
    print(f"\n   Found {len(overdue)} overdue bills\n")
    for bill in overdue[:5]:
        print(
            f"   - {bill.bill_number}: ${bill.amount_due - bill.amount_paid:.2f} outstanding"
        )
    if len(overdue) > 5:
        print(f"   ... and {len(overdue) - 5} more")

    print_section("7. Revenue Summary")
    for period in ["month", "quarter", "year"]:
        revenue = get_revenue_summary(session, period)
        print(f"\n   {period.capitalize()}:")
        print(f"   - Total Revenue: ${revenue['total_revenue']:,.2f}")
        print(f"   - Payment Count: {revenue['payment_count']}")
        print(f"   - Average Payment: ${revenue['average_payment']:,.2f}")

    session.close()

    print_section("Demonstration Complete!")
    print("\nThe MCP server is ready to use. Run with:")
    print("  python server.py")
    print("\nOr integrate with your MCP client to query insurance billing data.")


if __name__ == "__main__":
    main()
