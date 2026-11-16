"""Session IV Lab Exercise - Inventory Management and Optimization (EOQ).

Static matplotlib version of the exercise, as specified on the slide:
  - EOQ is calculated using demand, ordering cost and holding cost.
  - Inventory levels are simulated monthly.
  - Each point is labeled with remaining units.
  - Grid and axis labels enhance readability.

Run:  python eoq_lab.py   (saves eoq_inventory_plot.png and shows the chart)
"""
import matplotlib.pyplot as plt

from eoq_model import calculate_eoq, cost_breakdown, simulate_inventory

# ---- Inputs ----
D = 1200   # Annual demand (units/year)
S = 50     # Ordering cost per order (AED)
H = 2      # Holding cost per unit per year (AED)

# ---- EOQ ----
eoq = calculate_eoq(D, S, H)
costs = cost_breakdown(eoq, D, S, H)
print(f"EOQ                  : {eoq:.0f} units")
print(f"Orders per year      : {D / eoq:.1f}")
print(f"Annual ordering cost : AED {costs['ordering']:.2f}")
print(f"Annual holding cost  : AED {costs['holding']:.2f}")
print(f"Total inventory cost : AED {costs['total']:.2f}")

# ---- Monthly simulation (reorder EOQ when stock can't cover next month) ----
result = simulate_inventory(D, S, H)
df = result.table
print("\n", df.to_string(index=False))

# ---- Visualization ----
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(df["Month"], df["Closing Stock"], marker="o", linewidth=2, color="#2563eb",
        label="Inventory level (end of month)")
for x, y in zip(df["Month"], df["Closing Stock"]):
    ax.annotate(f"{y}", (x, y), textcoords="offset points", xytext=(0, 9),
                ha="center", fontsize=9, fontweight="bold")
ax.axhline(result.reorder_point, color="#dc2626", linestyle="--", linewidth=1.2,
           label=f"Reorder point ({result.reorder_point} units)")
ax.set_title(f"Inventory Depletion over 12 Months (EOQ = {result.eoq} units)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Month")
ax.set_ylabel("Inventory Level (units)")
ax.grid(True, linestyle="--", alpha=0.5)
ax.margins(y=0.15)
ax.legend()
plt.tight_layout()
plt.savefig("eoq_inventory_plot.png", dpi=150)
plt.show()
