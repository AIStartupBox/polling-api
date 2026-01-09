"""
Report Runner node - Processes identified reports.

This node simulates processing each identified report and extracting data.
"""

import asyncio
from typing import Dict, Any
from state import AppState


async def report_runner(app_state: AppState) -> Dict[str, Any]:
    """
    Process each identified report and extract data.

    Args:
        app_state: Current application state

    Returns:
        Updated state with processed report data
    """
    # Check interrupt flag - if True, skip processing
    if app_state.get("Interrupt", False):
        return {"state": app_state["state"].copy(), "Interrupt": True}

    current = app_state["state"].copy()

    reports = current["data"].get("reports", [])
    processed_data = []

    # Process each report with progress updates
    for idx, report in enumerate(reports, 1):
        # Update UI to show current progress
        current["ui"] = {
            "message": f"📊 Processing {report} ({idx}/{len(reports)})",
            "current_node": "report_runner",
            "status": "running",
            "progress": {"current": 3, "total": 4}
        }

        # Simulate processing time
        await asyncio.sleep(1.0)

        # Mock data extraction based on file type
        if "sales" in report.lower():
            processed_data.append({
                "file": report,
                "type": "sales",
                "metrics": {
                    "total_revenue": 2500000,
                    "growth_yoy": "23%",
                    "top_product": "Product A",
                    "top_product_contribution": "60%"
                }
            })
        elif "revenue" in report.lower():
            processed_data.append({
                "file": report,
                "type": "revenue",
                "metrics": {
                    "total_revenue": 2500000,
                    "recurring_revenue": 1800000,
                    "new_customers": 450,
                    "churn_rate": "3.2%"
                }
            })
        elif "marketing" in report.lower():
            processed_data.append({
                "file": report,
                "type": "marketing",
                "metrics": {
                    "campaign_roi": "340%",
                    "leads_generated": 1200,
                    "conversion_rate": "12%"
                }
            })
        elif "financial" in report.lower() or "budget" in report.lower():
            processed_data.append({
                "file": report,
                "type": "financial",
                "metrics": {
                    "budget_utilization": "87%",
                    "cost_savings": 150000,
                    "expenses_yoy": "-5%"
                }
            })
        else:
            processed_data.append({
                "file": report,
                "type": "general",
                "metrics": {}
            })

    # Final UI update for this node
    current["ui"] = {
        "message": f"✅ Processed {len(reports)} report(s) successfully",
        "current_node": "report_runner",
        "status": "running",
        "progress": {"current": 3, "total": 4}
    }

    # Store processed data
    current["data"]["processed_reports"] = processed_data
    current["data"]["step"] = "reports_processed"

    return {"state": current, "Interrupt": False}
