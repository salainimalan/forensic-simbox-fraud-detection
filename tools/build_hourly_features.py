"""Build hourly subscriber features for the FraudZen naive scenario."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


EVENT_COLUMNS = [
    "date", "time", "cdr_type", "src_number", "src_imei",
    "initial_src_cell", "current_src_cell", "dst_number", "dst_imei",
    "initial_dst_cell", "current_dst_cell", "duration", "size",
]


def read_fraud_users(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def parse_event_file(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        next(handle, None)
        for line_number, line in enumerate(handle, start=2):
            tokens = line.strip().split()
            if not tokens:
                continue
            # International rows omit the final size field; preserve that as blank.
            if len(tokens) == 12:
                tokens.append("")
            if len(tokens) != 13:
                raise ValueError(f"{path.name}:{line_number}: expected 12 or 13 fields, got {len(tokens)}")
            row = dict(zip(EVENT_COLUMNS, tokens))
            row["timestamp"] = datetime.strptime(
                f"{row.pop('date')} {row.pop('time')}", "%d-%m-%Y %H:%M:%S"
            )
            row["duration"] = float(row["duration"])
            row["size"] = float(row["size"]) if row["size"] else 0.0
            yield row


def add_event(bucket: dict, row: dict) -> None:
    bucket["events"] += 1
    bucket["types"][row["cdr_type"]] += 1
    bucket["destinations"].add(row["dst_number"])
    bucket["imeis"].add(row["src_imei"])
    bucket["cells"].add(row["current_src_cell"])
    bucket["durations"].append(row["duration"])
    bucket["size"] += row["size"]
    bucket["short_calls"] += row["cdr_type"] in {"MOC", "MTC", "I-MOC", "I-MTC"} and row["duration"] <= 10
    bucket["international"] += row["cdr_type"].startswith("I-")
    bucket["calls"] += row["cdr_type"] in {"MOC", "MTC", "I-MOC", "I-MTC"}
    bucket["sms"] += row["cdr_type"] == "MO-SMS"
    bucket["data"] += row["cdr_type"] == "DATA"


def build_features(scenario: Path, output: Path, include_international: bool = False) -> tuple[int, int]:
    fraud = read_fraud_users(scenario / "fraudulentUsers.txt")
    hourly = defaultdict(lambda: defaultdict(lambda: {
        "events": 0, "calls": 0, "sms": 0, "data": 0, "international": 0,
        "short_calls": 0, "size": 0.0, "destinations": set(), "imeis": set(),
        "cells": set(), "durations": [], "types": defaultdict(int),
    }))
    total_events = 0
    filenames = ["Op_1_CDRTrace.txt"]
    if include_international:
        filenames.append("International_CDRTrace.txt")
    for filename in filenames:
        for row in parse_event_file(scenario / filename):
            key = (row["src_number"], row["timestamp"].replace(minute=0, second=0, microsecond=0))
            add_event(hourly[key[1]][key[0]], row)
            total_events += 1

    by_user = defaultdict(list)
    for hour, users in hourly.items():
        for user, bucket in users.items():
            by_user[user].append((hour, bucket))

    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "src_number", "hour", "fraud", "events", "calls", "sms", "data",
        "international", "international_ratio", "short_calls", "short_call_ratio",
        "unique_destinations", "unique_imeis", "unique_cells", "cell_changes",
        "duration_mean", "duration_max", "size_total", "events_prev_hour",
        "events_prev_3h", "events_prev_6h",
    ]
    rows_written = 0
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for user in sorted(by_user):
            history = {hour: bucket for hour, bucket in by_user[user]}
            for hour in sorted(history):
                bucket = history[hour]
                durations = bucket["durations"]
                def prior_events(hours: int) -> int:
                    return sum(history.get(hour - timedelta(hours=i), {"events": 0})["events"] for i in range(1, hours + 1))
                events = bucket["events"]
                writer.writerow({
                    "src_number": user, "hour": hour.isoformat(sep=" "), "fraud": int(user in fraud),
                    "events": events, "calls": bucket["calls"], "sms": bucket["sms"], "data": bucket["data"],
                    "international": bucket["international"], "international_ratio": bucket["international"] / events if events else 0.0,
                    "short_calls": bucket["short_calls"], "short_call_ratio": bucket["short_calls"] / bucket["calls"] if bucket["calls"] else 0.0,
                    "unique_destinations": len(bucket["destinations"]), "unique_imeis": len(bucket["imeis"]),
                    "unique_cells": len(bucket["cells"]), "cell_changes": max(0, len(bucket["cells"]) - 1),
                    "duration_mean": sum(durations) / len(durations) if durations else 0.0,
                    "duration_max": max(durations) if durations else 0.0, "size_total": bucket["size"],
                    "events_prev_hour": prior_events(1), "events_prev_3h": prior_events(3), "events_prev_6h": prior_events(6),
                })
                rows_written += 1
    return total_events, rows_written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-international", action="store_true")
    args = parser.parse_args()
    total, rows = build_features(args.scenario, args.output, args.include_international)
    print(f"events={total} feature_rows={rows} output={args.output}")


if __name__ == "__main__":
    main()
