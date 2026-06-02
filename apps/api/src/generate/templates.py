"""Pre-built tool templates for DeskForge."""
from typing import Any

TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "inventory-tracker",
        "name": "Inventory Tracker",
        "description": "Track stock levels, manage product inventory, and get alerts for low stock items.",
        "category": "operations",
        "icon": "📦",
        "prompt": "Create an inventory tracking dashboard with a searchable data table showing products, quantities, locations, and restock dates. Include KPI cards for total items, low stock alerts, and total value. Add a form to add new products and update stock levels.",
    },
    {
        "id": "employee-directory",
        "name": "Employee Directory",
        "description": "Manage employee information, departments, and contact details.",
        "category": "hr",
        "icon": "👥",
        "prompt": "Build an employee directory with a searchable table showing name, department, title, email, phone, and start date. Include a form to add new employees and edit existing records. Add department filter and KPI cards for headcount by department.",
    },
    {
        "id": "crm-dashboard",
        "name": "CRM Dashboard",
        "description": "Track leads, deals, and customer interactions in a simple CRM.",
        "category": "sales",
        "icon": "🤝",
        "prompt": "Create a CRM dashboard with a table of leads and deals showing company, contact, stage, value, and last activity. Include KPI cards for total pipeline value, deals won this month, and conversion rate. Add a form to create new leads and a bar chart showing deals by stage.",
    },
    {
        "id": "project-tracker",
        "name": "Project Tracker",
        "description": "Track project status, deadlines, and team assignments.",
        "category": "operations",
        "icon": "📋",
        "prompt": "Build a project tracker with a table showing project name, status, priority, assigned team member, start date, and deadline. Include KPI cards for total projects, on-track count, and overdue count. Add a form to create new projects and a pie chart showing projects by status.",
    },
    {
        "id": "support-tickets",
        "name": "Support Ticket System",
        "description": "Manage and track customer support tickets.",
        "category": "operations",
        "icon": "🎫",
        "prompt": "Create a support ticket system with a table showing ticket ID, customer name, subject, priority, status, and assigned agent. Include KPI cards for open tickets, average resolution time, and tickets resolved today. Add a form to create tickets and filters for status and priority.",
    },
    {
        "id": "expense-tracker",
        "name": "Expense Tracker",
        "description": "Track and categorize business expenses with reporting.",
        "category": "reporting",
        "icon": "💰",
        "prompt": "Build an expense tracker with a table showing date, description, category, amount, and submitted by. Include KPI cards for total expenses this month, average expense, and largest expense. Add a form to submit expenses and a bar chart showing expenses by category.",
    },
    {
        "id": "event-registration",
        "name": "Event Registration",
        "description": "Manage event attendees and registrations.",
        "category": "operations",
        "icon": "📅",
        "prompt": "Create an event registration system with a table showing attendee name, email, event, registration date, and status. Include KPI cards for total registrations, confirmed attendees, and capacity used. Add a form to register attendees and a line chart showing registrations over time.",
    },
    {
        "id": "sales-reporting",
        "name": "Sales Reporting",
        "description": "Visualize sales data with charts and key metrics.",
        "category": "reporting",
        "icon": "📊",
        "prompt": "Build a sales reporting dashboard with KPI cards for total revenue, deals closed, and average deal size. Include a line chart showing revenue over time, a bar chart showing sales by rep, and a table of recent deals with company, amount, rep, and close date.",
    },
    {
        "id": "candidate-tracker",
        "name": "Candidate Tracker",
        "description": "Track job applicants through the hiring pipeline.",
        "category": "hr",
        "icon": "🎯",
        "prompt": "Create a candidate tracking system with a table showing candidate name, position, stage (applied, screening, interview, offer, hired), applied date, and recruiter. Include KPI cards for open positions, total candidates, and hires this month. Add a form to add candidates and a pie chart showing candidates by stage.",
    },
    {
        "id": "asset-management",
        "name": "Asset Management",
        "description": "Track company assets, assignments, and maintenance schedules.",
        "category": "operations",
        "icon": "🖥️",
        "prompt": "Build an asset management tool with a table showing asset name, type, serial number, assigned to, status, and purchase date. Include KPI cards for total assets, available assets, and assets needing maintenance. Add a form to add new assets and a bar chart showing assets by type.",
    },
    {
        "id": "customer-feedback",
        "name": "Customer Feedback",
        "description": "Collect and analyze customer feedback and ratings.",
        "category": "reporting",
        "icon": "⭐",
        "prompt": "Create a customer feedback dashboard with a table showing customer name, rating, category, feedback text, date, and status. Include KPI cards for average rating, total responses, and NPS score. Add a bar chart showing feedback by category and a line chart showing ratings over time.",
    },
    {
        "id": "meeting-room-booking",
        "name": "Meeting Room Booking",
        "description": "Book and manage meeting room reservations.",
        "category": "operations",
        "icon": "🏢",
        "prompt": "Build a meeting room booking system with a table showing room name, booked by, date, start time, end time, and purpose. Include KPI cards for rooms available today, total bookings this week, and most used room. Add a form to create bookings and a bar chart showing bookings by room.",
    },
]


def get_all_templates() -> list[dict]:
    return TEMPLATES


def get_template_by_id(template_id: str) -> dict | None:
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return None


def get_templates_by_category(category: str) -> list[dict]:
    return [t for t in TEMPLATES if t["category"] == category]
