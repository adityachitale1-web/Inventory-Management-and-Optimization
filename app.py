"""Streamlit dashboard - Inventory Management and Optimization (EOQ model).

AI in Operations | Session IV Lab Exercise
Run locally:  streamlit run app.py
"""
import plotly.graph_objects as go
import streamlit as st

from eoq_model import (calculate_eoq, cost_breakdown, cost_curve,
                       simulate_inventory)

st.set_page_config(page_title="EOQ Inventory Optimization", page_icon="📦", layout="wide")

# ---------------- Sidebar inputs ----------------
st.sidebar.header("📥 Model Inputs")
D = st.sidebar.number_input("Annual demand, D (units/year)", min_value=1, value=1200, step=100)
S = st.sidebar.number_input("Ordering cost, S (AED per order)", min_value=0.01, value=50.0, step=5.0)
H = st.sidebar.number_input("Holding cost, H (AED per unit/year)", min_value=0.01, value=2.0, step=0.5)

st.sidebar.header("⚙️ Simulation Settings")
lead_time = st.sidebar.selectbox("Lead time (months)", [0, 1, 2], index=0,
                                 help="0 = order arrives immediately")
safety_stock = st.sidebar.number_input("Safety stock (units)", min_value=0, value=0, step=10)
seasonality = st.sidebar.slider("Seasonality (%)", 0, 50, 0,
                                help="Amplitude of the seasonal swing, peaking in Q4")
variability = st.sidebar.slider("Random demand variability (%)", 0, 40, 0,
                                help="Std. dev. of monthly demand noise")
seed = st.sidebar.number_input("Random seed", min_value=0, value=42, step=1)

# ---------------- Calculations ----------------
eoq_exact = calculate_eoq(D, S, H)
costs = cost_breakdown(eoq_exact, D, S, H)
sim = simulate_inventory(D, S, H, lead_time_months=lead_time, safety_stock=safety_stock,
                         variability_pct=variability, seasonality_pct=seasonality, seed=seed)
df = sim.table

# ---------------- Header ----------------
st.title("📦 Inventory Management & Optimization")
st.caption("Retail inventory optimization using the Economic Order Quantity (EOQ) model · "
           "AI in Operations - Session IV Lab")
st.latex(r"EOQ = \sqrt{\frac{2DS}{H}}")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("EOQ", f"{eoq_exact:,.0f} units")
c2.metric("Orders / year", f"{D / eoq_exact:,.1f}")
c3.metric("Days between orders", f"{365 / (D / eoq_exact):,.0f}")
c4.metric("Total annual cost", f"AED {costs['total']:,.2f}")
c5.metric("Stockout units", f"{sim.stockout_units:,}",
          delta="None" if sim.stockout_units == 0 else "Review policy",
          delta_color="off" if sim.stockout_units == 0 else "inverse")

tab1, tab2, tab3, tab4 = st.tabs(["📉 Inventory Depletion", "💰 Cost Analysis",
                                  "📋 Monthly Table", "ℹ️ About"])

# ---------------- Tab 1: Inventory depletion ----------------
with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["Closing Stock"], mode="lines+markers+text",
        text=df["Closing Stock"], textposition="top center",
        line=dict(color="#2563eb", width=3), marker=dict(size=9),
        name="Closing stock", hovertemplate="%{x}: %{y} units<extra></extra>"))
    fig.add_trace(go.Bar(x=df["Month"], y=df["Demand"], name="Monthly demand",
                         marker_color="rgba(148,163,184,0.45)",
                         hovertemplate="%{x} demand: %{y} units<extra></extra>"))
    orders = df[df["Order Placed"] > 0]
    fig.add_trace(go.Scatter(
        x=orders["Month"], y=orders["Closing Stock"], mode="markers", name="Order placed",
        marker=dict(symbol="triangle-up", size=14, color="#16a34a"),
        hovertemplate="%{x}: order of " + str(sim.eoq) + " units placed<extra></extra>"))
    fig.add_hline(y=sim.reorder_point, line_dash="dash", line_color="#dc2626",
                  annotation_text=f"Reorder point: {sim.reorder_point}",
                  annotation_position="top left")
    if sim.safety_stock:
        fig.add_hline(y=sim.safety_stock, line_dash="dot", line_color="#f59e0b",
                      annotation_text=f"Safety stock: {sim.safety_stock}",
                      annotation_position="bottom left")
    fig.update_layout(title=f"Inventory Depletion over 12 Months (EOQ = {sim.eoq} units)",
                      xaxis_title="Month", yaxis_title="Inventory Level (units)",
                      height=480, hovermode="x unified", legend=dict(orientation="h", y=-0.2),
                      barmode="overlay")
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    st.plotly_chart(fig, width="stretch")

    st.info(
        f"**Insight:** Ordering **{sim.eoq} units** at a time means roughly "
        f"**{D / eoq_exact:.1f} orders a year**. The model placed **{sim.orders_placed} orders** "
        f"in the simulation, average stock was **{sim.avg_inventory:,.0f} units**, and "
        + ("there were **no stockouts**." if sim.stockout_units == 0
           else f"**{sim.stockout_units} units** of demand went unmet. "
                "Add safety stock or reduce lead time to fix this."))

# ---------------- Tab 2: Cost analysis ----------------
with tab2:
    cc = cost_curve(D, S, H)
    fig2 = go.Figure()
    for col, color in [("Ordering Cost", "#f59e0b"), ("Holding Cost", "#16a34a"),
                       ("Total Cost", "#2563eb")]:
        fig2.add_trace(go.Scatter(x=cc["Order Quantity"], y=cc[col], name=col,
                                  line=dict(color=color, width=3 if col == "Total Cost" else 2)))
    fig2.add_vline(x=eoq_exact, line_dash="dash", line_color="#dc2626",
                   annotation_text=f"EOQ ≈ {eoq_exact:.0f}")
    fig2.update_layout(title="Annual Cost vs Order Quantity",
                       xaxis_title="Order Quantity (units)", yaxis_title="Annual Cost (AED)",
                       height=450, hovermode="x unified", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig2, width="stretch")

    a, b, c = st.columns(3)
    a.metric("Annual ordering cost", f"AED {costs['ordering']:,.2f}")
    b.metric("Annual holding cost", f"AED {costs['holding']:,.2f}")
    c.metric("Total cost at EOQ", f"AED {costs['total']:,.2f}")
    st.caption("At the EOQ, ordering cost equals holding cost, which is the point where "
               "total cost is lowest.")

    st.subheader("What if we ordered a different quantity?")
    compare_q = st.slider("Alternative order quantity", 10, int(eoq_exact * 3),
                          int(eoq_exact * 1.5))
    alt = cost_breakdown(compare_q, D, S, H)
    st.write(f"Ordering **{compare_q} units** costs **AED {alt['total']:,.2f}/year**, which is "
             f"**AED {alt['total'] - costs['total']:,.2f} more** than ordering at the EOQ.")

# ---------------- Tab 3: Table ----------------
with tab3:
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button("⬇️ Download simulation (CSV)", df.to_csv(index=False),
                       "eoq_simulation.csv", "text/csv")

# ---------------- Tab 4: About ----------------
with tab4:
    st.markdown(f"""
**Use case:** Retail inventory optimization using the EOQ (Economic Order Quantity) model.

**Formula:** EOQ = √(2DS / H)
- **D** = annual demand (units per year): {D:,}
- **S** = setup or ordering cost (per purchase order): AED {S:,.2f}
- **H** = holding or carrying cost (per unit, per year): AED {H:,.2f}

**Simulation logic (monthly):**
1. Each month's demand is taken out of stock on hand.
2. If the inventory position (on hand + on order) falls to the reorder point or below, an order of EOQ units is placed.
3. The reorder point = average monthly demand × (lead time + 1) + safety stock.
4. Optional seasonality and random variability test how robust the EOQ policy is when demand is not flat.

**Key features:** EOQ from demand, ordering and holding cost · monthly inventory simulation ·
each point labelled with remaining units · gridlines and axis labels for readability ·
cost-trade-off curve · downloadable results.
""")
