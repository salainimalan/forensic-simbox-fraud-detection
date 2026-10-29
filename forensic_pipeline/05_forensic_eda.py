import pandas as pd
from common import OUT, ensure_out

out = ensure_out("05_forensic_eda")
tables = {}
for name in ["02_statistical_features/statistical_features.csv", "03_traffic_features/traffic_features.csv", "04_temporal_features/temporal_features.csv"]:
    frame = pd.read_csv(OUT / name)
    stage = name.split("/")[0]
    tables[stage] = frame
    frame.select_dtypes("number").corr(method="spearman").to_csv(out / f"{stage}_spearman_correlations.csv")
    frame.groupby("known_fraud").describe().to_csv(out / f"{stage}_group_statistics.csv")
summary = pd.DataFrame({"stage": list(tables), "rows": [len(x) for x in tables.values()], "columns": [len(x.columns) for x in tables.values()]})
summary.to_csv(out / "eda_stage_summary.csv", index=False)
print(summary.to_string(index=False))
