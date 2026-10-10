from pathlib import Path
import pandas as pd

# Project folders
ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "results" / "controller_results.csv"
REPORT_PATH = ROOT / "results" / "validation_summary.csv"

# Acceptance criteria
LIMITS = {
    "RiseTime_s": 2.0,
    "SettlingTime_s": 5.0,
    "Overshoot_pct": 10.0,
    "SteadyStateError_pct": 2.0,
}


def validate(row):
    checks = {}

    for metric, limit in LIMITS.items():
        value = pd.to_numeric(row[metric], errors="coerce")
        checks[metric] = pd.notna(value) and value <= limit

    overall = "PASS" if all(checks.values()) else "FAIL"
    return checks, overall


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {CSV_PATH}\n"
            "Export controller_results.csv from MATLAB "
            "into the project's results folder."
        )

    df = pd.read_csv(CSV_PATH)

    required = ["Controller", *LIMITS.keys()]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    report = []

    for _, row in df.iterrows():
        checks, overall = validate(row)

        print(f"\nController: {row['Controller']}")

        for metric, passed in checks.items():
            print(f"  {metric}: {'PASS' if passed else 'FAIL'}")

        print(f"Overall verdict: {overall}")

        report.append({
            "Controller": row["Controller"],
            **{metric: row[metric] for metric in LIMITS},
            **{
                f"{metric}_status":
                "PASS" if passed else "FAIL"
                for metric, passed in checks.items()
            },
            "Overall": overall,
        })

    pd.DataFrame(report).to_csv(REPORT_PATH, index=False)
    print(f"\nSummary saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()