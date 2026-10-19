"""
Supplier Research Agent: Scans supplier catalogs, discovers alternative vendors,
and calculates landed unit costs across multiple logistics tiers.
"""

class SupplierResearchAgent:
    def __init__(self):
        self.name = "Supplier Research Agent"
        self.role = "Market Sourcing, Alternate Vendor Discovery & Freight Analysis"

    def research(self, sku: str, suppliers_catalog: list, demand_info: dict) -> dict:
        deadline_day = demand_info["deadline_day"]
        options = []

        thought_log = [
            f"Querying supplier catalog for SKU: '{sku}'. Target delivery deadline: Day {deadline_day}."
        ]

        # Scan all suppliers
        for sup in suppliers_catalog:
            if sku not in sup.get("supported_skus", []):
                continue

            sup_id = sup["supplier_id"]
            sup_name = sup["name"]
            reliability = sup.get("reliability_score", 0.90)
            base_cost = sup.get("base_unit_cost", 20.0)

            thought_log.append(
                f"Evaluated Supplier '{sup_name}' ({sup_id}, Reliability: {reliability*100:.0f}%)."
            )

            # Evaluate each freight option
            for freight_mode, freight_data in sup.get("freight_options", {}).items():
                lead_days = freight_data["lead_time_days"]
                freight_per_unit = freight_data["freight_cost_per_unit"]
                total_unit_cost = round(base_cost + freight_per_unit, 2)
                meets_deadline = lead_days <= deadline_day

                option = {
                    "supplier_id": sup_id,
                    "supplier_name": sup_name,
                    "location": sup.get("location", "Unknown"),
                    "reliability": reliability,
                    "freight_mode": freight_mode,
                    "lead_time_days": lead_days,
                    "base_unit_cost": base_cost,
                    "freight_per_unit": freight_per_unit,
                    "landed_unit_cost": total_unit_cost,
                    "meets_deadline": meets_deadline
                }
                options.append(option)
                thought_log.append(
                    f"  -> Mode: {freight_mode} | Lead: {lead_days}d | Cost/unit: ${total_unit_cost} | On-Time: {meets_deadline}"
                )

        # Sort options: first by meets_deadline (descending), then by landed_unit_cost (ascending)
        options.sort(key=lambda x: (not x["meets_deadline"], x["landed_unit_cost"]))

        fastest = min(options, key=lambda x: x["lead_time_days"]) if options else None
        cheapest_on_time = next((o for o in options if o["meets_deadline"]), None)

        summary = (
            f"Discovered {len(options)} sourcing & logistics combinations. "
            f"Fastest option: {fastest['lead_time_days']} days via {fastest['supplier_name']} ({fastest['freight_mode']})."
            if fastest else "No valid suppliers found."
        )

        return {
            "agent": self.name,
            "sku": sku,
            "total_options_evaluated": len(options),
            "options": options,
            "fastest_option": fastest,
            "cheapest_on_time_option": cheapest_on_time,
            "summary": summary,
            "thought_log": thought_log
        }
