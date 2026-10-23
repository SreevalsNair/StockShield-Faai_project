"""
StockShield - Streamlit Proof-of-Concept Dashboard
Domain: Inventory and Supply-Chain Disruption Mitigation
Multi-Agent Agentic AI Architecture
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from orchestrator import StockShieldOrchestrator

# Set page layout and title
st.set_page_config(
    page_title="StockShield | Multi-Agent Supply Chain PoC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .approved-card {
        padding: 1.2rem;
        border-radius: 8px;
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .rejected-card {
        padding: 1.2rem;
        border-radius: 8px;
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .vendor-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        background-color: #E0F2FE;
        color: #0369A1;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Orchestrator
@st.cache_resource
def get_orchestrator():
    return StockShieldOrchestrator()

orchestrator = get_orchestrator()
items = orchestrator.get_items()
sku_options = {f"{item['sku']} - {item['name']}": item["sku"] for item in items}

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.markdown("## **StockShield Controls**")
    st.caption("Agentic AI Supply-Chain PoC (CA-3)")
    
    selected_label = st.selectbox("Select Critical SKU", list(sku_options.keys()))
    selected_sku = sku_options[selected_label]
    item_data = orchestrator.get_item_by_sku(selected_sku)

    st.markdown("---")
    st.markdown("### ⚠️ **Inject Disruption**")
    simulated_delay = st.slider(
        "Primary Supplier Delay (Days)",
        min_value=0,
        max_value=25,
        value=11,
        help="Simulate shipment delay from primary supplier"
    )

    demand_surge = st.slider(
        "Unexpected Demand Surge (%)",
        min_value=0,
        max_value=50,
        value=15,
        step=5,
        help="Simulate sudden sales or production surge"
    )

    st.markdown("---")
    st.markdown("### 💰 **Policy Constraints**")
    budget_cap = st.slider(
        "Max Contingency Budget Cap ($)",
        min_value=5000,
        max_value=25000,
        value=14500,
        step=500,
        help="Maximum allowable emergency expenditure enforced by Critic Agent"
    )

    st.markdown("---")
    st.markdown("### 🎯 **Replenishment Strategy Mode**")
    strategy_mode_selection = st.radio(
        "Select Operating Mode:",
        [
            "🤖 Auto (Closed-Loop Critic Cycle)",
            "⚖️ Dual-Source Split-Batch (Balanced)",
            "⚡ Express Solo (Speed-First)",
            "💰 Economy Standard (Cost-First)"
        ],
        index=0,
        help="Choose whether agents negotiate autonomously or simulate a specific strategy."
    )

    mode_map = {
        "🤖 Auto (Closed-Loop Critic Cycle)": "AUTO",
        "⚖️ Dual-Source Split-Batch (Balanced)": "SPLIT_BATCH_BALANCED",
        "⚡ Express Solo (Speed-First)": "EXPRESS_SOLO",
        "💰 Economy Standard (Cost-First)": "ECONOMY_SINGLE"
    }
    selected_mode = mode_map[strategy_mode_selection]

    run_sim = st.button("🚀 Run Multi-Agent Recovery", type="primary", use_container_width=True)

# ----------------- HEADER & STATUS -----------------
st.markdown('<div class="main-title">🛡️ StockShield: Multi-Agent Supply-Chain Defense</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Autonomous shortage detection, multi-tier sourcing transparency & Critic validation</div>',
    unsafe_allow_html=True
)

# Metric overview cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Stock Level", f"{item_data['current_stock']} units")
col2.metric("Daily Consumption", f"{item_data['daily_demand']} units/day")
col3.metric("Safety Stock Buffer", f"{item_data['safety_stock']} units")
col4.metric(
    "Primary Shipment ETA", 
    f"Day {item_data['incoming_po']['scheduled_arrival_days'] + simulated_delay}",
    delta=f"+{simulated_delay}d delay" if simulated_delay > 0 else "On schedule",
    delta_color="inverse"
)

st.markdown("---")

# ----------------- SIMULATION & AGENT FLOW -----------------
session_key = f"{selected_sku}_{simulated_delay}_{budget_cap}_{demand_surge}_{selected_mode}"

if run_sim or "sim_result" not in st.session_state or st.session_state.get("session_key") != session_key:
    with st.spinner("Multi-Agent Swarm coordinating recovery plan..."):
        sim_result = orchestrator.run_simulation(
            sku=selected_sku,
            delay_days=simulated_delay,
            budget_cap=budget_cap,
            demand_surge_pct=demand_surge,
            strategy_mode=selected_mode
        )
        st.session_state["sim_result"] = sim_result
        st.session_state["session_key"] = session_key
else:
    sim_result = st.session_state["sim_result"]

# ----------------- DASHBOARD LAYOUT -----------------
tab1, tab2, tab3 = st.tabs([
    "🤖 Multi-Agent Execution Trace", 
    "📈 Inventory Trajectory Chart", 
    "📦 Final Purchase Order & Vendor Details"
])

with tab1:
    st.markdown("### **Autonomous Agent Decision-Making Log**")
    st.caption("Inspect real-time reasoning, supplier selection transparency, and the Critic's rejection/approval gate:")

    for step in sim_result["trace"]:
        stage_name = step["stage"]
        agent_name = step["agent"]
        status = step["status"]
        summary = step["summary"]
        thought_log = step["thought_log"]
        step_data = step.get("data", {})

        # Color coding for status pills
        if "CRITICAL" in status or "REJECTED" in status:
            pill_color = "red"
        elif "SAFETY" in status or "PROPOSED" in status:
            pill_color = "orange"
        else:
            pill_color = "green"

        with st.expander(f"**{stage_name}** — Status: :{pill_color}[{status}]", expanded=True):
            st.markdown(f"**Action Summary:** {summary}")

            # Specific Rich Display for Supplier Research Agent
            if "Supplier Research" in stage_name and "options" in step_data:
                st.markdown("##### 🌐 Supplier Catalog Evaluation Matrix:")
                sup_df = pd.DataFrame(step_data["options"])
                if not sup_df.empty:
                    display_sup = sup_df[[
                        "supplier_name", "location", "freight_mode", 
                        "lead_time_days", "base_unit_cost", "freight_per_unit", 
                        "landed_unit_cost", "meets_deadline", "reliability"
                    ]].rename(columns={
                        "supplier_name": "Supplier",
                        "location": "Origin",
                        "freight_mode": "Logistics Mode",
                        "lead_time_days": "Lead Time (Days)",
                        "base_unit_cost": "Base Price ($)",
                        "freight_per_unit": "Freight ($)",
                        "landed_unit_cost": "Landed Unit Cost ($)",
                        "meets_deadline": "On-Time?",
                        "reliability": "Reliability"
                    })
                    display_sup["Reliability"] = display_sup["Reliability"].apply(lambda x: f"{x*100:.0f}%")
                    display_sup["On-Time?"] = display_sup["On-Time?"].apply(lambda x: "✅ Yes" if x else "❌ Exceeds Deadline")
                    st.dataframe(display_sup, use_container_width=True)

            # Specific Rich Display for Recovery Planning Agent
            if "Recovery Planning" in stage_name:
                # 1. Candidate Strategy Comparison
                if "candidate_strategies" in step_data:
                    st.markdown("##### 📊 Sourcing Strategy Comparison (Evaluated by Planner):")
                    strat_df = pd.DataFrame(step_data["candidate_strategies"])
                    display_strat = strat_df[[
                        "name", "supplier", "freight", "units", "lead_time", "total_cost"
                    ]].rename(columns={
                        "name": "Strategy",
                        "supplier": "Target Suppliers & Origin",
                        "freight": "Freight Route",
                        "units": "Allocation",
                        "lead_time": "Delivery Timeline",
                        "total_cost": "Est. Total Spend ($)"
                    })
                    display_strat["Est. Total Spend ($)"] = display_strat["Est. Total Spend ($)"].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(display_strat, use_container_width=True)

                # 2. Winning Order Breakdown with Origin & Rationale
                if "batches" in step_data:
                    st.markdown("##### 📍 Specific Orders Accepted by Suppliers:")
                    batch_df = pd.DataFrame(step_data["batches"])
                    display_b = batch_df[[
                        "batch_label", "supplier_name", "location", "freight_mode",
                        "units", "unit_cost", "total_cost", "arrival_day", "selection_rationale"
                    ]].rename(columns={
                        "batch_label": "Batch Purpose",
                        "supplier_name": "Accepting Supplier",
                        "location": "Country / Origin",
                        "freight_mode": "Logistics Tier",
                        "units": "Units Accepted",
                        "unit_cost": "Landed Unit Price ($)",
                        "total_cost": "Batch Total ($)",
                        "arrival_day": "Arrival Day",
                        "selection_rationale": "Why Supplier Was Awarded Order"
                    })
                    display_b["Batch Total ($)"] = display_b["Batch Total ($)"].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(display_b, use_container_width=True)

            # Specific Rich Display for Critic Agent
            if "Critic Agent" in stage_name:
                v_cols = st.columns(3)
                v_cols[0].metric(
                    "Budget Audit", 
                    f"${step_data.get('total_cost', 0):,.2f}", 
                    delta=f"Cap: ${step_data.get('budget_cap', 0):,.2f} ({'-' if step_data.get('cost_variance', 0) <= 0 else '+'}${abs(step_data.get('cost_variance', 0)):,.2f})",
                    delta_color="normal" if step_data.get("cost_variance", 0) <= 0 else "inverse"
                )
                v_cols[1].metric(
                    "Delivery SLA Audit", 
                    f"Day {step_data.get('earliest_arrival_days', 0)}", 
                    delta=f"Stockout: Day {step_data.get('deadline_day', 0)}",
                    delta_color="normal" if step_data.get("earliest_arrival_days", 999) <= step_data.get("deadline_day", 0) else "inverse"
                )
                v_cols[2].metric("Audit Verdict", step_data.get("decision", "PENDING"))

                if step_data.get("decision") == "REJECTED":
                    st.markdown(f"""
                    <div class="rejected-card">
                        <strong>❌ Rejection Directive Issued to Planner:</strong><br/>
                        {step_data.get('critique')}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("##### Agent Internal Chain-of-Thought:")
            for thought in thought_log:
                st.markdown(f"- `{thought}`")

    # Highlighting the Critic loop specifically
    if sim_result.get("iterations_count", 1) > 1:
        st.info(
            f"🔄 **Agentic Closed-Loop Demonstrated**: The Critic Agent rejected Attempt #1 due to budget constraints, "
            f"prompting the Recovery Planning Agent to dynamically rebalance into a Split-Batch Strategy in Attempt #2."
        )

with tab2:
    st.markdown("### **Inventory Depletion Trajectory: Unmitigated vs StockShield**")
    
    # Calculate projection timelines for visualization
    days_span = max(25, item_data['incoming_po']['scheduled_arrival_days'] + simulated_delay + 4)
    time_steps = list(range(days_span + 1))
    
    effective_demand = item_data['daily_demand'] * (1 + demand_surge / 100.0)
    current_inv = item_data['current_stock']
    safety = item_data['safety_stock']
    delayed_eta = item_data['incoming_po']['scheduled_arrival_days'] + simulated_delay
    po_units = item_data['incoming_po']['units']

    # Unmitigated curve (stock drops to 0 until delayed shipment arrives)
    unmitigated_curve = []
    stock = current_inv
    for t in time_steps:
        if t > 0:
            stock -= effective_demand
            if t == delayed_eta:
                stock += po_units
        unmitigated_curve.append(max(0, stock))

    # Mitigated curve with StockShield recovery plan
    mitigated_curve = []
    stock_mit = current_inv
    final_plan = sim_result.get("final_plan")
    recovery_deliveries = {}
    if final_plan:
        for batch in final_plan.get("batches", []):
            arr = batch["lead_time_days"]
            recovery_deliveries[arr] = recovery_deliveries.get(arr, 0) + batch["units"]

    for t in time_steps:
        if t > 0:
            stock_mit -= effective_demand
            if t in recovery_deliveries:
                stock_mit += recovery_deliveries[t]
            if t == delayed_eta:
                stock_mit += po_units
        mitigated_curve.append(stock_mit)

    fig = go.Figure()

    # Safety stock line
    fig.add_trace(go.Scatter(
        x=time_steps,
        y=[safety] * len(time_steps),
        mode='lines',
        name=f'Safety Buffer ({safety} units)',
        line=dict(color='orange', dash='dash', width=2)
    ))

    # Zero stock line
    fig.add_trace(go.Scatter(
        x=time_steps,
        y=[0] * len(time_steps),
        mode='lines',
        name='Stockout Threshold (0 units)',
        line=dict(color='red', dash='dot', width=2)
    ))

    # Unmitigated
    fig.add_trace(go.Scatter(
        x=time_steps,
        y=unmitigated_curve,
        mode='lines+markers',
        name='Without StockShield (Stockout Occurs)',
        line=dict(color='#DC2626', width=3)
    ))

    # Mitigated
    fig.add_trace(go.Scatter(
        x=time_steps,
        y=mitigated_curve,
        mode='lines+markers',
        name='With StockShield Agent Recovery (Continuous Operation)',
        line=dict(color='#10B981', width=3.5)
    ))

    fig.update_layout(
        title=f"Stock Depletion Timeline for {selected_sku} (Delay: +{simulated_delay}d, Surge: +{demand_surge}%)",
        xaxis_title="Timeline (Days from Today)",
        yaxis_title="Inventory Units on Hand",
        hovermode="x unified",
        template="plotly_white",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Green curve shows how StockShield's emergency split-batch arrival prevents stock from reaching zero.")

with tab3:
    st.markdown("### **Validated Purchase Order & Vendor Details**")
    
    final_plan = sim_result.get("final_plan")
    final_audit = sim_result.get("final_audit")

    if final_plan and final_audit:
        audit_card_class = "approved-card" if final_audit['decision'] == "APPROVED" else "rejected-card"
        st.markdown(f"""
        <div class="{audit_card_class}">
            <h4>Audit Status: {final_audit['decision']} by Critic Agent</h4>
            <p><strong>Selected Replenishment Strategy:</strong> {final_plan['strategy']}</p>
            <p><strong>Total Procurement Cost:</strong> ${final_plan['total_cost']:,.2f} 
            <em>(Budget Cap: ${final_audit['budget_cap']:,.2f} | Variance: ${final_audit['cost_variance']:,.2f})</em></p>
            <p><strong>Critic Audit Statement:</strong> {final_audit['critique']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### **Detailed Purchase Order Allocation:**")
        batch_df = pd.DataFrame(final_plan["batches"])
        
        display_df = batch_df[[
            "batch_label", "supplier_name", "location", "freight_mode", 
            "units", "lead_time_days", "unit_cost", "total_cost", "selection_rationale"
        ]].rename(columns={
            "batch_label": "Batch Purpose",
            "supplier_name": "Awarded Supplier",
            "location": "Origin",
            "freight_mode": "Logistics Mode",
            "units": "Units Ordered",
            "lead_time_days": "Lead Time (Days)",
            "unit_cost": "Landed Unit Cost ($)",
            "total_cost": "Total Batch Cost ($)",
            "selection_rationale": "Award Rationale"
        })

        st.dataframe(display_df, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Replenished Units", f"{final_plan['total_units']} units")
        with col_b:
            st.metric("Earliest Batch Arrival", f"Day {final_plan['earliest_arrival_days']} (Zero Downtime)")

        st.download_button(
            label="📥 Export Recovery PO (CSV)",
            data=display_df.to_csv(index=False),
            file_name=f"StockShield_PO_{selected_sku}.csv",
            mime="text/csv"
        )
    else:
        st.success("No emergency replenishment needed. Stock Runway covers standard arrival.")
