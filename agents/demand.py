"""
Demand Analysis Agent: Analyzes burn rate, projects stockout day (T_zero),
and computes the exact quantity needed to bridge the supply gap.
"""
import math

class DemandAnalysisAgent:
    def __init__(self):
        self.name = "Demand Analysis Agent"
        self.role = "Runway Projection, Stockout Timing & Unit Deficit Sizing"

    def analyze(self, item: dict, monitoring_result: dict, demand_surge_pct: float = 0.0) -> dict:
        current_stock = item["current_stock"]
        base_demand = item["daily_demand"]
        safety_stock = item["safety_stock"]
        new_arrival_days = monitoring_result["new_arrival_days"]

        effective_demand = base_demand * (1 + demand_surge_pct / 100.0)

        # Time until stock hits 0
        stockout_day = current_stock / effective_demand if effective_demand > 0 else 999
        # Days where we have zero stock before shipment arrives
        gap_days = max(0.0, new_arrival_days - stockout_day)

        # Net units consumed during the entire wait period until shipment arrives
        total_demand_until_arrival = new_arrival_days * effective_demand
        # Net deficit to prevent stockout and maintain safety stock buffer
        raw_deficit = total_demand_until_arrival - current_stock + safety_stock
        unit_deficit = max(0, math.ceil(raw_deficit))

        # Minimum units needed just to not drop below 0 stock (bare minimum bridge)
        bridge_minimum_units = max(0, math.ceil(gap_days * effective_demand))

        thought_log = [
            f"Effective daily demand is {effective_demand:.1f} units/day (Base: {base_demand}, Surge: +{demand_surge_pct}%).",
            f"Stockout predicted to occur on Day {stockout_day:.1f}.",
            f"Shipment arrival is Day {new_arrival_days}. Supply gap duration: {gap_days:.1f} days without stock.",
            f"Bridge requirement: Minimum {bridge_minimum_units} units to prevent line shutdown, or {unit_deficit} units to fully restore safety stock buffer ({safety_stock} units)."
        ]

        summary = (
            f"Calculated deficit of {unit_deficit} units required before Day {math.floor(stockout_day)} "
            f"to cover a {gap_days:.1f}-day stockout gap."
        )

        return {
            "agent": self.name,
            "effective_demand": round(effective_demand, 1),
            "stockout_day": round(stockout_day, 1),
            "gap_days": round(gap_days, 1),
            "bridge_minimum_units": bridge_minimum_units,
            "unit_deficit": unit_deficit,
            "deadline_day": math.floor(stockout_day),
            "summary": summary,
            "thought_log": thought_log
        }
