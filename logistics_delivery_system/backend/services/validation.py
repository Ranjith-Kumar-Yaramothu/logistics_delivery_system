
from pathlib import Path
import json
import pandas as pd

DATA = Path("data/generated")


def validate_dataset():
    errors = []
    checks = {}

    required = {
        "customer_sites": ["site_id"],
        "orders": ["order_id", "site_id"],
        "deliveries": ["delivery_id", "order_id", "site_id"],
        "vehicles": ["vehicle_id"],
        "vehicle_capacities": ["capacity_id", "vehicle_id"],
        "drivers": ["driver_id"],
        "shifts": ["shift_id", "driver_id"],
        "time_windows": ["time_window_id", "delivery_id"]
    }

    frames = {}

    # 1. Check required CSV files and columns
    for name, columns in required.items():
        path = DATA / f"{name}.csv"

        if not path.exists():
            errors.append(f"Missing file: {path}")
            continue

        df = pd.read_csv(path)
        frames[name] = df

        checks[f"{name}_rows"] = len(df)

        missing_columns = [
            col for col in columns if col not in df.columns
        ]

        if missing_columns:
            errors.append(
                f"{name} missing columns: {missing_columns}"
            )
            continue

        for col in columns:
            if df[col].isna().any():
                errors.append(
                    f"{name}.{col} contains null values"
                )

        pk = columns[0]

        if df[pk].duplicated().any():
            errors.append(
                f"{name}.{pk} is not unique"
            )

    # 2. Check foreign-key relationships
    relationships = [
        ("orders", "site_id", "customer_sites", "site_id"),
        ("deliveries", "order_id", "orders", "order_id"),
        ("deliveries", "site_id", "customer_sites", "site_id"),
        ("vehicle_capacities", "vehicle_id", "vehicles", "vehicle_id"),
        ("shifts", "driver_id", "drivers", "driver_id"),
        ("time_windows", "delivery_id", "deliveries", "delivery_id")
    ]

    for child, fk, parent, pk in relationships:
        if child not in frames or parent not in frames:
            continue

        if fk not in frames[child].columns:
            continue

        if pk not in frames[parent].columns:
            continue

        invalid = ~frames[child][fk].isin(
            frames[parent][pk]
        )

        if invalid.any():
            errors.append(
                f"{child}.{fk}: {int(invalid.sum())} invalid references"
            )

    # 3. Validate delivery demand
    if "deliveries" in frames:
        df = frames["deliveries"]

        if (
            (df["demand_weight_kg"] <= 0).any()
            or (df["demand_volume_m3"] <= 0).any()
        ):
            errors.append("Delivery demand must be positive")

    # 4. Validate time windows
    if "time_windows" in frames:
        df = frames["time_windows"]

        if (
            pd.to_datetime(df["window_start"])
            >= pd.to_datetime(df["window_end"])
        ).any():
            errors.append("Invalid time window ordering")

    # 5. Validate travel-time matrix
    matrix_path = DATA / "travel_time_matrix.csv"

    if not matrix_path.exists():
        errors.append("Missing travel_time_matrix.csv")
    elif "customer_sites" in frames:
        try:
            sites = frames["customer_sites"]["site_id"].tolist()
            site_count = len(sites)

            expected_pairs = site_count * (site_count - 1)

            manifest_path = DATA / "source_manifest.json"

            if manifest_path.exists():
                manifest = json.loads(
                    manifest_path.read_text()
                )

                n_days = manifest.get("days", 30)
                scenarios = manifest.get(
                    "travel_scenarios",
                    ["NORMAL", "TRAFFIC"]
                )
            else:
                n_days = 30
                scenarios = ["NORMAL", "TRAFFIC"]

            expected_per_scenario = expected_pairs * n_days
            scenario_counts = {}
            duplicate_count = 0
            invalid_reference_count = 0
            self_loop_count = 0
            invalid_scenario_count = 0
            invalid_value_count = 0

            site_ids = set(sites)
            seen_pairs = set()

            for chunk in pd.read_csv(
                matrix_path,
                chunksize=100000
            ):
                required_columns = [
                    "matrix_id",
                    "from_site_id",
                    "to_site_id",
                    "scenario_date",
                    "scenario",
                    "distance_km",
                    "travel_minutes"
                ]

                missing = [
                    col for col in required_columns
                    if col not in chunk.columns
                ]

                if missing:
                    errors.append(
                        f"Travel matrix missing columns: {missing}"
                    )
                    break

                for scenario, count in (
                    chunk["scenario"].value_counts().items()
                ):
                    scenario_counts[scenario] = (
                        scenario_counts.get(scenario, 0)
                        + int(count)
                    )

                invalid_reference_count += int(
                    (
                        ~chunk["from_site_id"].isin(site_ids)
                        | ~chunk["to_site_id"].isin(site_ids)
                    ).sum()
                )

                self_loop_count += int(
                    (
                        chunk["from_site_id"]
                        == chunk["to_site_id"]
                    ).sum()
                )

                invalid_scenario_count += int(
                    (~chunk["scenario"].isin(scenarios)).sum()
                )

                invalid_value_count += int(
                    (
                        (chunk["distance_km"] <= 0)
                        | (chunk["travel_minutes"] <= 0)
                    ).sum()
                )

                # Check duplicate directed pairs within each chunk.
                keys = [
                    "from_site_id",
                    "to_site_id",
                    "scenario_date",
                    "scenario"
                ]

                duplicate_count += int(
                    chunk.duplicated(subset=keys).sum()
                )

            checks["travel_time_matrix_rows"] = sum(
                scenario_counts.values()
            )

            checks["travel_matrix_scenario_counts"] = (
                scenario_counts
            )

            checks["expected_rows_per_scenario"] = (
                expected_per_scenario
            )

            checks["expected_total_matrix_rows"] = (
                expected_per_scenario * len(scenarios)
            )

            checks["travel_matrix_duplicate_rows_within_chunks"] = (
                duplicate_count
            )

            if invalid_reference_count:
                errors.append(
                    f"Travel matrix has {invalid_reference_count} invalid site references"
                )

            if self_loop_count:
                errors.append(
                    f"Travel matrix has {self_loop_count} self-loop records"
                )

            if invalid_scenario_count:
                errors.append(
                    f"Travel matrix has {invalid_scenario_count} invalid scenarios"
                )

            if invalid_value_count:
                errors.append(
                    f"Travel matrix has {invalid_value_count} invalid distance/time values"
                )

            if duplicate_count:
                errors.append(
                    "Duplicate travel pairs found within matrix chunks"
                )

            for scenario in scenarios:
                actual = scenario_counts.get(scenario, 0)

                if actual != expected_per_scenario:
                    errors.append(
                        f"{scenario}: expected "
                        f"{expected_per_scenario} rows, found {actual}"
                    )

            for scenario in scenario_counts:
                if scenario not in scenarios:
                    errors.append(
                        f"Unexpected travel scenario: {scenario}"
                    )

        except Exception as exc:
            errors.append(
                f"Travel matrix validation failed: {exc}"
            )

    return {
        "valid": len(errors) == 0,
        "checks": checks,
        "errors": errors
    }


if __name__ == "__main__":
    print(
        json.dumps(
            validate_dataset(),
            indent=2
        )
    )
