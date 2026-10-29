import pandas as pd
from common import OUT, ensure_out

events = pd.read_csv(OUT / "01_preprocess" / "canonical_events.csv", parse_dates=["timestamp"])
voice = {"MOC", "MTC", "I-MOC", "I-MTC"}
outgoing = {"MOC", "I-MOC", "MO-SMS"}
incoming = {"MTC", "I-MTC"}
events["is_voice"] = events.CDR_type.isin(voice)
events["is_outgoing"] = events.CDR_type.isin(outgoing)
events["is_incoming"] = events.CDR_type.isin(incoming)
events["is_international"] = events.CDR_type.str.startswith("I-")
src = events.rename(columns={"src_number": "sim", "dst_number": "contact"})
dst = events.rename(columns={"dst_number": "sim", "src_number": "contact"})
src["direction"] = "outgoing"; dst["direction"] = "incoming"
endpoints = pd.concat([src, dst], ignore_index=True).drop_duplicates(["sim", "record_id"])
features = endpoints.groupby("sim").agg(total_activity=("record_id", "count"), total_duration=("duration", "sum"), average_duration=("duration", "mean"), maximum_duration=("duration", "max"), minimum_duration=("duration", "min"), unique_contacts=("contact", "nunique"), international_activity=("is_international", "sum"), outgoing_activity=("is_outgoing", "sum"), incoming_activity=("is_incoming", "sum")).reset_index()
features["outgoing_to_incoming_ratio"] = features["outgoing_activity"].div(features["incoming_activity"].replace(0, pd.NA))
features["international_ratio"] = features["international_activity"] / features["total_activity"]
fraud = set((OUT / "01_preprocess" / "fraudulent_users.txt").read_text().split())
features["known_fraud"] = features.sim.isin(fraud)
out = ensure_out("03_traffic_features")
features.to_csv(out / "traffic_features.csv", index=False)
features.groupby("known_fraud").median(numeric_only=True).T.to_csv(out / "median_comparison.csv")
print(f"traffic feature rows={len(features):,}")
