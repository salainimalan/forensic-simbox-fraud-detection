# FraudZen forensic pipeline

Run from the project root:

```powershell
python forensic_pipeline\01_preprocess.py
python forensic_pipeline\02_statistical_features.py
python forensic_pipeline\03_traffic_features.py
python forensic_pipeline\04_temporal_features.py
python forensic_pipeline\05_forensic_eda.py
```

The pipeline targets `all_naive_12%_200sims` and keeps raw evidence, cleaned
events, feature tables, and forensic comparisons in separate output folders.
