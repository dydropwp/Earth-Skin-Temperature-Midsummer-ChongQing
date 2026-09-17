# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Parse the cached NASA POWER JSON into a tidy CSV.

Reads only from disk. Never touches the network. Run this after fetch.py
if you want to re-parse without re-fetching.

Run:
    uv run parse.py
"""

import csv
import datetime as dt
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# The same knobs as fetch.py, so the cache path matches.
# ---------------------------------------------------------------------------

LAT, LNG = 29.56, 106.55
START = "20260801"
END = "20260831"
PARAMETER = "TS"

HERE = Path(__file__).parent
CACHE = HERE / "__pycache__"
OUTPUT = HERE / "data" / "ts-chongqing-2026-08.csv"

CACHE_FILE = CACHE / f"ts-{LAT}-{LNG}-{START}-{END}.json"

# ---------------------------------------------------------------------------
# Parse.
# ---------------------------------------------------------------------------


def load_raw():
    """Read the raw JSON text from cache and return it as Python objects."""
    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"no cache file at {CACHE_FILE}\n"
            f"run:  uv run fetch.py"
        )
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def markers(data, parameter=PARAMETER):
    """Turn one Feature into a list of row dicts."""
    lng, lat, *_ = data["geometry"]["coordinates"]
    fill = data["header"]["fill_value"]
    series = data["properties"]["parameter"][parameter]

    rows = []
    for stamp, value in series.items():
        if value == fill:
            continue
        moment = dt.datetime.strptime(stamp, "%Y%m%d%H")
        rows.append({
            "time": moment.strftime("%Y-%m-%d %H:%M"),
            "point_id": f"{lat}_{lng}",
            "lng": round(lng, 5),
            "lat": round(lat, 5),
            "ts": float(value),
        })
    return rows


def main():
    data = load_raw()
    rows = markers(data)

    if not rows:
        print("no rows parsed — check the cache file")
        return

    rows.sort(key=lambda r: r["time"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"read   {CACHE_FILE.name}")
    print(f"wrote  {OUTPUT.name} — {len(rows)} rows")
    print(f"first  {rows[0]}")
    print(f"last   {rows[-1]}")


if __name__ == "__main__":
    main()