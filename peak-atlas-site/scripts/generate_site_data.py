#!/usr/bin/env python3

import csv
import glob
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = SITE_DIR / "site-data.js"
PATTERN = "01_BPR/c_daily_traffic_segment_single_*speedbasedpeak_5_RDP_v_speed-solely.csv"
MAP_POSITIONS = {
    "1203481": {"x": 44, "y": 74, "corridor": "North Coast"},
    "1203506": {"x": 49, "y": 61, "corridor": "Sacramento Valley"},
    "1205541": {"x": 57, "y": 49, "corridor": "Bay Area"},
    "1205572": {"x": 62, "y": 71, "corridor": "Los Angeles Basin"},
    "1205583": {"x": 66, "y": 78, "corridor": "Orange County"},
    "1212611": {"x": 54, "y": 65, "corridor": "Central Valley"},
    "1214006": {"x": 60, "y": 84, "corridor": "San Diego"},
}


def time_to_minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    if hour == 24:
        return 24 * 60
    return hour * 60 + minute


def minutes_to_label(total_minutes: int) -> str:
    total_minutes %= 24 * 60
    hour = total_minutes // 60
    minute = total_minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    return f"{hour_12}:{minute:02d} {suffix}"


def minutes_to_duration_label(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours and minutes:
        return f"{hours}h {minutes:02d}m"
    if hours:
        return f"{hours}h 00m"
    return f"{minutes}m"


def classify_story(am_coverage: float, pm_coverage: float, am_duration: int, pm_duration: int) -> tuple[str, str]:
    if pm_duration - am_duration >= 20:
        return "Longer PM peak", "PM-heavy pattern"
    if am_duration - pm_duration >= 20:
        return "Longer AM peak", "AM-heavy pattern"
    if abs(am_coverage - pm_coverage) >= 0.2:
        return "Uneven detection", "Coverage imbalance"
    return "Balanced peak pattern", "Stable dual peak"


def build_station_summary(path: str) -> dict:
    basename = os.path.basename(path)
    station_id = basename.split("_")[5]
    days = defaultdict(list)
    year = None

    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            year = row["year"]
            if row["period"] != "c":
                continue
            days[row["date"]].append(
                {
                    "start": time_to_minutes(row["start_time"]),
                    "duration": int(float(row["duration"])),
                }
            )

    daily_am = []
    daily_pm = []
    for segments in days.values():
        am_candidates = [segment for segment in segments if segment["start"] < 12 * 60]
        pm_candidates = [segment for segment in segments if segment["start"] >= 12 * 60]
        if am_candidates:
            daily_am.append(max(am_candidates, key=lambda segment: segment["duration"]))
        if pm_candidates:
            daily_pm.append(max(pm_candidates, key=lambda segment: segment["duration"]))

    if not daily_am and not daily_pm:
        raise ValueError(f"No detected peaks found in {path}")

    am_start = round(statistics.median(segment["start"] for segment in daily_am)) if daily_am else None
    am_duration = round(statistics.median(segment["duration"] for segment in daily_am)) if daily_am else None
    pm_start = round(statistics.median(segment["start"] for segment in daily_pm)) if daily_pm else None
    pm_duration = round(statistics.median(segment["duration"] for segment in daily_pm)) if daily_pm else None

    am_coverage = len(daily_am) / len(days) if daily_am else 0
    pm_coverage = len(daily_pm) / len(days) if daily_pm else 0
    trend, category = classify_story(am_coverage, pm_coverage, am_duration or 0, pm_duration or 0)

    return {
        "id": station_id,
        "name": f"VDS {station_id}",
        "trend": trend,
        "storyCategory": category,
        "summary": (
            f"Real-data summary built from {len(days)} detected day profiles in {year}. "
            f"AM coverage is {round(am_coverage * 100)}% and PM coverage is {round(pm_coverage * 100)}%."
        ),
        "dataSource": "Speed-based peak output",
        "map": MAP_POSITIONS.get(station_id, {"x": 50, "y": 50, "corridor": "California pilot"}),
        "years": {
            str(year): {
                "am": {
                    "start": minutes_to_label(am_start) if am_start is not None else "N/A",
                    "duration": minutes_to_duration_label(am_duration) if am_duration is not None else "N/A",
                    "startHour": round(am_start / 60, 2) if am_start is not None else 0,
                    "durationHour": round(am_duration / 60, 2) if am_duration is not None else 0,
                    "coverage": round(am_coverage * 100),
                },
                "pm": {
                    "start": minutes_to_label(pm_start) if pm_start is not None else "N/A",
                    "duration": minutes_to_duration_label(pm_duration) if pm_duration is not None else "N/A",
                    "startHour": round(pm_start / 60, 2) if pm_start is not None else 0,
                    "durationHour": round(pm_duration / 60, 2) if pm_duration is not None else 0,
                    "coverage": round(pm_coverage * 100),
                },
            }
        },
    }


def main() -> None:
    stations = [build_station_summary(str(path)) for path in sorted(ROOT.glob(PATTERN))]
    payload = {"generatedFrom": PATTERN, "stations": stations}
    js = "window.PEAK_ATLAS_DATA = " + json.dumps(payload, indent=2) + ";\n"
    OUTPUT_FILE.write_text(js)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
