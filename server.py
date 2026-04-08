from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError
from pydantic import AnyUrl
import mcp.server.stdio
import asyncio
import json
from datetime import datetime
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
    get_policy_by_number,
    get_policies_by_type,
    get_active_policies,
    get_policy_bills,
    get_overdue_bills,
    get_pending_bills,
    get_bills_by_date_range,
    get_payment_history,
    get_revenue_summary,
    get_policy_summary,
    get_billing_dashboard,
    search_policies,
)
from config import DATABASE_PATH
from sqlalchemy import func


def serialize_policy(policy):
    return {
        "policy_number": policy.policy_number,
        "policy_type": policy.policy_type,
        "insured_name": policy.insured_name,
        "effective_date": policy.effective_date.strftime("%Y-%m-%d"),
        "expiration_date": policy.expiration_date.strftime("%Y-%m-%d"),
        "premium_amount": policy.premium_amount,
        "status": policy.status,
    }


def serialize_bill(bill):
    return {
        "bill_number": bill.bill_number,
        "policy_id": bill.policy_id,
        "bill_date": bill.bill_date.strftime("%Y-%m-%d"),
        "due_date": bill.due_date.strftime("%Y-%m-%d"),
        "amount_due": bill.amount_due,
        "amount_paid": bill.amount_paid,
        "status": bill.status,
        "payment_date": bill.payment_date.strftime("%Y-%m-%d")
        if bill.payment_date
        else None,
    }


def serialize_payment(payment):
    return {
        "payment_number": payment.payment_number,
        "bill_id": payment.bill_id,
        "payment_date": payment.payment_date.strftime("%Y-%m-%d"),
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "transaction_id": payment.transaction_id,
    }


async def run_server():
    engine = create_database(DATABASE_PATH)

    Session = get_session(engine)
    policy_count = Session.query(func.count(Policy.id)).scalar()
    Session.close()

    if policy_count == 0:
        populate_sample_data(engine)

    server = Server("insurance-billing-query")

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri=AnyUrl("billing://dashboard"),
                name="Billing Dashboard",
                description="Overview of billing statistics including policies, bills, and financials",
                mimeType="application/json",
            ),
            Resource(
                uri=AnyUrl("billing://revenue/summary"),
                name="Revenue Summary",
                description="Revenue summary by period",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        if str(uri) == "billing://dashboard":
            engine = get_engine(DATABASE_PATH)
            session = get_session(engine)
            try:
                dashboard = get_billing_dashboard(session)
                return json.dumps(dashboard, indent=2)
            finally:
                session.close()

        elif str(uri) == "billing://revenue/summary":
            engine = get_engine(DATABASE_PATH)
            session = get_session(engine)
            try:
                revenue = get_revenue_summary(session, "month")
                return json.dumps(revenue, indent=2)
            finally:
                session.close()

        else:
            raise ValueError(f"Unknown resource: {uri}")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_policy_summary",
                description="Get detailed summary of a policy including billing and payment history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "policy_number": {
                            "type": "string",
                            "description": "Policy number to look up (e.g., POL-2024001)",
                        }
                    },
                    "required": ["policy_number"],
                },
            ),
            Tool(
                name="search_policies",
                description="Search policies by policy number, insured name, or policy type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Search term to match against policy number, name, or type",
                        }
                    },
                    "required": ["search_term"],
                },
            ),
            Tool(
                name="get_policies_by_type",
                description="Get all policies of a specific type (Auto, Homeowners, Commercial Property, General Liability, Workers Compensation)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "policy_type": {
                            "type": "string",
                            "description": "Type of policy to filter by",
                        }
                    },
                    "required": ["policy_type"],
                },
            ),
            Tool(
                name="get_active_policies",
                description="Get all active policies",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_policy_bills",
                description="Get all bills for a specific policy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "policy_number": {
                            "type": "string",
                            "description": "Policy number to get bills for",
                        }
                    },
                    "required": ["policy_number"],
                },
            ),
            Tool(
                name="get_overdue_bills",
                description="Get all overdue bills",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_pending_bills",
                description="Get all pending bills",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_payment_history",
                description="Get payment history for a specific policy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "policy_number": {
                            "type": "string",
                            "description": "Policy number to get payment history for",
                        }
                    },
                    "required": ["policy_number"],
                },
            ),
            Tool(
                name="get_revenue_summary",
                description="Get revenue summary for a specified period (month, quarter, year)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "description": "Time period for summary (month, quarter, year)",
                            "default": "month",
                        }
                    },
                },
            ),
            Tool(
                name="get_billing_dashboard",
                description="Get overall billing dashboard with key metrics",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        engine = get_engine(DATABASE_PATH)
        session = get_session(engine)

        try:
            if name == "get_policy_summary":
                policy_number = arguments.get("policy_number")
                result = get_policy_summary(session, policy_number)
                if result is None:
                    return [
                        TextContent(
                            type="text", text=f"Policy {policy_number} not found"
                        )
                    ]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "search_policies":
                search_term = arguments.get("search_term", "")
                policies = search_policies(session, search_term)
                if not policies:
                    return [TextContent(type="text", text="No policies found")]
                result = [serialize_policy(p) for p in policies]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_policies_by_type":
                policy_type = arguments.get("policy_type", "")
                policies = get_policies_by_type(session, policy_type)
                if not policies:
                    return [
                        TextContent(
                            type="text",
                            text=f"No policies found of type: {policy_type}",
                        )
                    ]
                result = [serialize_policy(p) for p in policies]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_active_policies":
                policies = get_active_policies(session)
                if not policies:
                    return [TextContent(type="text", text="No active policies found")]
                result = [serialize_policy(p) for p in policies]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_policy_bills":
                policy_number = arguments.get("policy_number")
                bills = get_policy_bills(session, policy_number)
                if not bills:
                    return [
                        TextContent(
                            type="text",
                            text=f"No bills found for policy {policy_number}",
                        )
                    ]
                result = [serialize_bill(b) for b in bills]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_overdue_bills":
                bills = get_overdue_bills(session)
                if not bills:
                    return [TextContent(type="text", text="No overdue bills found")]
                result = [serialize_bill(b) for b in bills]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_pending_bills":
                bills = get_pending_bills(session)
                if not bills:
                    return [TextContent(type="text", text="No pending bills found")]
                result = [serialize_bill(b) for b in bills]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_payment_history":
                policy_number = arguments.get("policy_number")
                payments = get_payment_history(session, policy_number)
                if not payments:
                    return [
                        TextContent(
                            type="text",
                            text=f"No payments found for policy {policy_number}",
                        )
                    ]
                result = [serialize_payment(p) for p in payments]
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_revenue_summary":
                period = arguments.get("period", "month")
                revenue = get_revenue_summary(session, period)
                return [TextContent(type="text", text=json.dumps(revenue, indent=2))]

            elif name == "get_billing_dashboard":
                dashboard = get_billing_dashboard(session)
                return [TextContent(type="text", text=json.dumps(dashboard, indent=2))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        finally:
            session.close()

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="insurance-billing-query",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run_server())
