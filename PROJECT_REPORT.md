# Forensic SIMBox Fraud Detection Using Subscriber Behaviour and History-Aware CDR Analysis

## Academic details

Developed as part of the course on "Forensic Analytics" at Vellore Institute of Technology, Chennai.  
by Salai Nimalan and Aditya Rao B  
Subject Code: CSE4074  
Semester: Fall 2026-27  
Professor: Dr. S. Johanan Joysingh

**Authors:** Salai Nimalan and Aditya Rao B  
**Programme:** Integrated M.Tech. Computer Science and Business Analytics

## 1. Project objective

The objective is to investigate whether behavioral patterns in synthetic CDR data can identify SIMs associated with naive SIMBox fraud. The project treats detection as a forensic analytics problem: first establish evidence patterns, then build a model, then produce an investigation-priority score.

## 2. Dataset and scope

The primary experiment uses the FraudZen `all_naive_12%_200sims` scenario. The local trace contains 86,873 events, 3,851 SIMs/subscribers, and 200 labeled fraudulent SIMs, with 199 fraudulent SIMs observed in the local trace. The project uses the local CDR trace and fraud-label file; generated outputs are excluded from Git tracking because they can be recreated.

## 3. Forensic analysis

The analysis covers statistical activity, traffic direction, temporal spread, mobility, and social contacts. Known fraudulent SIMs have higher median total duration (209 versus 53 seconds), more unique contacts (3 versus 1), more active hours (3 versus 1), and more outgoing activity (3 versus 0). The median outgoing share is 1.0 for fraudulent SIMs and 0.0 for legitimate SIMs. Mobility differences are modest, while outgoing social degree and contact count provide clearer separation.

These are descriptive findings. They explain the evidence used by the model but are not treated as fraud decisions on their own.

## 4. Static versus history-aware modeling

A static table has one row per SIM for the whole day:

```text
SIM -> total events, total calls, total duration, contacts, active hours
```

A history-aware table has multiple rows per SIM, one row per hour:

```text
SIM + hour -> current behavior + previous-hour behavior + recent cumulative behavior
```

History-aware features include current event and call counts, outgoing and incoming activity, duration, contacts, cell count, previous-hour activity, previous-three-hour activity, cumulative activity, hour of day, elapsed hours, ratios, and activity change. Prior-window features use earlier activity only, which preserves causal ordering and avoids using future behavior.

## 5. Model comparison

The following values are held-out test results from the executed baseline comparison:

| Model | Feature view | PR-AUC | F1 | Precision | Recall |
|---|---|---:|---:|---:|---:|
| Logistic Regression | Static | 0.195 | 0.409 | 0.283 | 0.737 |
| Logistic Regression | History-aware | 0.836 | 0.794 | 0.803 | 0.785 |
| Random Forest | Static | 0.598 | 0.568 | 0.500 | 0.658 |
| Random Forest | History-aware | 0.933 | 0.804 | 0.907 | 0.722 |
| HistGradientBoosting | Static | 0.581 | 0.370 | 0.625 | 0.263 |
| HistGradientBoosting | History-aware | 0.918 | 0.801 | 0.977 | 0.679 |

History-aware modeling improves PR-AUC for all three directly comparable algorithms. Random Forest has the strongest PR-AUC. HistGradientBoosting has the strongest precision in the reported baseline comparison. A tuned HistGradientBoosting model is also retained as a strong advanced comparator.

## 6. Forensic risk scoring

Notebook 15 combines traffic, social, temporal, mobility, and adaptive-deviation evidence into a transparent SIM-level risk score. The score is intended to prioritize investigation and provide evidence context around model outputs.

The current top-k validation table reports no fraud found in its top-k outputs. This indicates that the ranking or validation join still requires correction. Consequently, the classifier metrics are the principal validated modeling result, while the risk score should be described as a prototype forensic prioritization layer.

## 7. Evaluation design

All model partitions are grouped by SIM. This prevents rows from the same subscriber appearing in both training and test sets. Thresholds are selected on validation data, and final metrics are calculated on held-out test data. PR-AUC is emphasized because fraudulent SIMs are the minority class.

## 8. Contribution

The project contributes a compact forensic workflow that combines evidence aggregation with history-aware supervised detection. Its main result is empirical: current and recent subscriber behavior provide substantially more useful information than a single static daily summary in the selected synthetic scenario.

## 9. Limitations and next work

The dataset is synthetic and covers one day. It does not establish multi-day persistence, live-operator generalization, or production calibration. Further work should use multi-day traces, repeated simulation seeds, independent scenario validation, calibrated probabilities, operator-reviewed labels, and a corrected top-k risk-ranking evaluation.

The research paper is intentionally not included in this repository at this stage.
