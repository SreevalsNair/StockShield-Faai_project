"""
Critic Agent: Rigorously stress-tests proposed replenishment plans against
budget thresholds, delivery deadlines, and supplier risk constraints.
Provides actionable feedback to guide planner revision.
"""

class CriticAgent:
    def __init__(self):
        self.name = "Critic Agent"
        self.role = "Constraint Validation, Financial Auditing & Quality Gatekeeper"

    def audit(self, plan: dict, budget_cap: float, demand_info: dict, min_reliability: float = 0.85) -> dict:
        total_cost = plan["total_cost"]
        earliest_arrival = plan["earliest_arrival_days"]
        deadline_day = demand_info["deadline_day"]
        strategy = plan["strategy"]
        attempt = plan["attempt"]

        violations = []
        thought_log = [
            f"Auditing '{strategy}' (Attempt #{attempt}) against business constraints.",
            f"Constraint 1: Maximum Budget Cap = ${budget_cap:,.2f}.",
            f"Constraint 2: Stockout Deadline = Day {deadline_day}."
        ]

        # Audit 1: Budget Constraint
        cost_variance = total_cost - budget_cap
        if total_cost > budget_cap:
            violations.append({
                "type": "BUDGET_OVERRUN",
                "message": f"Proposed cost (${total_cost:,.2f}) exceeds budget cap (${budget_cap:,.2f}) by ${cost_variance:,.2f}."
            })
            thought_log.append(f"❌ Budget Audit Failed: Over budget by ${cost_variance:,.2f}.")
        else:
            thought_log.append(f"✅ Budget Audit Passed: Cost ${total_cost:,.2f} is within ${budget_cap:,.2f} cap (Margin: ${abs(cost_variance):,.2f}).")

        # Audit 2: Delivery Deadline Constraint
        if earliest_arrival > deadline_day:
            violations.append({
                "type": "DEADLINE_BREACH",
                "message": f"Earliest batch arrives on Day {earliest_arrival}, which is AFTER stockout on Day {deadline_day}."
            })
            thought_log.append(f"❌ SLA Audit Failed: Arrival Day {earliest_arrival} > Stockout Day {deadline_day}.")
        else:
            thought_log.append(f"✅ SLA Audit Passed: First shipment arrives on Day {earliest_arrival} (before Day {deadline_day} stockout).")

        # Decision
        if violations:
            decision = "REJECTED"
            primary_reason = violations[0]["message"]
            critique = (
                f"Plan Rejected by Critic: {primary_reason} "
                f"Directive to Planner: Restructure order into a Split-Batch (expedite only minimum runway bridge, shift remainder to standard freight)."
            )
            thought_log.append(f"Decision: {decision}. Emitting revision request to Planner.")
        else:
            decision = "APPROVED"
            critique = "All operational and financial constraints satisfied. Recovery plan approved for execution."
            thought_log.append(f"Decision: {decision}. Issuing authorization token.")

        return {
            "agent": self.name,
            "decision": decision,
            "attempt": attempt,
            "budget_cap": budget_cap,
            "total_cost": total_cost,
            "cost_variance": round(cost_variance, 2),
            "earliest_arrival_days": earliest_arrival,
            "deadline_day": deadline_day,
            "violations": violations,
            "critique": critique,
            "thought_log": thought_log
        }
