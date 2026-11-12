
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models import (
    Route,
    RouteStop,
    VehicleCapacity,
    Shift,
    Delivery,
    CustomerSite,
    TimeWindow
)


DELAY_THRESHOLD_MINUTES = 30


def detect_route_anomalies(db: Session, route_id: str):

    route = db.query(Route).filter_by(route_id=route_id).first()

    if not route:
        return [{
            "issue_type": "ROUTE_NOT_FOUND",
            "severity": "ERROR"
        }]

    issues = []

    stops = (
        db.query(RouteStop)
        .filter_by(route_id=route_id)
        .order_by(RouteStop.sequence_no)
        .all()
    )

    delivery_ids = [stop.delivery_id for stop in stops]

    # 1. Duplicate deliveries within the same route
    if len(delivery_ids) != len(set(delivery_ids)):
        issues.append({
            "issue_type": "DUPLICATE_DELIVERY",
            "severity": "HIGH"
        })

    # 2. Duplicate delivery assignments across different routes
    for delivery_id in set(delivery_ids):
        other_route = (
            db.query(RouteStop)
            .filter(
                RouteStop.delivery_id == delivery_id,
                RouteStop.route_id != route_id
            )
            .first()
        )

        if other_route:
            issues.append({
                "issue_type": "DUPLICATE_ROUTE_ASSIGNMENT",
                "delivery_id": delivery_id,
                "other_route_id": other_route.route_id,
                "severity": "HIGH"
            })

    # Load deliveries
    deliveries = (
        db.query(Delivery)
        .filter(Delivery.delivery_id.in_(delivery_ids))
        .all()
        if delivery_ids else []
    )

    delivery_map = {
        delivery.delivery_id: delivery
        for delivery in deliveries
    }

    # 3. Vehicle capacity checks
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

    if capacity:
        total_weight = sum(
            d.demand_weight_kg for d in deliveries
        )

        total_volume = sum(
            d.demand_volume_m3 for d in deliveries
        )

        if total_weight > capacity.max_weight_kg:
            issues.append({
                "issue_type": "WEIGHT_CAPACITY_EXCEEDED",
                "actual": total_weight,
                "limit": capacity.max_weight_kg,
                "severity": "HIGH"
            })

        if total_volume > capacity.max_volume_m3:
            issues.append({
                "issue_type": "VOLUME_CAPACITY_EXCEEDED",
                "actual": total_volume,
                "limit": capacity.max_volume_m3,
                "severity": "HIGH"
            })

        if len(stops) > capacity.max_stops:
            issues.append({
                "issue_type": "MAX_STOPS_EXCEEDED",
                "actual": len(stops),
                "limit": capacity.max_stops,
                "severity": "HIGH"
            })

    # 4. Stop sequence and actual time checks
    for previous, current in zip(stops, stops[1:]):

        if current.planned_arrival < previous.planned_departure:
            issues.append({
                "issue_type": "ARRIVAL_BEFORE_PREVIOUS_DEPARTURE",
                "previous_stop": previous.stop_id,
                "stop": current.stop_id,
                "severity": "HIGH"
            })

    for stop in stops:

        if (
            stop.actual_arrival
            and stop.actual_departure
            and stop.actual_departure < stop.actual_arrival
        ):
            issues.append({
                "issue_type": "INVALID_ACTUAL_STOP_TIMES",
                "stop_id": stop.stop_id,
                "severity": "HIGH"
            })

        delivery = delivery_map.get(stop.delivery_id)

        if not delivery:
            continue

        # 5. Unexpected delivery delay
        if stop.actual_arrival:

            delay_minutes = (
                stop.actual_arrival - stop.planned_arrival
            ).total_seconds() / 60

            if delay_minutes > DELAY_THRESHOLD_MINUTES:
                issues.append({
                    "issue_type": "UNEXPECTED_DELIVERY_DELAY",
                    "delivery_id": delivery.delivery_id,
                    "delay_minutes": round(delay_minutes, 2),
                    "threshold_minutes": DELAY_THRESHOLD_MINUTES,
                    "severity": "HIGH"
                })

        # 6. Customer time window checks
        window = (
            db.query(TimeWindow)
            .filter_by(delivery_id=delivery.delivery_id)
            .first()
        )

        if window:

            if stop.planned_arrival < window.window_start:
                issues.append({
                    "issue_type": "PLANNED_EARLY_ARRIVAL",
                    "delivery_id": delivery.delivery_id,
                    "severity": "LOW"
                })

            if stop.planned_arrival > window.window_end:
                issues.append({
                    "issue_type": "PLANNED_LATE_ARRIVAL",
                    "delivery_id": delivery.delivery_id,
                    "severity": "HIGH"
                })

            if stop.actual_arrival:

                if stop.actual_arrival < window.window_start:
                    issues.append({
                        "issue_type": "ACTUAL_EARLY_ARRIVAL",
                        "delivery_id": delivery.delivery_id,
                        "severity": "LOW"
                    })

                if stop.actual_arrival > window.window_end:
                    issues.append({
                        "issue_type": "ACTUAL_LATE_ARRIVAL",
                        "delivery_id": delivery.delivery_id,
                        "severity": "HIGH"
                    })

        # 7. Customer site coordinate checks
        site = (
            db.query(CustomerSite)
            .filter_by(site_id=delivery.site_id)
            .first()
        )

        if site and not (
            16.8 <= site.latitude <= 18.0
            and 77.8 <= site.longitude <= 79.0
        ):
            issues.append({
                "issue_type": "COORDINATE_OUTSIDE_REGION",
                "site_id": site.site_id,
                "severity": "MEDIUM"
            })

    # 8. Driver shift check
    shift = (
        db.query(Shift)
        .filter_by(
            driver_id=route.driver_id,
            shift_date=route.route_date
        )
        .first()
    )

    if shift and stops:

        last_stop = stops[-1]

        final_departure = (
            last_stop.actual_departure
            or last_stop.planned_departure
        )

        if final_departure > shift.end_time:
            issues.append({
                "issue_type": "DRIVER_SHIFT_EXCEEDED",
                "severity": "HIGH"
            })

    return issues
