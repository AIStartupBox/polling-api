"""
Report Identifier node - Identifies relevant reports based on user query.

This node analyzes the user's message and determines which reports to process.
"""

import asyncio
from typing import Dict, Any

from state import AppState


async def report_identifier(app_state: AppState) -> Dict[str, Any]:
    """
    Identify relevant reports based on user query.

    Args:
        app_state: Current application state

    Returns:
        Updated state with identified reports list
    """
    current = app_state["state"].copy()
    user_query = current.get("message", "")

    print(f"→ Entering report_identifier node - Query: '{user_query}'")

    # Check interrupt flag - if True, skip processing
    if app_state.get("Interrupt", False):
        print("→ Report_identifier node - Interrupt flag detected, skipping processing")
        return {"state": app_state["state"].copy(), "Interrupt": True}

    # Simulate report identification processing
    await asyncio.sleep(1.0)

    # Mock report identification based on query keywords
    user_query_lower = user_query.lower()
    identified_reports = []

    # Simple keyword-based report identification
    if "sales" in user_query_lower or "q4" in user_query_lower or "revenue" in user_query_lower:
        identified_reports = ["sales_q4.pdf", "revenue_q4.xlsx"]
    elif "marketing" in user_query_lower:
        identified_reports = ["marketing_report.pdf"]
    elif "finance" in user_query_lower:
        identified_reports = ["financial_summary.xlsx", "budget_q4.pdf"]
    else:
        # Default reports for generic queries
        identified_reports = ["sales_q4.pdf", "revenue_q4.xlsx"]

    print(f"  Report_identifier node - Identified {len(identified_reports)} reports: {identified_reports}")

    # Update UI state
    current["ui"] = {
        "message": f"📋 Found {len(identified_reports)} relevant report(s): {', '.join(identified_reports)}",
        "current_node": "report_identifier",
        "status": "running",
        "progress": {"current": 2, "total": 4}
    }

    # Store identified reports in data
    current["data"]["reports"] = identified_reports
    current["data"]["step"] = "reports_identified"

    print(f"← Leaving report_identifier node - Reports: {identified_reports}, Status: reports_identified")

    return {"state": current, "Interrupt": False}
