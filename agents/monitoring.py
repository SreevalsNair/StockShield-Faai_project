"""
Monitoring Agent: Continuously evaluates inventory telemetry against shipment ETAs.
Flags delay disruptions and impending stockout conditions.
"""

class MonitoringAgent:
    def __init__(self):
        self.name = "Monitoring Agent"
        self.role = "Telemetry, Threshold Auditing & Disruption Detection"

    def assess(self, item: dict, simulated_delay_days: int) -> dict:
        sku = item["sku"]
        current_stock = item["current_stock"]
        daily_demand = item["daily_demand"]
        safety_stock = item["safety_stock"]
        incoming = item.get("incoming_po", {})
        
        base_arrival_days = incoming.get("scheduled_arrival_days", 5)
        new_arrival_days = base_arrival_days + simulated_delay_days

        days_of_stock_left = current_stock / daily_demand if daily_demand > 0 else 999
        days_until_safety_breached = max(0, (current_stock - safety_stock) / daily_demand) if daily_demand > 0 else 999

        # Determine risk level
        is_stockout_risk = new_arrival_days > days_of_stock_left
        is_safety_breach = new_arrival_days > days_until_safety_breached

        if is_stockout_risk:
            status = "CRITICAL_STOCKOUT_RISK"
            summary = (
                f"🚨 Severe disruption! Supplier delay of +{simulated_delay_days} days moves delivery ETA to Day {new_arrival_days}. "
                f"Current stock ({current_stock} units) will run out completely in {days_of_stock_left:.1f} days."
            )
        elif is_safety_breach:
            status = "SAFETY_STOCK_BREACH"
            summary = (
                f"⚠️ Disruption detected! Delivery ETA moved to Day {new_arrival_days}. "
                f"Inventory will breach safety buffer ({safety_stock} units) on Day {days_until_safety_breached:.1f}."
            )
        else:
            status = "NORMAL"
            summary = (
                f"✅ Inventory secure. Delivery on Day {new_arrival_days} arrives before stockout (Stock lasts {days_of_stock_left:.1f} days)."
            )

        thought_log = [
            f"Auditing SKU '{sku}' (Current Stock: {current_stock}, Burn Rate: {daily_demand}/day).",
            f"Baseline PO arrival was Day {base_arrival_days}. With injected delay (+{simulated_delay_days}d), revised ETA is Day {new_arrival_days}.",
            f"Calculated runway: Stock completely depletes on Day {days_of_stock_left:.1f}. Safety buffer breached on Day {days_until_safety_breached:.1f}.",
            f"Conclusion: Status is '{status}'."
        ]

        return {
            "agent": self.name,
            "status": status,
            "simulated_delay_days": simulated_delay_days,
            "base_arrival_days": base_arrival_days,
            "new_arrival_days": new_arrival_days,
            "days_of_stock_left": round(days_of_stock_left, 1),
            "days_until_safety_breached": round(days_until_safety_breached, 1),
            "disruption_flagged": is_stockout_risk or is_safety_breach,
            "summary": summary,
            "thought_log": thought_log
        }
