"""Stage 1: preprocess and audit one FraudZen scenario.

Outputs cleaned CDRs, malformed/schema/timestamp audit tables, and a labeled
canonical event table. No fraud score or model is created here.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


RAW_COLUMNS = [
    "timestamp", "cdr_type", "src_number", "src_imei",
    "initial_src_cell_id", "current_src_cell_id", "dst_number", "dst_imei",
    "initial_dst_cell_id", "current_dst_cell_id", "duration", "size",
]
OUTPUT_COLUMNS = RAW_COLUMNS + [
    "dataset", "record_id", "event_key", "src_known_fraud", "dst_known_fraud",
    "involves_known_fraud",
]


def parse_file(path: Path, dataset: str):
    parsed, malformed, variants, timestamp_failures = [], [], [], []
    with path.open(encoding="utf-8", errors="replace") as handle:
        header = handle.readline().strip().split()
        for line_number, raw in enumerate(handle, start=2):
            if not raw.strip():
                continue
            fields = raw.strip().split()
            if len(fields) not in (12, 13):
                malformed.append({"source_line": line_number, "field_count": len(fields), "raw_line": raw.rstrip("\n")})
                continue
            # Date and time are separate tokens although the header calls them one field.
            row = {
                "timestamp": f"{fields[0]} {fields[1]}",
                "cdr_type": fields[2],
                "src_number": fields[3].strip(),
                "src_imei": fields[4].strip(),
                "initial_src_cell_id": fields[5],
                "current_src_cell_id": fields[6],
                "dst_number": fields[7].strip(),
                "dst_imei": fields[8].strip(),
                "initial_dst_cell_id": fields[9],
                "current_dst_cell_id": fields[10],
                "duration": fields[11],
                "size": fields[12] if len(fields) == 13 else "",
                "dataset": dataset,
                "source_line": line_number,
            }
            if len(fields) == 12:
                variants.append({"source_line": line_number, "field_count": len(fields), "raw_line": raw.rstrip("\n")})
            try:
                parsed_timestamp = datetime.strptime(row["timestamp"], "%d-%m-%Y %H:%M:%S")
                row["timestamp"] = parsed_timestamp.isoformat(sep=" ")
            except ValueError:
                timestamp_failures.append({"source_line": line_number, "raw_timestamp": row["timestamp"], "raw_line": raw.rstrip("\n")})
                continue
            parsed.append(row)
    return parsed, malformed, variants, timestamp_failures, header


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fraud_users = {
        line.strip() for line in (args.scenario / "fraudulentUsers.txt").read_text(encoding="utf-8").splitlines() if line.strip()
    }
    all_rows, audit = [], {}
    for filename, dataset in (("International_CDRTrace.txt", "international"), ("Op_1_CDRTrace.txt", "local")):
        parsed, malformed, variants, failures, header = parse_file(args.scenario / filename, dataset)
        audit[dataset] = {
            "filename": filename, "header": " | ".join(header), "parsed": len(parsed),
            "malformed": len(malformed), "schema_variants": len(variants),
            "timestamp_failures": len(failures),
        }
        write_csv(args.output_dir / f"{dataset}_malformed_rows.csv", malformed, ["source_line", "field_count", "raw_line"])
        write_csv(args.output_dir / f"{dataset}_schema_variant_rows.csv", variants, ["source_line", "field_count", "raw_line"])
        write_csv(args.output_dir / f"{dataset}_timestamp_failures.csv", failures, ["source_line", "raw_timestamp", "raw_line"])
        all_rows.extend(parsed)

    # The international trace is repeated in the local trace. Keep the first copy.
    international_keys = {
        (r["timestamp"], r["src_number"], r["dst_number"], r["duration"])
        for r in all_rows if r["dataset"] == "international"
    }
    canonical, duplicate_rows = [], []
    seen = set()
    for row in all_rows:
        key = (row["timestamp"], row["src_number"], row["dst_number"], row["duration"])
        if row["dataset"] == "local" and key in international_keys:
            duplicate_rows.append({**row, "event_key": "|".join(key), "duplicate_reason": "cross_file_international_copy"})
            continue
        if key in seen:
            duplicate_rows.append({**row, "event_key": "|".join(key), "duplicate_reason": "repeated_canonical_event"})
            continue
        seen.add(key)
        row["event_key"] = "|".join(key)
        row["src_known_fraud"] = row["src_number"] in fraud_users
        row["dst_known_fraud"] = row["dst_number"] in fraud_users
        row["involves_known_fraud"] = row["src_known_fraud"] or row["dst_known_fraud"]
        canonical.append(row)

    for record_id, row in enumerate(canonical):
        row["record_id"] = record_id
    write_csv(args.output_dir / "canonical_cdr.csv", canonical, OUTPUT_COLUMNS)
    write_csv(args.output_dir / "excluded_duplicate_events.csv", duplicate_rows, OUTPUT_COLUMNS + ["duplicate_reason"])
    write_csv(args.output_dir / "fraudulent_users.csv", [{"src_number": x, "known_fraud": 1} for x in sorted(fraud_users)], ["src_number", "known_fraud"])

    with (args.output_dir / "preprocessing_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "filename", "header", "parsed", "malformed", "schema_variants", "timestamp_failures"])
        writer.writeheader()
        writer.writerows({"dataset": k, **v} for k, v in audit.items())
    with (args.output_dir / "preprocessing_manifest.txt").open("w", encoding="utf-8") as handle:
        handle.write(f"scenario={args.scenario}\n")
        handle.write(f"ground_truth_users={len(fraud_users)}\n")
        handle.write(f"parsed_events={len(all_rows)}\n")
        handle.write(f"canonical_events={len(canonical)}\n")
        handle.write(f"excluded_duplicates={len(duplicate_rows)}\n")
        handle.write(f"canonical_source_fraud_events={sum(r['src_known_fraud'] for r in canonical)}\n")
        handle.write(f"canonical_destination_fraud_events={sum(r['dst_known_fraud'] for r in canonical)}\n")
    print(f"parsed={len(all_rows)} canonical={len(canonical)} duplicates={len(duplicate_rows)} labels={len(fraud_users)}")


if __name__ == "__main__":
    main()
