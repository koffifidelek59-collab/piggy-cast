"""Figure 1 of the Niger memo, redrawn from the Climate Impact Explorer data export.

Input : HI-danger_NER_NER_area_annual.csv (CIE download, Niger, area-weighted, annual)
Output: latex/fig_heat.pdf (vector, for LaTeX) and latex/fig_heat.png (300 dpi, for Word)

Usage: python3 make_figure.py <cie_csv> <output_dir>
"""
import csv
import io
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]

# Times New Roman if available, otherwise its metric-compatible equivalent
names = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = "Times New Roman" if "Times New Roman" in names else "Liberation Serif"
plt.rcParams.update({"font.size": 10, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "pdf.fonttype": 42})

TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#dcdad5"
BLUE, GREEN = "#1d6fa5", "#5B8C1F"   # validated pair (CVD and contrast checks pass)

lines = open(SRC, encoding="utf-8-sig").read().splitlines()
start = next(i for i, line in enumerate(lines) if line.startswith("year"))
rows = list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
years = [float(r["year"]) for r in rows]


def series(sc, field):
    return [float(r[f"{sc} {field}"]) for r in rows]


def crossing(sc, level):
    """Year in which the scenario's global warming level first reaches `level` (linear interpolation)."""
    wl = series(sc, "warming level")
    for (y0, w0), (y1, w1) in zip(zip(years, wl), zip(years[1:], wl[1:])):
        if w0 < level <= w1:
            return y0 + (level - w0) / (w1 - w0) * (y1 - y0)
    return None


def value_at(sc, year):
    med = series(sc, "median")
    for (y0, v0), (y1, v1) in zip(zip(years, med), zip(years[1:], med[1:])):
        if y0 <= year <= y1:
            return v0 + (year - y0) / (y1 - y0) * (v1 - v0)
    return med[-1]


fig, ax = plt.subplots(figsize=(6.3, 2.9))   # 16 cm wide
ax.axvspan(2060, 2100, color="#f1f0ec", zorder=0, lw=0)
ax.text(2080, 133, "Indicative model results after 2060", ha="center", va="top", fontsize=8.5, color=MUTED)

for sc, color, label in (("h_cpol", BLUE, "Current policies"), ("o_2c", GREEN, "Below 2°C")):
    lo, hi, med = series(sc, "5th percentile"), series(sc, "95th percentile"), series(sc, "median")
    ax.fill_between(years, lo, hi, color=color, alpha=0.16, lw=0, zorder=1)
    ax.plot([y for y in years if y <= 2060], [m for y, m in zip(years, med) if y <= 2060],
            color=color, lw=2, zorder=3, solid_capstyle="round")
    ax.plot([y for y in years if y >= 2060], [m for y, m in zip(years, med) if y >= 2060],
            color=color, lw=2, ls=(0, (3, 2)), zorder=3)

# direct labels at the end of each curve (identity never relies on colour alone)
ax.text(2101.5, value_at("h_cpol", 2100), "Current policies\n91 days (2.9°C in 2100)",
        va="center", fontsize=9, color=TEXT)
ax.text(2101.5, value_at("o_2c", 2100), "Below 2°C\n42 days (1.6°C in 2100)",
        va="center", fontsize=9, color=TEXT)

# global warming levels reached along the current-policies pathway
for level, dy in ((1.5, 9), (2.0, 9), (2.5, 9)):
    yr = crossing("h_cpol", level)
    v = value_at("h_cpol", yr)
    ax.plot(yr, v, "o", ms=6, mfc="white", mec=BLUE, mew=1.6, zorder=4)
    ax.annotate(f"+{level:.1f}°C", (yr, v), xytext=(0, dy), textcoords="offset points",
                ha="center", va="bottom", fontsize=8.5, color=TEXT)

ax.plot(2020, value_at("h_cpol", 2020), "o", ms=4.5, color=TEXT, zorder=4)
ax.annotate("Today: 31 days", (2020, value_at("h_cpol", 2020)), xytext=(4, -13),
            textcoords="offset points", fontsize=8.5, color=TEXT)

ax.set_xlim(2015, 2100)
ax.set_ylim(15, 140)
ax.set_xticks(range(2020, 2101, 10))
ax.set_ylabel("Days per year with\nheat index above 40°C", color=TEXT)
ax.grid(axis="y", color=GRID, lw=0.5)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.tick_params(colors=TEXT, labelsize=9)
ax.spines["left"].set_color(MUTED)
ax.spines["bottom"].set_color(MUTED)

fig.subplots_adjust(left=0.105, right=0.77, top=0.97, bottom=0.11)
os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "fig_heat.pdf"))
fig.savefig(os.path.join(OUT, "fig_heat.png"), dpi=300)
print("crossings (current policies):", {lvl: round(crossing("h_cpol", lvl), 1) for lvl in (1.5, 2.0, 2.5)})
