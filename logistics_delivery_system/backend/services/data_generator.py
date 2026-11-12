
from pathlib import Path
from datetime import datetime, date, time, timedelta
import json
import hashlib

import pandas as pd
import numpy as np


OUT = Path("data/generated")
GT = Path("data/ground_truth")

OUT.mkdir(parents=True, exist_ok=True)
GT.mkdir(parents=True, exist_ok=True)


def write_csv(df, name):
    df.to_csv(OUT / f"{name}.csv", index=False)


def generate_travel_matrix(sites, base_date, n_days):
    """
    Generate complete directed travel matrices for NORMAL
    and TRAFFIC scenarios, writing small batches to CSV.
    """

    path = OUT / "travel_time_matrix.csv"

    if path.exists():
        path.unlink()

    site_count = len(sites)
    matrix_id = 1
    total_rows = 0
    header_written = False

    scenarios = [
        ("NORMAL", 1.0),
        ("TRAFFIC", 1.5)
    ]

    # Process a small group of origin sites at a time.
    batch_size = 25

    for day in range(n_days):
        current_date = base_date + timedelta(days=day)

        for scenario, multiplier in scenarios:

            for start in range(0, site_count, batch_size):
                end = min(start + batch_size, site_count)
                records = []

                for a in range(start, end):
                    for b in range(site_count):

                        if a == b:
                            continue

                        dx = (
                            sites[a]["latitude"]
                            - sites[b]["latitude"]
                        )

                        dy = (
                            sites[a]["longitude"]
                            - sites[b]["longitude"]
                        )

                        distance = max(
                            1.0,
                            float(
                                np.sqrt(
                                    (dx * 111) ** 2
                                    + (dy * 95) ** 2
                                )
                            )
                        )

                        travel_minutes = max(
                            1,
                            int(round(
                                distance / 25 * 60 * multiplier
                            ))
                        )

                        records.append({
                            "matrix_id": matrix_id,
                            "from_site_id": sites[a]["site_id"],
                            "to_site_id": sites[b]["site_id"],
                            "scenario_date": current_date.isoformat(),
                            "scenario": scenario,
                            "distance_km": round(distance, 2),
                            "travel_minutes": travel_minutes
                        })

                        matrix_id += 1

                batch_df = pd.DataFrame(records)

                batch_df.to_csv(
                    path,
                    mode="a",
                    header=not header_written,
                    index=False
                )

                header_written = True
                total_rows += len(batch_df)

    return total_rows


def generate_dataset(
    mode="starter",
    seed=20261022,
    inject_anomalies=True
):
    rng = np.random.default_rng(seed)

    if mode == "starter":
        n_sites, n_deliveries, n_vehicles, n_drivers = (
            30, 100, 10, 10
        )
    elif mode == "full":
        n_sites, n_deliveries, n_vehicles, n_drivers = (
            500, 2000, 100, 100
        )
    else:
        raise ValueError("Mode must be starter or full")

    base_date = date(2026, 11, 1)
    n_days = 30

    # 1. Customer sites
    sites = []

    for i in range(1, n_sites + 1):
        sites.append({
            "site_id": f"SITE-{i:06d}",
            "site_name": f"Customer Site {i:03d}",
            "address": f"Delivery Zone {i:03d}",
            "latitude": round(
                17.20 + rng.random() * 0.65, 6
            ),
            "longitude": round(
                78.20 + rng.random() * 0.75, 6
            ),
            "region": "HYDERABAD",
            "is_active": True
        })

    sites_df = pd.DataFrame(sites)

    # 2. Vehicles and capacities
    vehicles = []
    capacities = []

    for i in range(1, n_vehicles + 1):
        vehicle_id = f"VEH-{i:06d}"

        vehicles.append({
            "vehicle_id": vehicle_id,
            "vehicle_type": "VAN" if i % 3 else "TRUCK",
            "registration_no": f"TS-{i:02d}-AB-{1000+i}",
            "is_active": True,
            "restricted_region": (
                None if i % 5 else "OLD_CITY"
            )
        })

        capacities.append({
            "capacity_id": i,
            "vehicle_id": vehicle_id,
            "effective_from": base_date.isoformat(),
            "effective_to": None,
            "max_weight_kg": (
                800 if i % 3 else 2500
            ),
            "max_volume_m3": (
                8 if i % 3 else 20
            ),
            "max_stops": (
                15 if i % 3 else 25
            )
        })

    vehicles_df = pd.DataFrame(vehicles)
    capacities_df = pd.DataFrame(capacities)

    # 3. Drivers and shifts
    drivers = []
    shifts = []

    for i in range(1, n_drivers + 1):
        driver_id = f"DRV-{i:06d}"

        drivers.append({
            "driver_id": driver_id,
            "driver_name": f"Driver {i:03d}",
            "license_type": "LMV" if i % 3 else "HMV",
            "is_active": True
        })

        for day in range(n_days):
            current_date = base_date + timedelta(days=day)

            shifts.append({
                "shift_id": (i - 1) * n_days + day + 1,
                "driver_id": driver_id,
                "shift_date": current_date.isoformat(),
                "start_time": f"{current_date} 08:00:00",
                "end_time": f"{current_date} 18:00:00"
            })

    drivers_df = pd.DataFrame(drivers)
    shifts_df = pd.DataFrame(shifts)

    # 4. Orders, deliveries and time windows
    orders = []
    deliveries = []
    windows = []

    for i in range(1, n_deliveries + 1):
        order_id = f"ORD-2026-{i:06d}"
        delivery_id = f"DEL-2026-{i:06d}"

        site = sites[int(rng.integers(0, n_sites))]
        day = int(rng.integers(0, n_days))
        current_date = base_date + timedelta(days=day)

        start_hour = int(
            rng.choice([9, 10, 11, 13, 14])
        )

        start = datetime.combine(
            current_date,
            time(start_hour, 0)
        )

        end = start + timedelta(
            hours=int(rng.choice([2, 3, 4]))
        )

        priority = str(
            rng.choice(
                ["LOW", "NORMAL", "HIGH"],
                p=[0.2, 0.6, 0.2]
            )
        )

        weight = round(
            float(rng.uniform(5, 180)), 2
        )

        volume = round(
            float(weight / rng.uniform(80, 160)), 3
        )

        orders.append({
            "order_id": order_id,
            "site_id": site["site_id"],
            "order_date": current_date.isoformat(),
            "priority": priority,
            "status": "OPEN",
            "created_at": f"{current_date} 07:00:00"
        })

        deliveries.append({
            "delivery_id": delivery_id,
            "order_id": order_id,
            "site_id": site["site_id"],
            "demand_weight_kg": weight,
            "demand_volume_m3": volume,
            "service_minutes": int(
                rng.integers(10, 31)
            ),
            "requested_date": current_date.isoformat(),
            "priority": priority,
            "status": "PENDING",
            "issue_type": None
        })

        windows.append({
            "time_window_id": i,
            "delivery_id": delivery_id,
            "window_start": start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "window_end": end.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

    orders_df = pd.DataFrame(orders)
    deliveries_df = pd.DataFrame(deliveries)
    windows_df = pd.DataFrame(windows)

    # 5. Save normal datasets
    datasets = {
        "customer_sites": sites_df,
        "orders": orders_df,
        "deliveries": deliveries_df,
        "vehicles": vehicles_df,
        "vehicle_capacities": capacities_df,
        "drivers": drivers_df,
        "shifts": shifts_df,
        "time_windows": windows_df
    }

    for name, df in datasets.items():
        write_csv(df, name)

    # 6. Generate complete travel-time scenarios
    matrix_rows = generate_travel_matrix(
        sites,
        base_date,
        n_days
    )

    # 7. Ground-truth anomaly catalogue
    truth = []

    if inject_anomalies:
        cases = [
            (
                "ANOM-001",
                "CAPACITY_EXCEEDED",
                "Route demand exceeds vehicle capacity",
                "REJECT_ROUTE"
            ),
            (
                "ANOM-002",
                "STOP_OMITTED",
                "Assigned delivery is absent from route stops",
                "FLAG_UNASSIGNED_STOP"
            ),
            (
                "ANOM-003",
                "STOP_DUPLICATED",
                "Same delivery appears twice in one route",
                "FLAG_DUPLICATE_STOP"
            ),
            (
                "ANOM-004",
                "ARRIVAL_BEFORE_DEPARTURE",
                "Next arrival precedes previous departure",
                "FLAG_TIME_SEQUENCE"
            ),
            (
                "ANOM-005",
                "SHIFT_EXCEEDED",
                "Route ends after driver shift",
                "FLAG_SHIFT_VIOLATION"
            ),
            (
                "ANOM-006",
                "COORDINATE_OUT_OF_REGION",
                "Site coordinate outside configured region",
                "FLAG_GEO_BOUNDARY"
            )
        ]

        for anomaly_id, issue, description, expected in cases:
            truth.append({
                "anomaly_id": anomaly_id,
                "issue_type": issue,
                "description": description,
                "expected_decision": expected,
                "source": "SYNTHETIC_RULE"
            })

    truth_df = pd.DataFrame(truth)

    truth_df.to_csv(
        GT / "ground_truth.csv",
        index=False
    )

    # 8. Dataset manifest
    counts = {
        name: len(df)
        for name, df in datasets.items()
    }

    counts["travel_time_matrix"] = matrix_rows

    manifest = {
        "seed": seed,
        "mode": mode,
        "counts": counts,
        "generator_version": "2.0",
        "base_date": str(base_date),
        "days": n_days,
        "travel_scenarios": ["NORMAL", "TRAFFIC"]
    }

    (OUT / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )

    # 9. Calculate checksums using small file-reading blocks
    checksums = {}

    for file_path in sorted(OUT.glob("*.csv")):
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            for block in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(block)

        checksums[file_path.name] = sha256.hexdigest()

    (OUT / "checksums.json").write_text(
        json.dumps(checksums, indent=2)
    )

    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["starter", "full"],
        default="starter"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20261022
    )

    args = parser.parse_args()

    result = generate_dataset(
        mode=args.mode,
        seed=args.seed
    )

    print(json.dumps(result, indent=2))
