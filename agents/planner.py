"""
Recovery Planning Agent: Formulates replenishment recovery strategies
(Speed-Priority, Cost-Optimized, and Split-Batch Sourcing).
Adapts dynamically when the Critic Agent provides rejection feedback.
Offers complete transparency into vendor selection, origin, and allocation rationale.
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
        attempt: int = 1,
        forced_strategy: str = None
    ) -> dict:
        options = supplier_info["options"]
        unit_deficit = demand_info["unit_deficit"]
        deadline_day = demand_info["deadline_day"]
        effective_demand = demand_info["effective_demand"]

        thought_log = [
            f"Evaluating sourcing options for SKU '{sku}' (Attempt #{attempt}).",
            f"Volume required: {unit_deficit} units | Stockout deadline: Day {deadline_day}."
        ]

        # Identify on-time viable options
        on_time_options = [o for o in options if o["meets_deadline"]]
        if not on_time_options:
            on_time_options = [min(options, key=lambda x: x["lead_time_days"])]

        fastest_opt = min(on_time_options, key=lambda x: x["lead_time_days"])
        cheapest_on_time_opt = min(on_time_options, key=lambda x: x["landed_unit_cost"])

        # Compute candidate strategies for transparent comparison
        # 1. Express Solo
        express_solo_cost = round(unit_deficit * fastest_opt["landed_unit_cost"], 2)
        # 2. Economy Standard
        economy_cost = round(unit_deficit * cheapest_on_time_opt["landed_unit_cost"], 2)

        # 3. Split Batch Calculation
        budget_cap = critic_feedback.get("budget_cap", 15000.0) if critic_feedback else 15000.0
        bridge_days = max(1, cheapest_on_time_opt["lead_time_days"] - fastest_opt["lead_time_days"] + 2)
        emergency_bridge_units = min(unit_deficit, math.ceil(bridge_days * effective_demand))
        remaining_deficit = unit_deficit - emergency_bridge_units

        express_cost = emergency_bridge_units * fastest_opt["landed_unit_cost"]
        remaining_budget = max(0.0, budget_cap - express_cost)
        bulk_affordable_units = math.floor(remaining_budget / cheapest_on_time_opt["landed_unit_cost"])
        bulk_units = min(remaining_deficit, bulk_affordable_units)
        split_batch_cost = round(express_cost + (bulk_units * cheapest_on_time_opt["landed_unit_cost"]), 2)

        candidate_strategies = [
            {
                "strategy_id": "EXPRESS_SOLO",
                "name": "Express Solo (Speed-First)",
                "supplier": f"{fastest_opt['supplier_name']} [{fastest_opt.get('location', 'Global')}]",
                "freight": fastest_opt["freight_mode"],
                "lead_time": f"{fastest_opt['lead_time_days']} day(s)",
                "units": unit_deficit,
                "total_cost": express_solo_cost,
                "description": f"100% of order ({unit_deficit} units) dispatched via fastest express air to eliminate stockout risk immediately."
            },
            {
                "strategy_id": "SPLIT_BATCH_BALANCED",
                "name": "Dual-Source Split-Batch (Balanced)",
                "supplier": f"{fastest_opt['supplier_name']} + {cheapest_on_time_opt['supplier_name']}",
                "freight": f"{fastest_opt['freight_mode']} (Bridge) + {cheapest_on_time_opt['freight_mode']} (Balance)",
                "lead_time": f"Day {fastest_opt['lead_time_days']} & Day {cheapest_on_time_opt['lead_time_days']}",
                "units": f"{emergency_bridge_units} (Air) + {bulk_units} (Std)",
                "total_cost": split_batch_cost,
                "description": f"Splits order: {emergency_bridge_units} units via Express Air to bridge stockout, and {bulk_units} units via Standard to compress budget."
            },
            {
                "strategy_id": "ECONOMY_SINGLE",
                "name": "Economy Standard (Cost-First)",
                "supplier": f"{cheapest_on_time_opt['supplier_name']} [{cheapest_on_time_opt.get('location', 'Global')}]",
                "freight": cheapest_on_time_opt["freight_mode"],
                "lead_time": f"{cheapest_on_time_opt['lead_time_days']} day(s)",
                "units": unit_deficit,
                "total_cost": economy_cost,
                "description": f"100% of order routed through the lowest-cost verified supplier that meets delivery deadline."
            }
        ]

        # Determine which strategy to formulate
        if forced_strategy:
            selected_strategy = forced_strategy
            thought_log.append(f"Operating under forced strategy directive: '{forced_strategy}'.")
        elif attempt == 1 and not critic_feedback:
            selected_strategy = "EXPRESS_SOLO"
            thought_log.append("Attempt #1 Strategy: Prioritize 100% risk elimination via fastest premium supplier.")
        else:
            selected_strategy = "SPLIT_BATCH_BALANCED"
            thought_log.append(f"Critic Rejection Acknowledged: '{critic_feedback.get('reason', '')}'.")
            thought_log.append(f"Adapting to Dual-Source Split-Batch with budget cap <= ${budget_cap:,.2f}.")

        # Build detailed allocation batches
        if selected_strategy == "EXPRESS_SOLO":
            batches = [
                {
                    "batch_label": "Primary Expedited Batch",
                    "supplier_id": fastest_opt["supplier_id"],
                    "supplier_name": fastest_opt["supplier_name"],
                    "location": fastest_opt.get("location", "Global"),
                    "freight_mode": fastest_opt["freight_mode"],
                    "units": unit_deficit,
                    "lead_time_days": fastest_opt["lead_time_days"],
                    "arrival_day": fastest_opt["lead_time_days"],
                    "unit_cost": fastest_opt["landed_unit_cost"],
                    "total_cost": round(unit_deficit * fastest_opt["landed_unit_cost"], 2),
                    "selection_rationale": (
                        f"Order accepted by {fastest_opt['supplier_name']} ({fastest_opt.get('location')}) via {fastest_opt['freight_mode']}. "
                        f"Guarantees delivery on Day {fastest_opt['lead_time_days']}, well before Day {deadline_day} stockout."
                    )
                }
            ]
        elif selected_strategy == "SPLIT_BATCH_BALANCED":
            batches = [
                {
                    "batch_label": "Emergency Bridge Batch (Fastest Air)",
                    "supplier_id": fastest_opt["supplier_id"],
                    "supplier_name": fastest_opt["supplier_name"],
                    "location": fastest_opt.get("location", "Global"),
                    "freight_mode": fastest_opt["freight_mode"],
                    "units": emergency_bridge_units,
                    "lead_time_days": fastest_opt["lead_time_days"],
                    "arrival_day": fastest_opt["lead_time_days"],
                    "unit_cost": fastest_opt["landed_unit_cost"],
                    "total_cost": round(emergency_bridge_units * fastest_opt["landed_unit_cost"], 2),
                    "selection_rationale": (
                        f"Emergency bridge order accepted by {fastest_opt['supplier_name']} ({fastest_opt.get('location')}). "
                        f"Rapid {fastest_opt['lead_time_days']}-day delivery prevents line shutdown on Day {deadline_day}."
                    )
                }
            ]
            if bulk_units > 0:
                batches.append({
                    "batch_label": "Replenishment Balance Batch (Standard Sourcing)",
                    "supplier_id": cheapest_on_time_opt["supplier_id"],
                    "supplier_name": cheapest_on_time_opt["supplier_name"],
                    "location": cheapest_on_time_opt.get("location", "Global"),
                    "freight_mode": cheapest_on_time_opt["freight_mode"],
                    "units": bulk_units,
                    "lead_time_days": cheapest_on_time_opt["lead_time_days"],
                    "arrival_day": cheapest_on_time_opt["lead_time_days"],
                    "unit_cost": cheapest_on_time_opt["landed_unit_cost"],
                    "total_cost": round(bulk_units * cheapest_on_time_opt["landed_unit_cost"], 2),
                    "selection_rationale": (
                        f"Balance replenishment accepted by {cheapest_on_time_opt['supplier_name']} ({cheapest_on_time_opt.get('location')}). "
                        f"Lower landed cost (${cheapest_on_time_opt['landed_unit_cost']}/unit) keeps total expenditure within budget."
                    )
                })
        else: # ECONOMY_SINGLE
            batches = [
                {
                    "batch_label": "Consolidated Economy Batch",
                    "supplier_id": cheapest_on_time_opt["supplier_id"],
                    "supplier_name": cheapest_on_time_opt["supplier_name"],
                    "location": cheapest_on_time_opt.get("location", "Global"),
                    "freight_mode": cheapest_on_time_opt["freight_mode"],
                    "units": unit_deficit,
                    "lead_time_days": cheapest_on_time_opt["lead_time_days"],
                    "arrival_day": cheapest_on_time_opt["lead_time_days"],
                    "unit_cost": cheapest_on_time_opt["landed_unit_cost"],
                    "total_cost": round(unit_deficit * cheapest_on_time_opt["landed_unit_cost"], 2),
                    "selection_rationale": (
                        f"Order accepted by {cheapest_on_time_opt['supplier_name']} ({cheapest_on_time_opt.get('location')}) via {cheapest_on_time_opt['freight_mode']} "
                        f"as lowest-cost on-time fulfillment."
                    )
                }
            ]

        total_cost = round(sum(b["total_cost"] for b in batches), 2)
        max_lead_time = max(b["lead_time_days"] for b in batches)
        earliest_arrival = min(b["lead_time_days"] for b in batches)
        total_procured_units = sum(b["units"] for b in batches)

        # Build comprehensive transparent summary
        batch_summaries = [
            f"{b['units']} units from '{b['supplier_name']}' [{b['location']}] via {b['freight_mode']} (${b['total_cost']:,.2f}, ETA: Day {b['arrival_day']})"
            for b in batches
        ]
        detailed_summary = (
            f"Strategy '{selected_strategy}' formulated: " + " | ".join(batch_summaries) +
            f" — Total: {total_procured_units} units for ${total_cost:,.2f}."
        )

        thought_log.append(
            f"Formulated {selected_strategy}: Total Cost = ${total_cost:,.2f} | Earliest Arrival: Day {earliest_arrival}."
        )

        return {
            "agent": self.name,
            "strategy": selected_strategy,
            "attempt": attempt,
            "batches": batches,
            "candidate_strategies": candidate_strategies,
            "total_units": total_procured_units,
            "total_cost": total_cost,
            "earliest_arrival_days": earliest_arrival,
            "final_arrival_days": max_lead_time,
            "deadline_day": deadline_day,
            "summary": detailed_summary,
            "thought_log": thought_log
        }
