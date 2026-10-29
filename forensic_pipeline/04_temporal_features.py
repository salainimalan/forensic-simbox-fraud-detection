import pandas as pd
from common import OUT, ensure_out

events = pd.read_csv(OUT / "01_preprocess" / "canonical_events.csv", parse_dates=["timestamp"])
src = events[["record_id", "src_number", "timestamp"]].rename(columns={"src_number": "sim"})
dst = events[["record_id", "dst_number", "timestamp"]].rename(columns={"dst_number": "sim"})
activity = pd.concat([src, dst]).drop_duplicates(["sim", "record_id"]).sort_values(["sim", "timestamp"])
activity["hour"] = activity.timestamp.dt.hour
activity["is_night"] = activity.hour.between(0, 5)
def calc(g):
    counts = g.hour.value_counts()
    gaps = g.timestamp.sort_values().diff().dt.total_seconds().dropna()
    return pd.Series({"active_days": g.timestamp.dt.date.nunique(), "active_hours": g.hour.nunique(), "activity_span_seconds": (g.timestamp.max()-g.timestamp.min()).total_seconds(), "hourly_concentration": counts.max()/len(g), "peak_hour": int(counts.idxmax()), "max_hourly_activity": int(counts.max()), "night_activity_count": int(g.is_night.sum()), "night_activity_ratio": g.is_night.mean(), "longest_inactivity_gap": gaps.max() if len(gaps) else pd.NA, "shortest_inactivity_gap": gaps.min() if len(gaps) else pd.NA})
features = activity.groupby("sim", group_keys=False).apply(calc, include_groups=False).reset_index()
fraud = set((OUT / "01_preprocess" / "fraudulent_users.txt").read_text().split())
features["known_fraud"] = features.sim.isin(fraud)
out = ensure_out("04_temporal_features")
features.to_csv(out / "temporal_features.csv", index=False)
features.groupby("known_fraud").median(numeric_only=True).T.to_csv(out / "median_comparison.csv")
activity.groupby("hour").size().reindex(range(24), fill_value=0).rename("activity_count").to_csv(out / "hourly_activity_distribution.csv")
print(f"temporal feature rows={len(features):,}")
