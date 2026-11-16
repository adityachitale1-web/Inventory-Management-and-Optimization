"""Core EOQ (Economic Order Quantity) logic and a 12-month inventory simulation.

EOQ = sqrt(2 * D * S / H)
    D = annual demand (units/year)
    S = setup / ordering cost per order
    H = holding cost per unit per year
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def calculate_eoq(D: float, S: float, H: float) -> float:
    """Economic Order Quantity."""
    if D <= 0 or S <= 0 or H <= 0:
        raise ValueError("D, S and H must all be positive.")
    return math.sqrt(2 * D * S / H)


def cost_breakdown(Q: float, D: float, S: float, H: float) -> dict:
    """Annual ordering, holding and total cost for an order quantity Q."""
    ordering = (D / Q) * S
    holding = (Q / 2) * H
    return {"ordering": ordering, "holding": holding, "total": ordering + holding}


def cost_curve(D: float, S: float, H: float, points: int = 200) -> pd.DataFrame:
    """Ordering / holding / total cost across a range of order quantities."""
    eoq = calculate_eoq(D, S, H)
    q = np.linspace(max(1.0, eoq * 0.2), eoq * 3, points)
    return pd.DataFrame({
        "Order Quantity": q,
        "Ordering Cost": (D / q) * S,
        "Holding Cost": (q / 2) * H,
        "Total Cost": (D / q) * S + (q / 2) * H,
    })


def monthly_demand(D: float, variability_pct: float = 0.0,
                   seasonality_pct: float = 0.0, seed: int = 42) -> np.ndarray:
    """Monthly demand: D/12, optionally with seasonality and random noise.

    The series is rescaled so it still sums to the annual demand D.
    """
    base = np.full(12, D / 12.0)
    if seasonality_pct:
        # Sine wave peaking in Q4 (retail holiday season)
        season = 1 + (seasonality_pct / 100) * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, 12))
        base = base * season
    if variability_pct:
        rng = np.random.default_rng(seed)
        base = base * rng.normal(1.0, variability_pct / 100, 12)
    base = np.clip(base, 0, None)
    if base.sum() > 0:
        base = base * (D / base.sum())
    return np.round(base).astype(int)


@dataclass
class SimulationResult:
    table: pd.DataFrame
    eoq: int
    reorder_point: int
    safety_stock: int
    orders_placed: int
    stockout_units: int
    avg_inventory: float


def simulate_inventory(D: float, S: float, H: float,
                       initial_inventory: int | None = None,
                       lead_time_months: int = 0,
                       safety_stock: int = 0,
                       variability_pct: float = 0.0,
                       seasonality_pct: float = 0.0,
                       seed: int = 42) -> SimulationResult:
    """Simulate inventory month by month over 12 months using an EOQ policy.

    Policy (continuous review, checked at month end):
      * Demand for the month is consumed from stock on hand.
      * If inventory position (on hand + on order) <= reorder point,
        an order of EOQ units is placed.
      * The order arrives after `lead_time_months` (0 = arrives immediately).
    Reorder point = average monthly demand * (lead time + 1) + safety stock,
    i.e. enough stock to cover the next month plus the lead time.
    """
    eoq = int(round(calculate_eoq(D, S, H)))
    demand = monthly_demand(D, variability_pct, seasonality_pct, seed)
    avg_month = D / 12.0
    rop = int(round(avg_month * (lead_time_months + 1) + safety_stock))

    on_hand = eoq + safety_stock if initial_inventory is None else int(initial_inventory)
    pipeline: list[tuple[int, int]] = []  # (arrival month index, qty)
    rows, orders, stockouts = [], 0, 0

    for m in range(12):
        # Receive any orders due this month
        received = sum(q for (arr, q) in pipeline if arr == m)
        pipeline = [(arr, q) for (arr, q) in pipeline if arr != m]
        on_hand += received
        start = on_hand

        d = int(demand[m])
        shipped = min(d, on_hand)
        short = d - shipped
        stockouts += short
        on_hand -= shipped

        ordered = 0
        position = on_hand + sum(q for _, q in pipeline)
        if position <= rop:
            ordered = eoq
            orders += 1
            if lead_time_months == 0:
                on_hand += eoq
            else:
                pipeline.append((m + lead_time_months, eoq))

        rows.append({
            "Month": MONTHS[m],
            "Opening Stock": start,
            "Received": received,
            "Demand": d,
            "Stockout Units": short,
            "Order Placed": ordered,
            "Closing Stock": on_hand,
        })

    table = pd.DataFrame(rows)
    return SimulationResult(
        table=table,
        eoq=eoq,
        reorder_point=rop,
        safety_stock=int(safety_stock),
        orders_placed=orders,
        stockout_units=stockouts,
        avg_inventory=float((table["Opening Stock"] + table["Closing Stock"]).mean() / 2),
    )
