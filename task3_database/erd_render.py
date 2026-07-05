"""Render erd_diagram.png for the report (no external diagram tools needed).

Draws the star schema (regions, datetime_dim -> energy_readings) with matplotlib.

Usage:
    python erd_render.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent / "erd_diagram.png"

TABLES = {
    "regions": {
        "xy": (0.5, 5.2),
        "pk": "region_id (PK)",
        "cols": ["region_code (UQ)", "region_name", "description"],
        "color": "#4C78A8",
    },
    "datetime_dim": {
        "xy": (0.5, 0.6),
        "pk": "datetime_id (PK)",
        "cols": ["full_datetime (UQ)", "hour", "day", "month",
                 "year", "day_of_week", "is_weekend"],
        "color": "#4C78A8",
    },
    "energy_readings": {
        "xy": (6.0, 2.8),
        "pk": "reading_id (PK)",
        "cols": ["datetime_id (FK)", "region_id (FK)",
                 "consumption_mw", "created_at"],
        "color": "#E45756",
    },
}

ROW_H = 0.42
BOX_W = 3.1


def draw_table(ax, name, spec):
    x, y = spec["xy"]
    rows = [spec["pk"]] + spec["cols"]
    height = ROW_H * (len(rows) + 1)

    ax.add_patch(FancyBboxPatch(
        (x, y), BOX_W, height, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.5, edgecolor="#333", facecolor="white", zorder=2))
    # title bar
    ax.add_patch(FancyBboxPatch(
        (x, y + height - ROW_H), BOX_W, ROW_H,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=0, facecolor=spec["color"], zorder=3))
    ax.text(x + BOX_W / 2, y + height - ROW_H / 2, name,
            ha="center", va="center", color="white", fontsize=11,
            fontweight="bold", zorder=4)
    for i, row in enumerate(rows):
        ry = y + height - ROW_H * (i + 2) + ROW_H / 2
        weight = "bold" if i == 0 else "normal"
        ax.text(x + 0.15, ry, row, ha="left", va="center",
                fontsize=9, fontweight=weight, zorder=4)
    return {"right": (x + BOX_W, y + height / 2), "left": (x, y + height / 2)}


def connect(ax, p_from, p_to):
    ax.add_patch(FancyArrowPatch(
        p_from, p_to, arrowstyle="-|>", mutation_scale=16,
        linewidth=1.6, color="#555", zorder=1,
        connectionstyle="arc3,rad=0.05"))


def main():
    fig, ax = plt.subplots(figsize=(11, 7))
    anchors = {name: draw_table(ax, name, spec) for name, spec in TABLES.items()}

    connect(ax, anchors["regions"]["right"], anchors["energy_readings"]["left"])
    connect(ax, anchors["datetime_dim"]["right"], anchors["energy_readings"]["left"])

    ax.text(4.7, 5.1, "1 : N", fontsize=9, color="#555")
    ax.text(4.7, 2.0, "1 : N", fontsize=9, color="#555")

    ax.set_title("PJME Energy — Relational ERD (Star Schema)",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
