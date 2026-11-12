
import csv
from pathlib import Path
from uuid import uuid4
from datetime import timedelta

from sqlalchemy import or_

from backend.database import SessionLocal
from backend.models import (
    Route,
    RouteStop,
    Delivery,
    VehicleCapacity,
    Shift,
    CustomerSite,
    TimeWindow
)
from backend.services.anomaly_detector import detect_route_anomalies


ROUTE_ID = "RTE-2026-000002"

GROUND_TRUTH_FILE = Path(
    "data/ground_truth/ground_truth.csv"
)


def get_test_data(db):

    route = (
        db.query(Route)
        .filter_by(route_id=ROUTE_ID)
        .first()
    )

    if not route:
        raise ValueError(f"Route not found: {ROUTE_ID}")

    stops = (
        db.query(RouteStop)
        .filter_by(route_id=ROUTE_ID)
        .order_by(RouteStop.sequence_no)
        .all()
    )

    if not stops:
        raise ValueError("No route stops found")

    deliveries = (
        db.query(Delivery)
        .filter(
            Delivery.delivery_id.in_(
                [stop.delivery_id for stop in stops]
            )
        )
        .all()
    )

    if not deliveries:
        raise ValueError("No deliveries found for this route")

    return route, stops, deliveries


def get_capacity(db, route):

    capacity = (
        db.query(VehicleCapacity)
        .filter(
            VehicleCapacity.vehicle_id == route.vehicle_id,
            VehicleCapacity.effective_from <= route.route_date,
            or_(
                VehicleCapacity.effective_to.is_(None),
                VehicleCapacity.effective_to >= route.route_date
            )
        )
        .order_by(VehicleCapacity.effective_from.desc())
        .first()
    )

    if not capacity:
        raise ValueError("Vehicle capacity record not found")

    return capacity


def get_shift(db, route):

    shift = (
        db.query(Shift)
        .filter(
            Shift.driver_id == route.driver_id,
            Shift.shift_date == route.route_date
        )
        .first()
    )

    if not shift:
        raise ValueError("Driver shift not found")

    return shift


def inject_anomaly(db, issue_type):

    route, stops, deliveries = get_test_data(db)

    first_stop = stops[0]
    last_stop = stops[-1]
    first_delivery = deliveries[0]

    # 1. Unexpected delivery delay
    if issue_type == "UNEXPECTED_DELIVERY_DELAY":

        first_stop.actual_arrival = (
            first_stop.planned_arrival
            + timedelta(minutes=31)
        )

    # 2. Weight capacity exceeded
    elif issue_type == "WEIGHT_CAPACITY_EXCEEDED":

        capacity = get_capacity(db, route)

        first_delivery.demand_weight_kg = (
            capacity.max_weight_kg + 100
        )

    # 3. Volume capacity exceeded
    elif issue_type == "VOLUME_CAPACITY_EXCEEDED":

        capacity = get_capacity(db, route)

        first_delivery.demand_volume_m3 = (
            capacity.max_volume_m3 + 10
        )

    # 4. Duplicate delivery
    elif issue_type == "DUPLICATE_DELIVERY":

        duplicate_stop = RouteStop(
            stop_id=f"TEST-{uuid4().hex[:20]}",
            route_id=route.route_id,
            delivery_id=first_stop.delivery_id,
            sequence_no=max(
                stop.sequence_no for stop in stops
            ) + 1,
            planned_arrival=last_stop.planned_arrival,
            planned_departure=last_stop.planned_departure,
            stop_status="PLANNED"
        )

        db.add(duplicate_stop)

    # 5. Arrival before previous departure
    elif issue_type == "ARRIVAL_BEFORE_PREVIOUS_DEPARTURE":

        if len(stops) < 2:
            raise ValueError(
                "At least two stops are required"
            )

        second_stop = stops[1]

        second_stop.planned_arrival = (
            first_stop.planned_departure
            - timedelta(minutes=1)
        )

    # 6. Driver shift exceeded
    elif issue_type == "DRIVER_SHIFT_EXCEEDED":

        shift = get_shift(db, route)

        last_stop.actual_departure = (
            shift.end_time + timedelta(minutes=10)
        )

    # 7. Customer coordinates outside region
    elif issue_type == "COORDINATE_OUTSIDE_REGION":

        site = (
            db.query(CustomerSite)
            .filter_by(site_id=first_delivery.site_id)
            .first()
        )

        if not site:
            raise ValueError("Customer site not found")

        site.latitude = 99.0

    # 8. Planned late arrival
    elif issue_type == "PLANNED_LATE_ARRIVAL":

        window = (
            db.query(TimeWindow)
            .filter_by(
                delivery_id=first_delivery.delivery_id
            )
            .first()
        )

        if not window:
            raise ValueError("Customer time window not found")

        window.window_end = (
            first_stop.planned_arrival
            - timedelta(minutes=1)
        )

    # 9. Actual late arrival
    elif issue_type == "ACTUAL_LATE_ARRIVAL":

        window = (
            db.query(TimeWindow)
            .filter_by(
                delivery_id=first_delivery.delivery_id
            )
            .first()
        )

        if not window:
            raise ValueError("Customer time window not found")

        first_stop.actual_arrival = (
            first_stop.planned_arrival
            + timedelta(minutes=5)
        )

        window.window_end = (
            first_stop.planned_arrival
            + timedelta(minutes=2)
        )

    else:
        raise ValueError(
            f"Unknown anomaly type: {issue_type}"
        )


def load_ground_truth():

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {GROUND_TRUTH_FILE}"
        )

    with open(
        GROUND_TRUTH_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(
            line for line in file if line.strip()
        )

        if not reader.fieldnames:
            raise ValueError(
                "Ground truth CSV header is missing"
            )

        reader.fieldnames = [
            name.strip() for name in reader.fieldnames
        ]

        required_columns = {
            "anomaly_id",
            "issue_type",
            "description",
            "expected_severity",
            "source"
        }

        missing = required_columns - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing CSV columns: {sorted(missing)}"
            )

        scenarios = list(reader)

    return scenarios


def evaluate_ground_truth():

    scenarios = load_ground_truth()

    db = SessionLocal()

    results = []

    try:

        # Confirm the test route exists.
        get_test_data(db)

        print("\nGROUND TRUTH ANOMALY EVALUATION")
        print("=" * 75)

        for scenario in scenarios:

            anomaly_id = scenario["anomaly_id"].strip()
            issue_type = scenario["issue_type"].strip()
            expected_severity = (
                scenario["expected_severity"].strip()
            )

            try:

                # Start each test from the original database state.
                db.rollback()

                inject_anomaly(db, issue_type)

                # Apply temporary changes inside the transaction.
                db.flush()

                detected = detect_route_anomalies(
                    db,
                    ROUTE_ID
                )

                matching = [
                    issue
                    for issue in detected
                    if issue.get("issue_type") == issue_type
                ]

                issue_detected = bool(matching)

                severity_match = any(
                    issue.get("severity") == expected_severity
                    for issue in matching
                )

                passed = (
                    issue_detected and severity_match
                )

                status = "PASS" if passed else "FAIL"

                results.append({
                    "anomaly_id": anomaly_id,
                    "issue_type": issue_type,
                    "expected_severity": expected_severity,
                    "detected": issue_detected,
                    "severity_match": severity_match,
                    "status": status
                })

                print(
                    f"{anomaly_id} | "
                    f"{issue_type} | "
                    f"{status}"
                )

                if issue_detected and not severity_match:
                    print(
                        f"  Expected severity: {expected_severity}"
                    )
                    print(
                        f"  Detected severity: "
                        f"{[i.get('severity') for i in matching]}"
                    )

                if not issue_detected:
                    print(
                        "  Expected anomaly was not detected."
                    )

            except Exception as error:

                db.rollback()

                results.append({
                    "anomaly_id": anomaly_id,
                    "issue_type": issue_type,
                    "expected_severity": expected_severity,
                    "detected": False,
                    "severity_match": False,
                    "status": "ERROR",
                    "error": str(error)
                })

                print(
                    f"{anomaly_id} | "
                    f"{issue_type} | ERROR"
                )

                print(f"  Error: {error}")

            finally:

                # Never retain injected test changes.
                db.rollback()

        passed_count = sum(
            result["status"] == "PASS"
            for result in results
        )

        failed_count = sum(
            result["status"] == "FAIL"
            for result in results
        )

        error_count = sum(
            result["status"] == "ERROR"
            for result in results
        )

        total = len(results)

        print("\n" + "=" * 75)
        print("GROUND TRUTH EVALUATION SUMMARY")
        print("=" * 75)

        print(f"Total scenarios : {total}")
        print(f"Passed          : {passed_count}")
        print(f"Failed          : {failed_count}")
        print(f"Errors          : {error_count}")

        accuracy = (
            passed_count / total * 100
            if total else 0
        )

        print(f"Accuracy        : {accuracy:.2f}%")

        if passed_count == total:
            print("\nAll anomaly scenarios passed!")
        else:
            print("\nSome scenarios need correction.")

        print("=" * 75)

    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    evaluate_ground_truth()
