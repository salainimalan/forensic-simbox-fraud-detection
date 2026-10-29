from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "Fraudzen-dataset" / "Fraudzen-dataset" / "FraudZen_Cdrs" / "all_naive" / "all_naive_12%_200sims"
OUT = ROOT / "outputs" / "forensic_pipeline"
RAW_COLUMNS = ["timestamp", "CDR_type", "src_number", "src_imei", "initial_src_cellId", "current_src_cellId", "dst_number", "dst_imei", "initial_dst_cellId", "current_dst_cellId", "duration", "size"]

def parse_raw(path: Path, dataset: str):
    rows, malformed, variants = [], [], []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines()[1:], 2):
        fields = line.split()
        if len(fields) == 13:
            values = fields
        elif len(fields) == 12:
            values = fields + [None]
            variants.append({"dataset": dataset, "line": line_number, "reason": "missing_size", "raw": line})
        else:
            malformed.append({"dataset": dataset, "line": line_number, "field_count": len(fields), "raw": line})
            continue
        rows.append([f"{values[0]} {values[1]}", *values[2:], dataset, line_number])
    frame = pd.DataFrame(rows, columns=RAW_COLUMNS + ["dataset", "source_line"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%d-%m-%Y %H:%M:%S", errors="coerce")
    for col in ["duration", "size", "initial_src_cellId", "current_src_cellId", "initial_dst_cellId", "current_dst_cellId"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame, pd.DataFrame(malformed), pd.DataFrame(variants)

def load_events():
    local, lm, lv = parse_raw(SCENARIO / "Op_1_CDRTrace.txt", "local")
    international, im, iv = parse_raw(SCENARIO / "International_CDRTrace.txt", "international")
    all_events = pd.concat([local, international], ignore_index=True)
    key_cols = ["timestamp", "src_number", "dst_number", "duration"]
    keys = international[key_cols].astype("string").agg("|".join, axis=1)
    duplicate_local = all_events["dataset"].eq("local") & all_events[key_cols].astype("string").agg("|".join, axis=1).isin(set(keys))
    all_events = all_events.loc[~duplicate_local].copy()
    all_events["record_id"] = range(len(all_events))
    fraud = {x.strip() for x in (SCENARIO / "fraudulentUsers.txt").read_text().splitlines() if x.strip()}
    all_events["src_known_fraud"] = all_events["src_number"].isin(fraud)
    all_events["dst_known_fraud"] = all_events["dst_number"].isin(fraud)
    all_events["involves_known_fraud"] = all_events["src_known_fraud"] | all_events["dst_known_fraud"]
    return all_events, pd.concat([lm, im], ignore_index=True), pd.concat([lv, iv], ignore_index=True), fraud, int(duplicate_local.sum())

def ensure_out(name):
    path = OUT / name
    path.mkdir(parents=True, exist_ok=True)
    return path
