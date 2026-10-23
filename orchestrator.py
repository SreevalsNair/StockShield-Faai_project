"""
StockShield Multi-Agent Orchestrator
Coordinates information flow between Monitoring, Demand, Supplier, Planner, and Critic agents.
Manages the iterative critique and adaptive replanning cycle.
"""
import json
import os
from agents.monitoring import MonitoringAgent
from agents.demand import DemandAnalysisAgent
from agents.supplier import SupplierResearchAgent
from agents.planner import RecoveryPlanningAgent
from agents.critic import CriticAgent

class StockShieldOrchestrator:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.inventory_path = os.path.join(data_dir, "inventory.json")
        self.suppliers_path = os.path.join(data_dir, "suppliers.json")
        
        self.inventory_data = self._load_json(self.inventory_path).get("items", [])
        self.suppliers_data = self._load_json(self.suppliers_path).get("suppliers", [])
        
        # Instantiate the 5 domain agents
        self.monitoring_agent = MonitoringAgent()
        self.demand_agent = DemandAnalysisAgent()
        self.supplier_agent = SupplierResearchAgent()
        self.planner_agent = RecoveryPlanningAgent()
        self.critic_agent = CriticAgent()

    def _load_json(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_items(self) -> list:
        return self.inventory_data

    def get_item_by_sku(self, sku: str) -> dict:
        for item in self.inventory_data:
            if item["sku"] == sku:
                return item
        return self.inventory_data[0]

    def run_simulation(
        self,
        sku: str,
        delay_days: int,
        budget_cap: float,
        demand_surge_pct: float = 0.0,
        max_critic_iterations: int = 3,
        strategy_mode: str = "AUTO"
    ) -> dict:
        """
        Executes the end-to-end multi-agent recovery workflow.
        """
        item = self.get_item_by_sku(sku)
        trace = []

        # Step 1: Monitoring Agent
        mon_result = self.monitoring_agent.assess(item, simulated_delay_days=delay_days)
        trace.append({
            "stage": "1. Monitoring Agent",
            "agent": mon_result["agent"],
            "status": mon_result["status"],
            "summary": mon_result["summary"],
            "thought_log": mon_result["thought_log"],
            "data": mon_result
        })

        if not mon_result["disruption_flagged"]:
            return {
                "disruption_handled": False,
                "message": "No disruption requiring recovery. Stock runway is sufficient.",
                "trace": trace,
                "final_plan": None
            }

        # Step 2: Demand Analysis Agent
        demand_result = self.demand_agent.analyze(item, mon_result, demand_surge_pct=demand_surge_pct)
        trace.append({
            "stage": "2. Demand Analysis Agent",
            "agent": demand_result["agent"],
            "status": "COMPLETED",
            "summary": demand_result["summary"],
            "thought_log": demand_result["thought_log"],
            "data": demand_result
        })

        # Step 3: Supplier Research Agent
        supplier_result = self.supplier_agent.research(sku, self.suppliers_data, demand_result)
        trace.append({
            "stage": "3. Supplier Research Agent",
            "agent": supplier_result["agent"],
            "status": "COMPLETED",
            "summary": supplier_result["summary"],
            "thought_log": supplier_result["thought_log"],
            "data": supplier_result
        })

        # Step 4 & 5: Iterative Planner <-> Critic Loop
        critic_feedback = None
        final_plan = None
        final_audit = None
        iteration_history = []

        forced_strategy = None
        if strategy_mode != "AUTO":
            forced_strategy = strategy_mode

        for attempt in range(1, max_critic_iterations + 1):
            # Recovery Planning Agent crafts or adapts plan
            plan = self.planner_agent.formulate_plan(
                sku=sku,
                demand_info=demand_result,
                supplier_info=supplier_result,
                critic_feedback=critic_feedback,
                attempt=attempt,
                forced_strategy=forced_strategy
            )
            
            trace.append({
                "stage": f"4. Recovery Planning Agent (Attempt #{attempt})",
                "agent": plan["agent"],
                "status": f"PROPOSED ({plan['strategy']})",
                "summary": plan["summary"],
                "thought_log": plan["thought_log"],
                "data": plan
            })

            # Critic Agent validates constraints
            audit = self.critic_agent.audit(
                plan=plan,
                budget_cap=budget_cap,
                demand_info=demand_result
            )

            trace.append({
                "stage": f"5. Critic Agent (Audit #{attempt})",
                "agent": audit["agent"],
                "status": audit["decision"],
                "summary": audit["critique"],
                "thought_log": audit["thought_log"],
                "data": audit
            })

            iteration_history.append({"attempt": attempt, "plan": plan, "audit": audit})

            if audit["decision"] == "APPROVED" or forced_strategy is not None:
                final_plan = plan
                final_audit = audit
                break
            else:
                # Feedback loop: feed critique back to planner for next iteration
                critic_feedback = {
                    "reason": audit["violations"][0]["message"] if audit["violations"] else "Optimization required",
                    "budget_cap": budget_cap,
                    "target_strategy": "SPLIT_BATCH"
                }

        # If loop ended without approval, take the best constrained plan
        if not final_plan and iteration_history:
            final_plan = iteration_history[-1]["plan"]
            final_audit = iteration_history[-1]["audit"]

        return {
            "disruption_handled": True,
            "sku": sku,
            "item_name": item["name"],
            "simulated_delay_days": delay_days,
            "budget_cap": budget_cap,
            "strategy_mode": strategy_mode,
            "iterations_count": len(iteration_history),
            "trace": trace,
            "iteration_history": iteration_history,
            "final_plan": final_plan,
            "final_audit": final_audit,
            "monitoring_summary": mon_result,
            "demand_summary": demand_result,
            "supplier_summary": supplier_result
        }
