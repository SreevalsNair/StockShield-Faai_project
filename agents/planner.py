"""
Recovery Planning Agent: Formulates replenishment recovery strategies
(Speed-Priority, Cost-Optimized, and Split-Batch Sourcing).
Adapts dynamically when the Critic Agent provides rejection feedback.
"""
import math

class RecoveryPlanningAgent:
    def __init__(self):
        self.name = "Recovery Planning Agent"
        self.role = "Replenishment Strategy Formulation & Adaptive Replanning"

    def formulate_plan(
        self,
        sku: str,
        demand_info: dict,
        supplier_info: dict,
        critic_feedback: dict = None,
        attempt: int = 1
    ) -> dict:
        options = supplier_info["options"]
        unit_deficit = demand_info["unit_deficit"]
        bridge_minimum = demand_info["bridge_minimum_units"]
        deadline_day = demand_info["deadline_day"]

        thought_log = [
            f"Drafting replenishment recovery plan for SKU: '{sku}' (Attempt #{attempt}).",
            f"Required recovery volume: {unit_deficit} units. Immediate stockout deadline: Day {deadline_day}."
        ]

        # Filter options that arrive on or before deadline
        on_time_options = [o for o in options if o["meets_deadline"]]
        if not on_time_options:
            # Fallback to absolute fastest option even if tight
            on_time_options = [min(options, key=lambda x: x["lead_time_days"])]

        fastest_opt = min(on_time_options, key=lambda x: x["lead_time_days"])
        cheapest_on_time_opt = min(on_time_options, key=lambda x: x["landed_unit_cost"])

        # Decide strategy based on attempt and critique
        if attempt == 1 and not critic_feedback:
            # Strategy: Full Speed Sourcing (aggressive default)
            selected_strategy = "EXPRESS_SOLO"
            thought_log.append("Attempt #1 Strategy: Prioritize 100% risk elimination via fastest premium supplier.")
            
            batches = [
                {
                    "batch_label": "Primary Expedited Batch",
                    "supplier_id": fastest_opt["supplier_id"],
                    "supplier_name": fastest_opt["supplier_name"],
                    "freight_mode": fastest_opt["freight_mode"],
                    "units": unit_deficit,
                    "lead_time_days": fastest_opt["lead_time_days"],
                    "unit_cost": fastest_opt["landed_unit_cost"],
                    "total_cost": round(unit_deficit * fastest_opt["landed_unit_cost"], 2)
                }
            ]
        else:
            # Planner adapts after receiving Critic feedback!
            selected_strategy = "SPLIT_BATCH_BALANCED"
            budget_cap = critic_feedback.get("budget_cap", 15000.0) if critic_feedback else 15000.0
            thought_log.append(f"Received Critic rejection: '{critic_feedback.get('reason', '')}'.")
            thought_log.append(f"Adapting strategy: Dual-Source Split-Batch with budget target <= ${budget_cap:,.2f}.")

            # Bridge batch: prioritize enough units to bridge until standard batch arrives
            # Standard batch arrives in cheapest_on_time_opt['lead_time_days']
            bridge_days = max(1, cheapest_on_time_opt["lead_time_days"] - fastest_opt["lead_time_days"] + 2)
            emergency_bridge_units = min(unit_deficit, math.ceil(bridge_days * demand_info["effective_demand"]))
            
            # Remaining units allocated to cost-optimized supplier
            remaining_deficit = unit_deficit - emergency_bridge_units
            
            # Ensure within budget cap
            express_cost = emergency_bridge_units * fastest_opt["landed_unit_cost"]
            remaining_budget = max(0.0, budget_cap - express_cost)
            bulk_affordable_units = math.floor(remaining_budget / cheapest_on_time_opt["landed_unit_cost"])
            bulk_units = min(remaining_deficit, bulk_affordable_units)

            batches = [
                {
                    "batch_label": "Emergency Bridge Batch (Fastest Air)",
                    "supplier_id": fastest_opt["supplier_id"],
                    "supplier_name": fastest_opt["supplier_name"],
                    "freight_mode": fastest_opt["freight_mode"],
                    "units": emergency_bridge_units,
                    "lead_time_days": fastest_opt["lead_time_days"],
                    "unit_cost": fastest_opt["landed_unit_cost"],
                    "total_cost": round(emergency_bridge_units * fastest_opt["landed_unit_cost"], 2)
                }
            ]

            if bulk_units > 0:
                batches.append({
                    "batch_label": "Replenishment Balance Batch (Standard Sourcing)",
                    "supplier_id": cheapest_on_time_opt["supplier_id"],
                    "supplier_name": cheapest_on_time_opt["supplier_name"],
                    "freight_mode": cheapest_on_time_opt["freight_mode"],
                    "units": bulk_units,
                    "lead_time_days": cheapest_on_time_opt["lead_time_days"],
                    "unit_cost": cheapest_on_time_opt["landed_unit_cost"],
                    "total_cost": round(bulk_units * cheapest_on_time_opt["landed_unit_cost"], 2)
                })

        total_cost = round(sum(b["total_cost"] for b in batches), 2)
        max_lead_time = max(b["lead_time_days"] for b in batches)
        earliest_arrival = min(b["lead_time_days"] for b in batches)

        thought_log.append(
            f"Generated Plan ({selected_strategy}): Total Cost = ${total_cost:,.2f}, "
            f"First Batch Arrives: Day {earliest_arrival}, Final Batch: Day {max_lead_time}."
        )

        return {
            "agent": self.name,
            "strategy": selected_strategy,
            "attempt": attempt,
            "batches": batches,
            "total_units": unit_deficit,
            "total_cost": total_cost,
            "earliest_arrival_days": earliest_arrival,
            "final_arrival_days": max_lead_time,
            "deadline_day": deadline_day,
            "summary": f"Proposed '{selected_strategy}' plan procuring {unit_deficit} units across {len(batches)} batch(es) for ${total_cost:,.2f}.",
            "thought_log": thought_log
        }
