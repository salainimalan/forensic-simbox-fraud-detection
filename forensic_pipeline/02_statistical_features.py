import pandas as pd
from common import OUT, ensure_out

events = pd.read_csv(OUT / "01_preprocess" / "canonical_events.csv", parse_dates=["timestamp"])
src = events.rename(columns={"src_number": "sim", "dst_number": "contact", "current_src_cellId": "cell"})
dst = events.rename(columns={"dst_number": "sim", "src_number": "contact", "current_dst_cellId": "cell"})
endpoints = pd.concat([src[["record_id", "sim", "contact", "timestamp", "duration", "cell"]], dst[["record_id", "sim", "contact", "timestamp", "duration", "cell"]]])
endpoints = endpoints.drop_duplicates(["sim", "record_id"])
features = endpoints.groupby("sim").agg(activity_count=("record_id", "count"), total_duration=("duration", "sum"), average_duration=("duration", "mean"), median_duration=("duration", "median"), active_days=("timestamp", lambda x: x.dt.date.nunique()), active_hours=("timestamp", lambda x: x.dt.hour.nunique()), unique_contacts=("contact", "nunique"), unique_current_cells=("cell", "nunique")).reset_index()
fraud = set((OUT / "01_preprocess" / "fraudulent_users.txt").read_text().split())
features["known_fraud"] = features["sim"].isin(fraud)
out = ensure_out("02_statistical_features")
features.to_csv(out / "statistical_features.csv", index=False)
features.groupby("known_fraud").describe().to_csv(out / "descriptive_statistics.csv")
print(f"statistical feature rows={len(features):,}")
