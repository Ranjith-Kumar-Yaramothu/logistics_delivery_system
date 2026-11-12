
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models import (
    Delivery,
    CustomerSite,
    TimeWindow,
    Vehicle,
    VehicleCapacity,
    Driver,
    Shift,
    Route,
    RouteStop,
    EventHistory,
    TravelTimeMatrix
)


LICENSE_REQUIREMENTS = {
    "VAN": "LMV",
    "TRUCK": "HMV"
}

PRIORITY_ORDER = {
    "URGENT": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "NORMAL": 3,
    "LOW": 4
}


def build_greedy_plan(
    db: Session,
    plan_date,
    max_deliveries=100,
    scenario="NORMAL"
):
    try:
        scenario = scenario.upper()

        if scenario not in ("NORMAL", "TRAFFIC"):
            raise ValueError(
                "Scenario must be NORMAL or TRAFFIC"
            )

        # 1. Get pending deliveries
        deliveries = (
            db.query(Delivery)
            .filter(
                Delivery.requested_date == plan_date,
                Delivery.status == "PENDING"
            )
            .limit(max_deliveries)
            .all()
        )

        if not deliveries:
            return {
                "assigned": 0,
                "unserved": 0,
                "routes": [],
                "unassigned_details": []
            }

        # 2. Sort deliveries by priority and time window
        windows = {
            window.delivery_id: window
            for window in (
                db.query(TimeWindow)
                .join(
                    Delivery,
                    Delivery.delivery_id == TimeWindow.delivery_id
                )
                .filter(
                    Delivery.requested_date == plan_date
                )
                .all()
            )
        }

        def delivery_sort_key(delivery):
            priority = PRIORITY_ORDER.get(
                delivery.priority.upper(), 99
            )

            window = windows.get(delivery.delivery_id)
            window_start = (
                window.window_start
                if window else datetime.max
            )

            return (
                priority,
                window_start,
                delivery.delivery_id
            )

        deliveries.sort(key=delivery_sort_key)

        # 3. Load customer sites
        sites = {
            site.site_id: site
            for site in db.query(CustomerSite).all()
        }

        # 4. Load active vehicles and drivers
        vehicles = (
            db.query(Vehicle)
            .filter(Vehicle.is_active.is_(True))
            .order_by(Vehicle.vehicle_id)
            .all()
        )

        drivers = (
            db.query(Driver)
            .filter(Driver.is_active.is_(True))
            .order_by(Driver.driver_id)
            .all()
        )

        # 5. Identify vehicles and drivers already used
        existing_routes = (
            db.query(Route.vehicle_id, Route.driver_id)
            .filter(Route.route_date == plan_date)
            .all()
        )

        used_vehicles = {
            row.vehicle_id for row in existing_routes
        }

        used_drivers = {
            row.driver_id for row in existing_routes
        }

        # 6. Load effective vehicle capacities
        capacities = (
            db.query(VehicleCapacity)
            .filter(
                VehicleCapacity.effective_from <= plan_date
            )
            .filter(
                (VehicleCapacity.effective_to.is_(None)) |
                (VehicleCapacity.effective_to >= plan_date)
            )
            .order_by(
                VehicleCapacity.effective_from.desc()
            )
            .all()
        )

        capacity_by_vehicle = {}

        for capacity in capacities:
            if capacity.vehicle_id not in capacity_by_vehicle:
                capacity_by_vehicle[capacity.vehicle_id] = capacity

        # 7. Load driver shifts
        shifts = (
            db.query(Shift)
            .filter(Shift.shift_date == plan_date)
            .order_by(Shift.start_time)
            .all()
        )

        shift_by_driver = {}

        for shift in shifts:
            if shift.driver_id not in shift_by_driver:
                shift_by_driver[shift.driver_id] = shift

        # 8. Load travel-time matrix
        matrix_rows = (
            db.query(TravelTimeMatrix)
            .filter(
                TravelTimeMatrix.scenario_date == plan_date,
                TravelTimeMatrix.scenario == scenario
            )
            .all()
        )

        travel = {
            (row.from_site_id, row.to_site_id): (
                row.travel_minutes,
                row.distance_km
            )
            for row in matrix_rows
        }

        # 9. Track unassigned delivery reasons
        remaining = list(deliveries)
        reasons = {
            delivery.delivery_id: set()
            for delivery in deliveries
        }

        def add_reason(delivery, reason):
            reasons[delivery.delivery_id].add(reason)

        route_results = []

        # 10. Generate unique route IDs
        latest_route = (
            db.query(Route)
            .filter(
                Route.route_id.like(
                    f"RTE-{plan_date.year}-%"
                )
            )
            .order_by(Route.route_id.desc())
            .first()
        )

        if latest_route:
            route_number = (
                int(
                    latest_route.route_id.rsplit("-", 1)[-1]
                ) + 1
            )
        else:
            route_number = 1

        # 11. Assign deliveries to compatible vehicles and drivers
        for vehicle in vehicles:

            if not remaining:
                break

            if vehicle.vehicle_id in used_vehicles:
                continue

            capacity = capacity_by_vehicle.get(
                vehicle.vehicle_id
            )

            if not capacity:
                for delivery in remaining:
                    add_reason(delivery, "NO_VALID_VEHICLE_CAPACITY")
                continue

            required_license = LICENSE_REQUIREMENTS.get(
                vehicle.vehicle_type.upper()
            )

            if not required_license:
                for delivery in remaining:
                    add_reason(delivery, "UNSUPPORTED_VEHICLE_TYPE")
                continue

            compatible_drivers = [
                driver for driver in drivers
                if driver.driver_id not in used_drivers
                and driver.license_type.upper() == required_license
                and driver.driver_id in shift_by_driver
            ]

            if not compatible_drivers:
                for delivery in remaining:
                    add_reason(
                        delivery,
                        "NO_COMPATIBLE_DRIVER_OR_SHIFT"
                    )
                continue

            # Choose the compatible driver with the earliest shift
            driver = compatible_drivers[0]
            shift = shift_by_driver[driver.driver_id]

            if shift.start_time >= shift.end_time:
                for delivery in remaining:
                    add_reason(delivery, "INVALID_DRIVER_SHIFT")
                continue

            chosen = []
            current = shift.start_time
            previous_site = None

            total_weight = 0.0
            total_volume = 0.0
            total_distance = 0.0

            # 12. Select feasible deliveries
            while len(chosen) < capacity.max_stops:

                selected = None

                for delivery in remaining:

                    site = sites.get(delivery.site_id)

                    if not site or not site.is_active:
                        add_reason(
                            delivery,
                            "INVALID_OR_INACTIVE_CUSTOMER_SITE"
                        )
                        continue

                    # Vehicle restricted-region check
                    if (
                        vehicle.restricted_region
                        and site.region.upper()
                        == vehicle.restricted_region.upper()
                    ):
                        add_reason(
                            delivery,
                            "VEHICLE_RESTRICTED_FROM_REGION"
                        )
                        continue

                    # Weight capacity
                    if (
                        total_weight + delivery.demand_weight_kg
                        > capacity.max_weight_kg
                    ):
                        add_reason(
                            delivery,
                            "VEHICLE_WEIGHT_CAPACITY_EXCEEDED"
                        )
                        continue

                    # Volume capacity
                    if (
                        total_volume + delivery.demand_volume_m3
                        > capacity.max_volume_m3
                    ):
                        add_reason(
                            delivery,
                            "VEHICLE_VOLUME_CAPACITY_EXCEEDED"
                        )
                        continue

                    # Travel from previous customer site
                    travel_minutes = 0
                    distance_km = 0.0

                    if previous_site is not None:
                        if previous_site == delivery.site_id:
                            travel_minutes = 0
                            distance_km = 0.0
                        else:
                            leg = travel.get(
                                (previous_site, delivery.site_id)
                            )

                            if leg is None:
                                add_reason(
                                    delivery,
                                    "MISSING_TRAVEL_TIME"
                                )
                                continue

                            travel_minutes, distance_km = leg

                    arrival = current + timedelta(
                        minutes=travel_minutes
                    )

                    # Customer time-window validation
                    window = windows.get(delivery.delivery_id)

                    if window:
                        if arrival < window.window_start:
                            arrival = window.window_start

                        if arrival > window.window_end:
                            add_reason(
                                delivery,
                                "CUSTOMER_TIME_WINDOW_MISSED"
                            )
                            continue

                    departure = arrival + timedelta(
                        minutes=delivery.service_minutes
                    )

                    # Driver shift validation
                    if departure > shift.end_time:
                        add_reason(
                            delivery,
                            "DRIVER_SHIFT_TIME_EXCEEDED"
                        )
                        continue

                    selected = (
                        delivery,
                        arrival,
                        departure,
                        travel_minutes,
                        distance_km
                    )
                    break

                if selected is None:
                    break

                delivery, arrival, departure, leg_time, leg_distance = selected

                chosen.append(selected)

                total_weight += delivery.demand_weight_kg
                total_volume += delivery.demand_volume_m3
                total_distance += leg_distance

                current = departure
                previous_site = delivery.site_id

                remaining.remove(delivery)

            if not chosen:
                continue

            # 13. Create route
            route_id = (
                f"RTE-{plan_date.year}-{route_number:06d}"
            )
            route_number += 1

            route = Route(
                route_id=route_id,
                vehicle_id=vehicle.vehicle_id,
                driver_id=driver.driver_id,
                route_date=plan_date,
                status="PLANNED",
                planned_distance_km=round(total_distance, 2),
                planned_duration_minutes=int(
                    (current - shift.start_time).total_seconds()
                    / 60
                )
            )

            db.add(route)
            db.flush()

            # 14. Create route stops and event history
            for sequence, item in enumerate(chosen, start=1):

                delivery, arrival, departure, _, _ = item

                stop = RouteStop(
                    stop_id=(
                        f"STOP-{route_id}-{sequence:03d}"
                    ),
                    route_id=route_id,
                    delivery_id=delivery.delivery_id,
                    sequence_no=sequence,
                    planned_arrival=arrival,
                    planned_departure=departure,
                    stop_status="PLANNED"
                )

                delivery.status = "ASSIGNED"

                event = EventHistory(
                    entity_type="Delivery",
                    entity_id=delivery.delivery_id,
                    event_type="ASSIGNED_TO_ROUTE",
                    event_time=datetime.now(),
                    old_value="PENDING",
                    new_value=route_id,
                    details=(
                        f"Assigned using {scenario} scenario; "
                        f"vehicle={vehicle.vehicle_id}; "
                        f"driver={driver.driver_id}"
                    )
                )

                db.add(stop)
                db.add(event)

            route_results.append(route_id)

            used_vehicles.add(vehicle.vehicle_id)
            used_drivers.add(driver.driver_id)

        # 15. Build unassigned-delivery details
        unassigned_details = []

        for delivery in remaining:

            delivery_reasons = sorted(
                reasons[delivery.delivery_id]
            )

            if not delivery_reasons:
                delivery_reasons = [
                    "NO_FEASIBLE_VEHICLE_OR_DRIVER"
                ]

            unassigned_details.append({
                "delivery_id": delivery.delivery_id,
                "reasons": delivery_reasons
            })

        # 16. Save database changes
        db.commit()

        assigned_count = len(deliveries) - len(remaining)

        return {
            "assigned": assigned_count,
            "unserved": len(remaining),
            "routes": route_results,
            "unassigned_details": unassigned_details
        }

    except Exception:
        db.rollback()
        raise
