
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "results" / "disturbance_results.csv"

# Initial project acceptance criteria; tune these
# after establishing a documented engineering baseline.
MAX_EFFECT_LIMIT = 0.10
MAX_RECOVERY_TIME = 2.50


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Results file not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    required = [
        "Scenario",
        "Controller",
        "MaxDisturbanceEffect",
        "RecoveryTime_s",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    reports = []

    for _, row in df.iterrows():
        effect = pd.to_numeric(
            row["MaxDisturbanceEffect"], errors="coerce"
        )
        recovery = pd.to_numeric(
            row["RecoveryTime_s"], errors="coerce"
        )

        effect_pass = (
            pd.notna(effect) and effect <= MAX_EFFECT_LIMIT
        )
        recovery_pass = (
            pd.notna(recovery)
            and recovery >= 0
            and recovery <= MAX_RECOVERY_TIME
        )

        overall = (
            "PASS" if effect_pass and recovery_pass else "FAIL"
        )

        print(f"\nScenario: {row['Scenario']}")
        print(f"Controller: {row['Controller']}")
        print(
            f"Maximum effect: {effect} -> "
            f"{'PASS' if effect_pass else 'FAIL'}"
        )
        print(
            f"Recovery time: {recovery} s -> "
            f"{'PASS' if recovery_pass else 'FAIL'}"
        )
        print(f"Overall verdict: {overall}")

        reports.append({
            "Scenario": row["Scenario"],
            "Controller": row["Controller"],
            "MaxDisturbanceEffect": effect,
            "RecoveryTime_s": recovery,
            "EffectStatus": "PASS" if effect_pass else "FAIL",
            "RecoveryStatus": (
                "PASS" if recovery_pass else "FAIL"
            ),
            "Overall": overall,
        })

    report_path = ROOT / "results" / "disturbance_validation.csv"
    pd.DataFrame(reports).to_csv(report_path, index=False)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
