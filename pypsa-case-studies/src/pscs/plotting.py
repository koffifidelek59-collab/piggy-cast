"""One chart style for every figure (report, slides, notebooks).

Colours follow a validated colour-blind-safe categorical order (blue, orange,
aqua, yellow, magenta, green, violet, red) assigned in fixed order. Status
colours are reserved for limits and violations and always come with a label.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
# one colour per entity, used identically in every chart of the project
ENTITY = {"demand": "#2a78d6", "thermal": "#eb6834", "import": "#6250d6", "solar": "#eda100",
          "battery": "#1baf7a", "diesel": "#eb6834", "curtailed": "#c3c2b7"}
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def use_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "axes.prop_cycle": mpl.cycler(color=SERIES),
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "lines.linewidth": 2.0, "lines.markersize": 6,
        "legend.frameon": False, "legend.fontsize": 9,
    })


def limit_line(ax, y, label, color=CRITICAL, axis="y"):
    """Draw a labelled operating limit (dashed) on an axis."""
    if axis == "y":
        ax.axhline(y, color=color, lw=1.2, ls="--", zorder=1)
        ax.annotate(label, xy=(1, y), xycoords=("axes fraction", "data"), xytext=(-4, 3),
                    textcoords="offset points", ha="right", va="bottom", fontsize=8.5, color=INK2)
    else:
        ax.axvline(y, color=color, lw=1.2, ls="--", zorder=1)
        ax.annotate(label, xy=(y, 1), xycoords=("data", "axes fraction"), xytext=(3, -4),
                    textcoords="offset points", ha="left", va="top", fontsize=8.5, color=INK2)


def save(fig, path):
    fig.savefig(path)
    plt.close(fig)
