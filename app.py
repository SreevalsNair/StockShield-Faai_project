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
    .agent-card {
        padding: 1.1rem;
        border-radius: 8px;
        background-color: #F8FAFC;
        border-left: 5px solid #0284C7;
        margin-bottom: 1rem;
    }
    .approved-card {
        padding: 1.2rem;
        border-radius: 8px;
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        margin-top: 1rem;
    }
    .critic-rejection {
        padding: 0.9rem;
        border-radius: 6px;
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        margin: 0.6rem 0;
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

    run_sim = st.button("🚀 Run Multi-Agent Recovery", type="primary", use_container_width=True)

# ----------------- HEADER & STATUS -----------------
st.markdown('<div class="main-title">🛡️ StockShield: Multi-Agent Supply-Chain Defense</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Autonomous shortage detection, alternative sourcing, cost optimization & Critic validation</div>',
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
if run_sim or "sim_result" not in st.session_state or st.session_state.get("last_sku") != selected_sku:
    with st.spinner("Multi-Agent Swarm coordinating recovery plan..."):
        sim_result = orchestrator.run_simulation(
            sku=selected_sku,
            delay_days=simulated_delay,
            budget_cap=budget_cap,
            demand_surge_pct=demand_surge
        )
        st.session_state["sim_result"] = sim_result
        st.session_state["last_sku"] = selected_sku
else:
    sim_result = st.session_state["sim_result"]

# ----------------- DASHBOARD LAYOUT -----------------
tab1, tab2, tab3 = st.tabs(["🤖 Multi-Agent Execution Trace", "📈 Inventory Trajectory Chart", "📦 Final Purchase Order"])

with tab1:
    st.markdown("### **Autonomous Agent Decision-Making Log**")
    st.caption("Observe step-by-step reasoning, tool outputs, and the Critic's rejection-revision cycle:")

    for step in sim_result["trace"]:
        stage_name = step["stage"]
        agent_name = step["agent"]
        status = step["status"]
        summary = step["summary"]
        thought_log = step["thought_log"]

        # Color coding for status pills
        if "CRITICAL" in status or "REJECTED" in status:
            pill_color = "red"
        elif "SAFETY" in status or "PROPOSED" in status:
            pill_color = "orange"
        else:
            pill_color = "green"

        with st.expander(f"**{stage_name}** — Status: :{pill_color}[{status}]", expanded=True):
            st.markdown(f"**Action Summary:** {summary}")
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
    st.markdown("### **Validated Purchase Order & Recovery Strategy**")
    
    final_plan = sim_result.get("final_plan")
    final_audit = sim_result.get("final_audit")

    if final_plan and final_audit:
        st.markdown(f"""
        <div class="approved-card">
            <h4>✅ Status: {final_audit['decision']} by Critic Agent</h4>
            <p><strong>Selected Strategy:</strong> {final_plan['strategy']}</p>
            <p><strong>Total Procurement Cost:</strong> ${final_plan['total_cost']:,.2f} 
            <em>(Budget Cap: ${final_audit['budget_cap']:,.2f} | Remaining Buffer: ${final_audit['budget_cap'] - final_plan['total_cost']:,.2f})</em></p>
            <p><strong>Audit Statement:</strong> {final_audit['critique']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### **Allocated Replenishment Batches:**")
        batch_df = pd.DataFrame(final_plan["batches"])
        # Format for clean display
        display_df = batch_df[[
            "batch_label", "supplier_name", "freight_mode", 
            "units", "lead_time_days", "unit_cost", "total_cost"
        ]].rename(columns={
            "batch_label": "Batch Purpose",
            "supplier_name": "Supplier",
            "freight_mode": "Logistics Mode",
            "units": "Units",
            "lead_time_days": "Lead Time (Days)",
            "unit_cost": "Landed Unit Cost ($)",
            "total_cost": "Total Batch Cost ($)"
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
