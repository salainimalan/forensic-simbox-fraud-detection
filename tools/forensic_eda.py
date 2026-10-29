"""Forensic EDA for one FraudZen scenario.

Creates investigator-oriented user summaries, aggregate statistics, and plots.
The primary source is Op_1_CDRTrace.txt because it contains local subscriber
behavior and aligns with fraudulentUsers.txt.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def read_labels(path: Path) -> set[str]:
    return {x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()}


def parse_rows(path: Path):
    with path.open(encoding="utf-8", errors="replace") as handle:
        next(handle)
        for line in handle:
            tokens = line.split()
            if len(tokens) != 13:
                continue
            yield {
                "timestamp": datetime.strptime(" ".join(tokens[:2]), "%d-%m-%Y %H:%M:%S"),
                "cdr_type": tokens[2],
                "src_number": tokens[3],
                "src_imei": tokens[4],
                "src_cell": tokens[6],
                "dst_number": tokens[7],
                "duration": float(tokens[11]),
                "size": float(tokens[12]),
            }


def new_user():
    return {
        "events": 0, "calls": 0, "sms": 0, "data": 0, "international": 0,
        "short_calls": 0, "duration": 0.0, "size": 0.0,
        "destinations": set(), "imeis": set(), "cells": set(), "hours": set(),
        "types": Counter(), "first_seen": None, "last_seen": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fraud = read_labels(args.scenario / "fraudulentUsers.txt")
    users = defaultdict(new_user)
    hourly = defaultdict(lambda: {"fraud": 0, "legitimate": 0})
    event_types = {"fraud": Counter(), "legitimate": Counter()}
    total = 0

    for row in parse_rows(args.scenario / "Op_1_CDRTrace.txt"):
        total += 1
        label = "fraud" if row["src_number"] in fraud else "legitimate"
        u = users[row["src_number"]]
        u["events"] += 1
        u["types"][row["cdr_type"]] += 1
        u["calls"] += row["cdr_type"] in {"MOC", "MTC", "I-MOC", "I-MTC"}
        u["sms"] += row["cdr_type"] == "MO-SMS"
        u["data"] += row["cdr_type"] == "DATA"
        u["international"] += row["cdr_type"].startswith("I-")
        u["short_calls"] += row["cdr_type"] in {"MOC", "MTC", "I-MOC", "I-MTC"} and row["duration"] <= 10
        u["duration"] += row["duration"]
        u["size"] += row["size"]
        u["destinations"].add(row["dst_number"])
        u["imeis"].add(row["src_imei"])
        u["cells"].add(row["src_cell"])
        u["hours"].add(row["timestamp"].hour)
        u["first_seen"] = row["timestamp"] if u["first_seen"] is None else min(u["first_seen"], row["timestamp"])
        u["last_seen"] = row["timestamp"] if u["last_seen"] is None else max(u["last_seen"], row["timestamp"])
        hourly[row["timestamp"].hour][label] += 1
        event_types[label][row["cdr_type"]] += 1

    fields = ["src_number", "fraud", "events", "calls", "sms", "data", "international",
              "international_ratio", "short_calls", "short_call_ratio", "duration_total",
              "duration_mean", "size_total", "unique_destinations", "unique_imeis",
              "unique_cells", "active_hours", "first_seen", "last_seen"]
    with (args.output_dir / "subscriber_forensic_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for number, u in sorted(users.items()):
            writer.writerow({
                "src_number": number, "fraud": int(number in fraud), "events": u["events"],
                "calls": u["calls"], "sms": u["sms"], "data": u["data"],
                "international": u["international"], "international_ratio": u["international"] / u["events"],
                "short_calls": u["short_calls"], "short_call_ratio": u["short_calls"] / u["calls"] if u["calls"] else 0,
                "duration_total": u["duration"], "duration_mean": u["duration"] / u["calls"] if u["calls"] else 0,
                "size_total": u["size"], "unique_destinations": len(u["destinations"]),
                "unique_imeis": len(u["imeis"]), "unique_cells": len(u["cells"]),
                "active_hours": len(u["hours"]), "first_seen": u["first_seen"], "last_seen": u["last_seen"],
            })

    with (args.output_dir / "eda_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write(f"events={total}\nusers={len(users)}\nlabels={len(fraud)}\n")
        handle.write(f"observed_fraud_users={sum(number in fraud for number in users)}\n")
        for label in ("fraud", "legitimate"):
            handle.write(f"{label}_events={sum(event_types[label].values())}\n")
            handle.write(f"{label}_event_types={dict(event_types[label])}\n")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for plots") from exc

    summary = []
    for number, u in users.items():
        summary.append((int(number in fraud), u))
    labels = {0: "Legitimate", 1: "Fraudulent"}
    metrics = [("events", "Events per subscriber"), ("destinations", "Unique destinations"),
               ("cells", "Unique source cells"), ("hours", "Active hours")]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (key, title) in zip(axes.ravel(), metrics):
        for label in (0, 1):
            values = []
            for current, u in summary:
                if current != label:
                    continue
                values.append({"events": u["events"], "destinations": len(u["destinations"]),
                               "cells": len(u["cells"]), "hours": len(u["hours"])}[key])
            ax.hist(values, bins=25, alpha=0.65, label=labels[label])
        ax.set_title(title)
        ax.set_xlabel(title)
        ax.set_ylabel("Subscribers")
        ax.legend()
    fig.suptitle("Forensic comparison: subscriber behavior")
    fig.tight_layout()
    fig.savefig(args.output_dir / "subscriber_behavior_comparison.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5))
    hours = list(range(24))
    ax.plot(hours, [hourly[h]["legitimate"] for h in hours], marker="o", label="Legitimate events")
    ax.plot(hours, [hourly[h]["fraud"] for h in hours], marker="o", label="Fraudulent events")
    ax.set_title("Event timing by subscriber label")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("CDR events")
    ax.set_xticks(hours)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "hourly_event_timing.png", dpi=150)
    plt.close(fig)

    types = sorted(set(event_types["fraud"]) | set(event_types["legitimate"]))
    fig, ax = plt.subplots(figsize=(10, 5))
    x = list(range(len(types)))
    width = 0.38
    ax.bar([v - width / 2 for v in x], [event_types["legitimate"][t] for t in types], width, label="Legitimate")
    ax.bar([v + width / 2 for v in x], [event_types["fraud"][t] for t in types], width, label="Fraudulent")
    ax.set_title("Event-type composition by subscriber label")
    ax.set_xlabel("CDR type")
    ax.set_ylabel("Events")
    ax.set_xticks(x, types)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "event_type_comparison.png", dpi=150)
    plt.close(fig)

    print(f"events={total} users={len(users)} observed_fraud={sum(number in fraud for number in users)}")


if __name__ == "__main__":
    main()
