# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

"""
The hottest day of the month, bent into a circle: hour becomes an angle, °C a
radius. A hand sweeps from midnight, pulling a moving dot around the dial.

Two outputs:
    out/ts-clock-hottest.png   the full 24-hour shape, still
    out/ts-clock-hottest.gif   the same shape, drawn hour by hour

Run it:
    uv run ts_clock_hottest.py
"""

import csv
import datetime as dt
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap, Normalize

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

BASELINE = 22.0            # °C, subtracted from every temperature
HOURS = 24
TURN = 360                 # degrees in a full turn
SUBSTEPS = 5               # extra frames per hour — the key to smooth motion
FPS = 25                   # playback speed
DOTS = True
LINE_WIDTH = 2.4
PAD = 0.20
DPI = 90                   # smaller GIF

PAPER = "#faf8f4"
INK = "#1d1d1b"
MARK = "#d6591d"           # moving dot, hand, and the trailing edge

# green -> yellow -> orange -> red -> dark red
COLOURS = LinearSegmentedColormap.from_list("ts-scale", [
    "#e8f5e9", "#c5e1a5", "#aed581", "#dce775",
    "#fff176", "#ffd54f", "#ffb74d", "#ff8a65",
    "#ef5350", "#c62828", "#8e0000",
])

HERE = Path(__file__).parent
DATA = HERE / "data" / "ts-chongqing-2026-08.csv"
OUT = HERE / "out"
PNG = OUT / "ts-clock-hottest.png"
GIF = OUT / "ts-clock-hottest.gif"

# ---------------------------------------------------------------------------
# Reading.
# ---------------------------------------------------------------------------


def load_month():
    rows = []
    with DATA.open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            when = dt.datetime.strptime(record["time"], "%Y-%m-%d %H:%M")
            rows.append((when, float(record["ts"])))
    return rows


def group_by_day(rows):
    buckets = {}
    for when, value in rows:
        buckets.setdefault(when.date(), [None] * 24)[when.hour] = value
    return [(day, buckets[day]) for day in sorted(buckets)]


def hottest_day(days):
    return max(days, key=lambda pair: max(pair[1]))


# ---------------------------------------------------------------------------
# The transformation.
# ---------------------------------------------------------------------------


def to_xy(hour, radius):
    """Polar to cartesian. Hour 0 at the top, clockwise. Accepts float hours."""
    angle = math.radians(90 - hour / HOURS * TURN)
    return (radius * math.cos(angle), radius * math.sin(angle))


# ---------------------------------------------------------------------------
# Background, drawn identically every frame.
# ---------------------------------------------------------------------------


def draw_background(axes, radii):
    lo, hi = min(radii), max(radii)
    mean = sum(radii) / len(radii)

    for hour in range(HOURS):
        inner = to_xy(hour, lo * 0.45)
        outer = to_xy(hour, hi * 1.06)
        axes.plot([inner[0], outer[0]], [inner[1], outer[1]],
                  color=INK, alpha=0.32 if hour % 6 == 0 else 0.10,
                  linewidth=0.9)
        if hour % 6 == 0:
            label = to_xy(hour, hi * 1.30)
            axes.text(label[0], label[1], f"{hour:02d}:00",
                      color=INK, alpha=0.7, fontsize=9,
                      ha="center", va="center")

    ring = [to_xy(hour, mean) for hour in range(HOURS + 1)]
    axes.plot([p[0] for p in ring], [p[1] for p in ring],
              color=INK, alpha=0.22, linewidth=0.9, linestyle="--")


# ---------------------------------------------------------------------------
# The still: whole 24-hour shape.
# ---------------------------------------------------------------------------


def draw_still(axes, temps, colour):
    radii = [t - BASELINE for t in temps]
    draw_background(axes, radii)

    points = [to_xy(h, radii[h]) for h in range(HOURS)]
    points.append(points[0])
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    axes.fill(xs, ys, color=colour, alpha=0.16)
    axes.plot(xs, ys, color=colour, linewidth=LINE_WIDTH)
    if DOTS:
        axes.plot(xs, ys, "o", color=colour, markersize=4)

    hot = radii.index(max(radii))
    top = to_xy(hot, max(radii))
    axes.plot(top[0], top[1], "o", color=INK, markersize=8, zorder=5)


# ---------------------------------------------------------------------------
# The sweep: trail grows from 00:00 to the moving tip, a hand ties tip to centre.
# ---------------------------------------------------------------------------


def draw_sweep(axes, temps, colour, t_now):
    """t_now is a continuous hour value in [0, 24)."""
    radii = [t - BASELINE for t in temps]
    draw_background(axes, radii)

    # the trail so far: one vertex per completed hour, plus a fractional tip
    full = int(t_now)
    trail = [to_xy(h, radii[h]) for h in range(full + 1)]

    h1 = full % HOURS
    h2 = (h1 + 1) % HOURS
    frac = t_now - full
    r_tip = radii[h1] + (radii[h2] - radii[h1]) * frac
    tip = to_xy(t_now, r_tip)
    trail.append(tip)

    xs = [p[0] for p in trail]
    ys = [p[1] for p in trail]
    axes.plot(xs, ys, color=colour, linewidth=LINE_WIDTH, zorder=3)

    # the hand: a straight line from the centre to the moving tip
    axes.plot([0, tip[0]], [0, tip[1]], color=MARK, linewidth=1.8,
              alpha=0.9, zorder=4)

    # a small hub at the centre
    axes.plot(0, 0, "o", color=INK, markersize=3.5, zorder=5)

    # the moving dot
    axes.plot(tip[0], tip[1], "o", color=MARK, markersize=11,
              zorder=5, markeredgecolor=PAPER, markeredgewidth=1.5)


# ---------------------------------------------------------------------------
# The two outputs.
# ---------------------------------------------------------------------------


def main():
    days = group_by_day(load_month())
    if not days:
        raise SystemExit(f"no data in {DATA}")

    day, temps = hottest_day(days)

    all_temps = [t for _, row in days for t in row]
    norm = Normalize(vmin=min(all_temps), vmax=max(all_temps))
    colour = COLOURS(norm(max(temps)))

    rad_max = max(temps) - BASELINE
    lim = rad_max * (1 + PAD) * 1.15

    title = (f"Chongqing — {day:%d %B %Y} (hottest day)\n"
             f"hour as angle, °C as radius (baseline {BASELINE:.0f} °C)")

    OUT.mkdir(exist_ok=True)

    # -- 1. the still --------------------------------------------------------
    figure, axes = plt.subplots(figsize=(5.5, 5.5), facecolor=PAPER)
    figure.subplots_adjust(left=0.06, right=0.94, top=0.86, bottom=0.06)
    axes.set_facecolor(PAPER)
    axes.set_aspect("equal")
    axes.axis("off")
    axes.set_xlim(-lim, lim)
    axes.set_ylim(-lim, lim)
    draw_still(axes, temps, colour)
    axes.set_title(title, color=INK, fontsize=11, pad=16)
    figure.savefig(PNG, dpi=150, facecolor=PAPER)
    print(f"wrote {PNG.relative_to(HERE)}")

    # -- 2. the animation ----------------------------------------------------
    figure2, axes2 = plt.subplots(figsize=(5.5, 5.5), facecolor=PAPER)
    figure2.subplots_adjust(left=0.06, right=0.94, top=0.86, bottom=0.06)

    def update(frame):
        axes2.clear()
        axes2.set_facecolor(PAPER)
        axes2.set_aspect("equal")
        axes2.axis("off")
        axes2.set_xlim(-lim, lim)
        axes2.set_ylim(-lim, lim)
        axes2.set_title(title, color=INK, fontsize=11, pad=16)
        draw_sweep(axes2, temps, colour, frame / SUBSTEPS)

    total_frames = HOURS * SUBSTEPS
    anim = FuncAnimation(figure2, update, frames=range(total_frames),
                         interval=1000 / FPS, repeat=True)

    anim.save(GIF, writer=PillowWriter(fps=FPS), dpi=DPI)
    print(f"wrote {GIF.relative_to(HERE)} — {total_frames} frames at {FPS} fps")
    print(f"\nhottest day: {day:%Y-%m-%d}, "
          f"peak {max(temps):.2f} °C at {temps.index(max(temps)):02d}:00 LST")
    plt.show()


if __name__ == "__main__":
    main()