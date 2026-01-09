"""
Summary Agent node - Generates final summary and insights.

This node creates a comprehensive summary based on processed report data.
"""

import asyncio
from typing import Dict, Any, List
from state import AppState


async def summary_agent(app_state: AppState) -> Dict[str, Any]:
    """
    Generate comprehensive summary and insights from processed reports.

    Args:
        app_state: Current application state

    Returns:
        Updated state with final summary and completed status
    """
    current = app_state["state"].copy()

    # Simulate AI summary generation
    await asyncio.sleep(1.5)

    processed_reports = current["data"].get("processed_reports", [])

    # Generate insights based on processed data
    insights = []
    summary_text = ""

    if processed_reports:
        # Extract key metrics across all reports
        for report_data in processed_reports:
            report_type = report_data.get("type", "general")
            metrics = report_data.get("metrics", {})

            if report_type == "sales":
                if "growth_yoy" in metrics:
                    insights.append(f"Sales grew {metrics['growth_yoy']} year-over-year")
                if "top_product_contribution" in metrics:
                    insights.append(f"{metrics.get('top_product', 'Top product')} drove {metrics['top_product_contribution']} of growth")

            elif report_type == "revenue":
                if "total_revenue" in metrics:
                    insights.append(f"Total revenue reached ${metrics['total_revenue']:,}")
                if "new_customers" in metrics:
                    insights.append(f"Acquired {metrics['new_customers']} new customers")

            elif report_type == "marketing":
                if "campaign_roi" in metrics:
                    insights.append(f"Marketing campaigns achieved {metrics['campaign_roi']} ROI")
                if "conversion_rate" in metrics:
                    insights.append(f"Conversion rate improved to {metrics['conversion_rate']}")

            elif report_type == "financial":
                if "cost_savings" in metrics:
                    insights.append(f"Achieved ${metrics['cost_savings']:,} in cost savings")
                if "budget_utilization" in metrics:
                    insights.append(f"Budget utilization at {metrics['budget_utilization']}")

        # Generate summary text
        if any("sales" in r.get("type", "") for r in processed_reports):
            summary_text = "✅ Q4 sales analysis complete: +23% YoY growth driven by strong product performance and customer acquisition"
        elif any("marketing" in r.get("type", "") for r in processed_reports):
            summary_text = "✅ Marketing analysis complete: Campaign ROI exceeded expectations with strong lead generation"
        elif any("financial" in r.get("type", "") for r in processed_reports):
            summary_text = "✅ Financial analysis complete: Strong budget management with significant cost savings achieved"
        else:
            summary_text = f"✅ Analysis complete: Successfully processed {len(processed_reports)} report(s) with key insights extracted"
    else:
        summary_text = "✅ Analysis complete: No reports processed"
        insights = ["No data available for analysis"]

    # Update UI state - COMPLETED
    current["ui"] = {
        "message": summary_text,
        "current_node": "summary_agent",
        "status": "completed",
        "progress": {"current": 4, "total": 4}
    }

    # Store final summary and insights
    current["data"]["summary"] = summary_text
    current["data"]["insights"] = insights
    current["data"]["step"] = "completed"

    return {"state": current}
