from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Provisional acceptance criteria
LIMITS = {
    "MaxDisturbanceEffect": 0.10,
    "RecoveryTime_s": 2.50,
}


def validate_scenario(row):
    effect = pd.to_numeric(
        pd.Series([row["MaxDisturbanceEffect"]]),
        errors="coerce"
    ).iloc[0]

    recovery = pd.to_numeric(
        pd.Series([row["RecoveryTime_s"]]),
        errors="coerce"
    ).iloc[0]

    effect_pass = pd.notna(effect) and effect >= 0 and (
        effect <= LIMITS["MaxDisturbanceEffect"]
    )

    recovery_pass = pd.notna(recovery) and recovery >= 0 and (
        recovery <= LIMITS["RecoveryTime_s"]
    )

    return {
        "EffectStatus": "PASS" if effect_pass else "FAIL",
        "RecoveryStatus": "PASS" if recovery_pass else "FAIL",
        "Overall": (
            "PASS" if effect_pass and recovery_pass else "FAIL"
        ),
    }


def main():
    source = RESULTS / "disturbance_results.csv"

    if not source.exists():
        raise FileNotFoundError(
            f"Missing simulation results: {source}"
        )

    df = pd.read_csv(source)

    required = [
        "Scenario",
        "Controller",
        "MaxDisturbanceEffect",
        "RecoveryTime_s",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    report = []

    for _, row in df.iterrows():
        verdict = validate_scenario(row)

        result = {
            "Scenario": row["Scenario"],
            "Controller": row["Controller"],
            "MaxDisturbanceEffect": row["MaxDisturbanceEffect"],
            "RecoveryTime_s": row["RecoveryTime_s"],
            **verdict,
        }

        report.append(result)

        print(
            f"{row['Scenario']} | {row['Controller']} | "
            f"{verdict['Overall']}"
        )

    output = pd.DataFrame(report)
    output.to_csv(RESULTS / "scenario_report.csv", index=False)

    # Descriptive pass rate, not a stability certificate.
    summary = (
        output.groupby("Controller")["Overall"]
        .apply(lambda s: (s == "PASS").mean() * 100)
        .rename("ScenarioPassRate_pct")
        .reset_index()
    )

    summary.to_csv(RESULTS / "robustness_summary.csv", index=False)

    print("\nScenario report saved.")
    print("\nPass rate across available scenarios:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
