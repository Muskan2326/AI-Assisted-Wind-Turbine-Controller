
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

METRICS_FILE = RESULTS / "wind_turbine_pid_metrics.csv"
TIMESERIES_FILE = RESULTS / "wind_turbine_timeseries.csv"

# Provisional demonstration limits, not industry standards.
LIMITS = {
    "MaxDeviation_rad_s": 0.10,
    "Overshoot_pct": 10.0,
    "SteadyStateError_pct": 2.0,
}


def validate_metrics(row):
    checks = {}

    for metric, limit in LIMITS.items():
        value = row[metric]
        checks[metric] = (
            pd.notna(value)
            and np.isfinite(value)
            and value <= limit
        )

    overall = "PASS" if all(checks.values()) else "FAIL"
    return checks, overall


def main():
    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Missing MATLAB metrics: {METRICS_FILE}"
        )

    df = pd.read_csv(METRICS_FILE)

    required = ["Controller", *LIMITS.keys()]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required CSV columns: {missing}"
        )

    reports = []

    for _, row in df.iterrows():
        checks, overall = validate_metrics(row)

        print(f"\nController: {row['Controller']}")

        for metric, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {metric}: {status}")

        print(f"  Overall verdict: {overall}")

        report = {
            "Controller": row["Controller"],
            **{
                f"{metric}_status":
                    "PASS" if passed else "FAIL"
                for metric, passed in checks.items()
            },
            "Overall": overall,
        }

        reports.append(report)

    report_df = pd.DataFrame(reports)
    output_file = RESULTS / "wind_turbine_validation.csv"
    report_df.to_csv(output_file, index=False)

    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
