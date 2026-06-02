#!/usr/bin/env python3
"""
DeskForge — Database Seeding Script

Seeds the database with:
- Default templates (12 templates)
- Test user + team
- Sample tools
- Test data sources

Usage:
    python infra/scripts/seed.py
    python infra/scripts/seed.py --env staging
    python infra/scripts/seed.py --reset  # Drops and recreates seed data
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))

import asyncpg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://deskforge:password@localhost:5432/deskforge",
).replace("+asyncpg", "")


# ============================================================
# Template Definitions (12 templates)
# ============================================================

TEMPLATES = [
    {
        "id": str(uuid4()),
        "name": "KPI Dashboard",
        "description": "A dashboard displaying key performance indicators with KPI cards and trend charts.",
        "category": "dashboard",
        "prompt": "Create a KPI dashboard that shows key metrics like revenue, users, and conversion rates with trend charts.",
        "spec": json.dumps({
            "version": 1,
            "name": "KPI Dashboard",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "kpi-1", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 3}, "props": {"title": "Total Revenue", "format": "currency"}},
                {"id": "kpi-2", "type": "kpiCard", "position": {"row": 1, "col": 4, "colSpan": 3}, "props": {"title": "Active Users", "format": "number"}},
                {"id": "kpi-3", "type": "kpiCard", "position": {"row": 1, "col": 7, "colSpan": 3}, "props": {"title": "Conversion Rate", "format": "percent"}},
                {"id": "kpi-4", "type": "kpiCard", "position": {"row": 1, "col": 10, "colSpan": 3}, "props": {"title": "Avg Order Value", "format": "currency"}},
                {"id": "chart-1", "type": "lineChart", "position": {"row": 2, "col": 1, "colSpan": 8}, "props": {"title": "Revenue Trend", "xKey": "date", "yKey": "revenue"}},
                {"id": "chart-2", "type": "pieChart", "position": {"row": 2, "col": 9, "colSpan": 4}, "props": {"title": "Revenue by Category", "nameKey": "category", "valueKey": "amount"}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Data Table Viewer",
        "description": "A sortable, filterable data table with search and pagination.",
        "category": "data",
        "prompt": "Create a data table viewer with sorting, filtering, search, and pagination for viewing records.",
        "spec": json.dumps({
            "version": 1,
            "name": "Data Table Viewer",
            "layout": {"type": "single-column", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "search", "type": "form", "position": {"row": 1, "col": 1, "colSpan": 12}, "props": {"fields": [{"name": "search", "type": "text", "label": "Search"}], "layout": "inline"}},
                {"id": "table", "type": "dataTable", "position": {"row": 2, "col": 1, "colSpan": 12}, "props": {"sortable": True, "filterable": True, "paginated": True, "pageSize": 25}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Simple CRUD App",
        "description": "A basic CRUD application with a form to create/edit records and a table to view them.",
        "category": "crud",
        "prompt": "Create a simple CRUD application with a form for creating and editing records, and a data table to display them.",
        "spec": json.dumps({
            "version": 1,
            "name": "Simple CRUD App",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "form", "type": "form", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Save"}},
                {"id": "table", "type": "dataTable", "position": {"row": 1, "col": 5, "colSpan": 8}, "props": {"sortable": True, "paginated": True}}
            ],
            "dataSources": [],
            "actions": [{"id": "create", "type": "create", "triggerComponentId": "form"}]
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Sales Report",
        "description": "A sales reporting dashboard with bar charts, line charts, and summary KPIs.",
        "category": "dashboard",
        "prompt": "Create a sales report dashboard with bar charts for sales by region, line charts for trends, and KPI cards for totals.",
        "spec": json.dumps({
            "version": 1,
            "name": "Sales Report",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "total-sales", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"title": "Total Sales", "format": "currency"}},
                {"id": "avg-deal", "type": "kpiCard", "position": {"row": 1, "col": 5, "colSpan": 4}, "props": {"title": "Avg Deal Size", "format": "currency"}},
                {"id": "win-rate", "type": "kpiCard", "position": {"row": 1, "col": 9, "colSpan": 4}, "props": {"title": "Win Rate", "format": "percent"}},
                {"id": "bar-chart", "type": "barChart", "position": {"row": 2, "col": 1, "colSpan": 6}, "props": {"title": "Sales by Region", "xKey": "region", "yKey": "amount"}},
                {"id": "line-chart", "type": "lineChart", "position": {"row": 2, "col": 7, "colSpan": 6}, "props": {"title": "Monthly Trend", "xKey": "month", "yKey": "amount"}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Inventory Tracker",
        "description": "Track inventory levels with a searchable table and low-stock alerts.",
        "category": "crud",
        "prompt": "Create an inventory tracker that shows stock levels in a table with search, highlights low-stock items, and allows adding/editing items.",
        "spec": json.dumps({
            "version": 1,
            "name": "Inventory Tracker",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "low-stock", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"title": "Low Stock Items", "format": "number"}},
                {"id": "total-items", "type": "kpiCard", "position": {"row": 1, "col": 5, "colSpan": 4}, "props": {"title": "Total Items", "format": "number"}},
                {"id": "total-value", "type": "kpiCard", "position": {"row": 1, "col": 9, "colSpan": 4}, "props": {"title": "Total Value", "format": "currency"}},
                {"id": "form", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 3}, "props": {"fields": [], "submitLabel": "Add Item"}},
                {"id": "table", "type": "dataTable", "position": {"row": 2, "col": 4, "colSpan": 9}, "props": {"sortable": True, "filterable": True, "paginated": True}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Customer Feedback Board",
        "description": "Collect and analyze customer feedback with forms and visualizations.",
        "category": "data",
        "prompt": "Create a customer feedback board with a form to submit feedback, a table to view all submissions, and charts to analyze sentiment and categories.",
        "spec": json.dumps({
            "version": 1,
            "name": "Customer Feedback Board",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "submit", "type": "form", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Submit Feedback"}},
                {"id": "table", "type": "dataTable", "position": {"row": 1, "col": 5, "colSpan": 8}, "props": {"sortable": True, "paginated": True, "pageSize": 10}},
                {"id": "sentiment", "type": "pieChart", "position": {"row": 2, "col": 1, "colSpan": 6}, "props": {"title": "Sentiment Distribution", "nameKey": "sentiment", "valueKey": "count"}},
                {"id": "categories", "type": "barChart", "position": {"row": 2, "col": 7, "colSpan": 6}, "props": {"title": "Feedback by Category", "xKey": "category", "yKey": "count"}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Project Task Manager",
        "description": "Manage project tasks with status tracking and progress visualization.",
        "category": "crud",
        "prompt": "Create a project task manager with task creation form, status columns, progress tracking, and team workload charts.",
        "spec": json.dumps({
            "version": 1,
            "name": "Project Task Manager",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "todo-count", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 3}, "props": {"title": "To Do", "format": "number"}},
                {"id": "progress-count", "type": "kpiCard", "position": {"row": 1, "col": 4, "colSpan": 3}, "props": {"title": "In Progress", "format": "number"}},
                {"id": "done-count", "type": "kpiCard", "position": {"row": 1, "col": 7, "colSpan": 3}, "props": {"title": "Done", "format": "number"}},
                {"id": "total-count", "type": "kpiCard", "position": {"row": 1, "col": 10, "colSpan": 3}, "props": {"title": "Total", "format": "number"}},
                {"id": "task-form", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Add Task"}},
                {"id": "task-table", "type": "dataTable", "position": {"row": 2, "col": 5, "colSpan": 8}, "props": {"sortable": True, "filterable": True}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Employee Directory",
        "description": "Browse and search employees with department filters and contact details.",
        "category": "data",
        "prompt": "Create an employee directory with search, department filtering, and a data table showing contact information.",
        "spec": json.dumps({
            "version": 1,
            "name": "Employee Directory",
            "layout": {"type": "single-column", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "filters", "type": "form", "position": {"row": 1, "col": 1, "colSpan": 12}, "props": {"fields": [], "layout": "inline"}},
                {"id": "directory", "type": "dataTable", "position": {"row": 2, "col": 1, "colSpan": 12}, "props": {"sortable": True, "filterable": True, "paginated": True, "pageSize": 20}}
            ],
            "dataSources": []
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Expense Tracker",
        "description": "Track expenses with category breakdowns and monthly trend analysis.",
        "category": "dashboard",
        "prompt": "Create an expense tracker with a form to add expenses, a table to view them, and charts for category breakdown and monthly trends.",
        "spec": json.dumps({
            "version": 1,
            "name": "Expense Tracker",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "total-expense", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"title": "Total Expenses", "format": "currency"}},
                {"id": "avg-expense", "type": "kpiCard", "position": {"row": 1, "col": 5, "colSpan": 4}, "props": {"title": "Avg per Entry", "format": "currency"}},
                {"id": "count", "type": "kpiCard", "position": {"row": 1, "col": 9, "colSpan": 4}, "props": {"title": "Entries", "format": "number"}},
                {"id": "add-form", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Add Expense"}},
                {"id": "expense-table", "type": "dataTable", "position": {"row": 2, "col": 5, "colSpan": 8}, "props": {"sortable": True, "paginated": True}},
                {"id": "category-chart", "type": "pieChart", "position": {"row": 3, "col": 1, "colSpan": 6}, "props": {"title": "By Category", "nameKey": "category", "valueKey": "amount"}},
                {"id": "trend-chart", "type": "lineChart", "position": {"row": 3, "col": 7, "colSpan": 6}, "props": {"title": "Monthly Trend", "xKey": "month", "yKey": "amount"}}
            ],
            "dataSources": [],
            "actions": [{"id": "add-expense", "type": "create", "triggerComponentId": "add-form"}]
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Support Ticket System",
        "description": "Manage support tickets with priority tracking and status updates.",
        "category": "crud",
        "prompt": "Create a support ticket system with ticket creation, priority levels, status tracking, and a dashboard showing ticket metrics.",
        "spec": json.dumps({
            "version": 1,
            "name": "Support Ticket System",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "open-tickets", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 3}, "props": {"title": "Open", "format": "number"}},
                {"id": "in-progress", "type": "kpiCard", "position": {"row": 1, "col": 4, "colSpan": 3}, "props": {"title": "In Progress", "format": "number"}},
                {"id": "resolved", "type": "kpiCard", "position": {"row": 1, "col": 7, "colSpan": 3}, "props": {"title": "Resolved Today", "format": "number"}},
                {"id": "avg-resolve", "type": "kpiCard", "position": {"row": 1, "col": 10, "colSpan": 3}, "props": {"title": "Avg Resolution", "format": "text"}},
                {"id": "new-ticket", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Create Ticket"}},
                {"id": "ticket-list", "type": "dataTable", "position": {"row": 2, "col": 5, "colSpan": 8}, "props": {"sortable": True, "filterable": True, "paginated": True}}
            ],
            "dataSources": [],
            "actions": [{"id": "create-ticket", "type": "create", "triggerComponentId": "new-ticket"}]
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Event Calendar",
        "description": "View and manage events with a data table and event statistics.",
        "category": "data",
        "prompt": "Create an event management tool with event creation form, upcoming events table, and event statistics by category.",
        "spec": json.dumps({
            "version": 1,
            "name": "Event Calendar",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "total-events", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 4}, "props": {"title": "Upcoming Events", "format": "number"}},
                {"id": "this-week", "type": "kpiCard", "position": {"row": 1, "col": 5, "colSpan": 4}, "props": {"title": "This Week", "format": "number"}},
                {"id": "this-month", "type": "kpiCard", "position": {"row": 1, "col": 9, "colSpan": 4}, "props": {"title": "This Month", "format": "number"}},
                {"id": "event-form", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Add Event"}},
                {"id": "event-table", "type": "dataTable", "position": {"row": 2, "col": 5, "colSpan": 8}, "props": {"sortable": True, "paginated": True}},
                {"id": "category-chart", "type": "barChart", "position": {"row": 3, "col": 1, "colSpan": 12}, "props": {"title": "Events by Category", "xKey": "category", "yKey": "count"}}
            ],
            "dataSources": [],
            "actions": [{"id": "add-event", "type": "create", "triggerComponentId": "event-form"}]
        }),
    },
    {
        "id": str(uuid4()),
        "name": "Bug Tracker",
        "description": "Track software bugs with severity levels, assignment, and resolution metrics.",
        "category": "crud",
        "prompt": "Create a bug tracking tool with bug submission form, severity classification, assignment tracking, and a dashboard with bug metrics.",
        "spec": json.dumps({
            "version": 1,
            "name": "Bug Tracker",
            "layout": {"type": "grid", "columns": 12, "gap": "1rem"},
            "components": [
                {"id": "critical", "type": "kpiCard", "position": {"row": 1, "col": 1, "colSpan": 3}, "props": {"title": "Critical", "format": "number"}},
                {"id": "high", "type": "kpiCard", "position": {"row": 1, "col": 4, "colSpan": 3}, "props": {"title": "High", "format": "number"}},
                {"id": "medium", "type": "kpiCard", "position": {"row": 1, "col": 7, "colSpan": 3}, "props": {"title": "Medium", "format": "number"}},
                {"id": "low", "type": "kpiCard", "position": {"row": 1, "col": 10, "colSpan": 3}, "props": {"title": "Low", "format": "number"}},
                {"id": "bug-form", "type": "form", "position": {"row": 2, "col": 1, "colSpan": 4}, "props": {"fields": [], "submitLabel": "Submit Bug"}},
                {"id": "bug-table", "type": "dataTable", "position": {"row": 2, "col": 5, "colSpan": 8}, "props": {"sortable": True, "filterable": True, "paginated": True}}
            ],
            "dataSources": [],
            "actions": [{"id": "report-bug", "type": "create", "triggerComponentId": "bug-form"}]
        }),
    },
]


# ============================================================
# Test Data
# ============================================================

TEST_USER = {
    "id": str(uuid4()),
    "email": "demo@deskforge.io",
    "name": "Demo User",
    "email_verified": True,
    "auth_provider": "local",
}

TEST_TEAM = {
    "id": str(uuid4()),
    "name": "Demo Team",
    "plan": "pro",
}


async def seed_templates(conn):
    """Insert all template definitions."""
    print(f"  Seeding {len(TEMPLATES)} templates...")
    for tmpl in TEMPLATES:
        await conn.execute(
            """
            INSERT INTO templates (id, name, description, category, prompt, spec, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                spec = EXCLUDED.spec,
                updated_at = NOW()
            """,
            tmpl["id"],
            tmpl["name"],
            tmpl["description"],
            tmpl["category"],
            tmpl["prompt"],
            tmpl["spec"],
        )
    print(f"  ✓ {len(TEMPLATES)} templates seeded")


async def seed_test_data(conn):
    """Insert test user and team for development."""
    print("  Seeding test user and team...")

    # Check if test user exists
    existing = await conn.fetchval(
        "SELECT id FROM users WHERE email = $1", TEST_USER["email"]
    )

    if existing:
        print(f"  ⏭  Test user already exists: {TEST_USER['email']}")
        return

    # Create test user (password: "demo123456")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_context.hash("demo123456")

    await conn.execute(
        """
        INSERT INTO users (id, email, password_hash, name, email_verified, auth_provider, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6::auth_provider, NOW(), NOW())
        """,
        TEST_USER["id"],
        TEST_USER["email"],
        password_hash,
        TEST_USER["name"],
        TEST_USER["email_verified"],
        TEST_USER["auth_provider"],
    )

    # Create test team
    await conn.execute(
        """
        INSERT INTO teams (id, name, owner_id, plan, created_at, updated_at)
        VALUES ($1, $2, $3, $4::team_plan, NOW(), NOW())
        """,
        TEST_TEAM["id"],
        TEST_TEAM["name"],
        TEST_USER["id"],
        TEST_TEAM["plan"],
    )

    # Add user as team owner
    await conn.execute(
        """
        INSERT INTO team_members (id, team_id, user_id, role, invited_at, accepted_at)
        VALUES ($1, $2, $3, 'owner'::team_role, NOW(), NOW())
        """,
        str(uuid4()),
        TEST_TEAM["id"],
        TEST_USER["id"],
    )

    print(f"  ✓ Test user created: {TEST_USER['email']} (password: demo123456)")
    print(f"  ✓ Test team created: {TEST_TEAM['name']}")


async def check_tables_exist(conn):
    """Verify required tables exist."""
    tables = await conn.fetch(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('users', 'teams', 'team_members', 'templates')
        """
    )
    return {r["table_name"] for r in tables}


async def main(reset: bool = False):
    """Run the seed script."""
    print("🌱 DeskForge Database Seeder")
    print("=" * 50)

    # Parse connection params from URL
    url = DATABASE_URL.replace("postgresql://", "")
    user_pass, host_db = url.split("@")
    user, password = user_pass.split(":")
    host_port, db = host_db.split("/")
    host, port = host_port.split(":")

    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=db,
            host=host,
            port=int(port),
        )
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"   Connection URL: {DATABASE_URL}")
        sys.exit(1)

    try:
        # Check tables exist
        existing_tables = await check_tables_exist(conn)
        required_tables = {"users", "teams", "team_members"}
        missing = required_tables - existing_tables

        if missing:
            print(f"❌ Missing required tables: {missing}")
            print("   Run migrations first: bash infra/scripts/migrate.sh")
            sys.exit(1)

        if reset:
            print("🔄 Resetting seed data...")
            await conn.execute("DELETE FROM templates WHERE id = ANY($1)", [t["id"] for t in TEMPLATES])
            test_user_exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", TEST_USER["email"])
            if test_user_exists:
                await conn.execute("DELETE FROM team_members WHERE user_id = $1", TEST_USER["id"])
                await conn.execute("DELETE FROM teams WHERE owner_id = $1", TEST_USER["id"])
                await conn.execute("DELETE FROM users WHERE id = $1", TEST_USER["id"])
            print("  ✓ Seed data cleared")

        # Check if templates table exists
        if "templates" in existing_tables:
            await seed_templates(conn)
        else:
            print("  ⏭  Templates table not found, skipping templates seed")

        await seed_test_data(conn)

        print()
        print("=" * 50)
        print("✅ Seeding complete!")
        print()
        print("Test credentials:")
        print(f"  Email:    {TEST_USER['email']}")
        print(f"  Password: demo123456")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed DeskForge database")
    parser.add_argument("--reset", action="store_true", help="Reset seed data before inserting")
    args = parser.parse_args()

    asyncio.run(main(reset=args.reset))
