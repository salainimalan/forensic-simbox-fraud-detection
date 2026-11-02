# Forensic SIMBox Fraud Detection Using Subscriber Behaviour and History-Aware CDR Analysis

Developed as part of the course on "Forensic Analytics" at Vellore Institute of Technology, Chennai.  
by Salai Nimalan and Aditya Rao B  
Subject Code: CSE4074  
Semester: Fall 2026-27  
Professor: Dr. S. Johanan Joysingh

## Project overview

This project develops a forensic analytics pipeline for detecting naive SIMBox fraud from synthetic Call Detail Record (CDR) data. The pipeline combines descriptive forensic analysis, traffic and temporal evidence, mobility and social indicators, history-aware feature engineering, supervised machine learning, and SIM-level risk scoring.

The selected primary scenario is `all_naive_12%_200sims` from the FraudZen synthetic CDR dataset. The project predicts whether a SIM/subscriber is fraudulent. Hourly model scores are treated as behavioral evidence that can support SIM-level investigation prioritization.

## Main finding

History-aware features outperform static full-day SIM profiles for every tested model.

| Model | Static daily PR-AUC | History-aware PR-AUC | History-aware F1 | History-aware recall |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.195 | 0.836 | 0.794 | 0.785 |
| Random Forest | 0.598 | 0.933 | 0.804 | 0.722 |
| HistGradientBoosting | 0.581 | 0.918 | 0.801 | 0.679 |

The strongest primary result is the history-aware Random Forest, with test PR-AUC 0.933, precision 0.907, recall 0.722, and F1 0.804. Tuned HistGradientBoosting provides a competitive alternative with F1 0.812, precision 0.905, and recall 0.736 in the advanced comparison.

## Forensic findings

In the primary scenario, known fraudulent SIMs show higher median total duration, contact count, active hours, outgoing activity, and activity span. Fraudulent activity is dominated by outbound calling and contacts are more often reached from the fraudulent SIM than used for incoming activity. Mobility separation is weaker because most SIMs remain associated with few cells.

The history-aware table represents each SIM-hour with current activity and prior behavior, including previous-hour events, previous-three-hour events, cumulative activity, call counts, outgoing activity, contact counts, duration, and activity change. This preserves behavioral change that a single daily SIM profile cannot represent.

## Pipeline

1. Validate and preprocess the CDR trace and fraud labels.
2. Produce statistical, traffic, temporal, mobility, and social forensic summaries.
3. Aggregate evidence and document descriptive inferences.
4. Build static SIM-level and history-aware SIM-hour feature tables.
5. Train Logistic Regression, Random Forest, and HistGradientBoosting baselines.
6. Tune and compare the advanced history-aware model.
7. Produce forensic deviation analysis and SIM-level risk scores.
8. Evaluate with SIM-grouped train, validation, and test partitions to prevent subscriber leakage.

## Repository structure

```text
forensic_pipeline/       Reusable Python pipeline stages
notebooks/               Executed analysis and modeling notebooks
tools/                   Data parsing and feature-building utilities
Fraudzen-dataset/        Local raw dataset; excluded from Git tracking
outputs/                 Generated tables, plots, and model artifacts; excluded from Git tracking
PROJECT_REPORT.md        Detailed project explanation aligned with the presentation
```

## Running the project

Open the notebooks in order from notebook 1 through notebook 15. The main analysis, feature engineering, model training, evaluation, and risk-scoring work is contained in these notebooks. The notebooks expect the local FraudZen dataset and write generated artifacts under `outputs/`.

## Evaluation and limitations

Thresholds are selected using validation data, while final metrics are calculated on held-out SIMs. The data covers one synthetic calendar day, so long-term persistence cannot be evaluated. The results may contain simulator-specific behavioral patterns and require validation on multi-day and real operator data.

Notebook 15 produces a transparent evidence-based risk score for investigation prioritization. Its current top-k ranking validation requires further correction before the risk ranking is presented as a validated operational result. The machine-learning comparison and the forensic evidence analysis remain the primary project results.

The management publication is not included in this repository at this stage.

## Authors

**Salai Nimalan**  
Integrated M.Tech. Computer Science and Business Analytics  
**Aditya Rao B**  
Integrated M.Tech. Computer Science and Business Analytics
