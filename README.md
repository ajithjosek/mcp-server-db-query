# P&C Insurance Billing MCP Server

An MCP (Model Context Protocol) server for querying Property & Casualty insurance billing data. Built with Python, SQLAlchemy, and SQLite.

## Features

- **Policy Management**: Search policies by number, name, or type
- **Billing Queries**: View bills, payments, and revenue summaries
- **Dashboard**: Get real-time billing metrics and financial overviews
- **MCP Protocol**: Standard interface for AI assistants and tools to query insurance data

## Project Structure

```
├── config.py           # Configuration and environment settings
├── database.py         # Database models (Policy, Bill, Payment) and sample data
├── queries.py          # Query functions for insurance billing data
├── server.py           # MCP server implementation
├── demo.py             # Demonstration script
├── requirements.txt    # Python dependencies
└── insurance_billing.db # SQLite database (created on first run)
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the demonstration:
```bash
python demo.py
```

### Start the MCP server:
```bash
python server.py
```

The server runs via stdio and can be integrated with MCP-compatible clients.

## Available Tools

- `get_policy_summary` - Get detailed policy information with billing history
- `search_policies` - Search policies by number, name, or type
- `get_policies_by_type` - Filter policies by type (Auto, Homeowners, etc.)
- `get_active_policies` - List all active policies
- `get_policy_bills` - Get bills for a specific policy
- `get_overdue_bills` - Find all overdue bills
- `get_pending_bills` - Find all pending bills
- `get_payment_history` - Get payment history for a policy
- `get_revenue_summary` - Revenue summary by period (month/quarter/year)
- `get_billing_dashboard` - Overall dashboard with key metrics

## Database Schema

- **Policies**: Policy number, type, insured name, dates, premium, status
- **Bills**: Bill number, policy relationship, dates, amounts, status
- **Payments**: Payment details linked to bills

Sample data is auto-generated on first run with 20 policies and billing records.

## Configuration

Environment variables (see `.env.example`):
- `DATABASE_PATH`: SQLite database file location
- `LOG_LEVEL`: Logging level
- `SERVER_HOST/SERVER_PORT`: Network settings (for future HTTP interface)