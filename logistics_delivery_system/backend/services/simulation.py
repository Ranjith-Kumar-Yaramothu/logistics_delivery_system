
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models import (
    Route,
    RouteStop,
    Delivery,
    DeliveryOutcome,
    EventHistory
)


def simulate_route(db: Session, route_id: str, seed: int = 20261022):

    try:
        route = db.query(Route).filter_by(route_id=route_id).first()

        if not route:
            return {"error": "Route not found"}

        stops = (
            db.query(RouteStop)
            .filter_by(route_id=route_id)
            .order_by(RouteStop.sequence_no)
            .all()
        )

        if not stops:
            return {"message": "No stops found for this route"}

        results = []

        for stop in stops:

            actual_arrival = (
                stop.planned_arrival
                + timedelta(minutes=(stop.sequence_no % 4) * 5)
            )

            actual_departure = (
                actual_arrival
                + (stop.planned_departure - stop.planned_arrival)
            )

            old_stop_status = stop.stop_status

            stop.actual_arrival = actual_arrival
            stop.actual_departure = actual_departure
            stop.stop_status = "COMPLETED"

            delivery = (
                db.query(Delivery)
                .filter_by(delivery_id=stop.delivery_id)
                .first()
            )

            if not delivery:
                raise ValueError(
                    f"Delivery not found: {stop.delivery_id}"
                )

            old_delivery_status = delivery.status
            delivery.status = "DELIVERED"

            outcome = (
                db.query(DeliveryOutcome)
                .filter_by(delivery_id=stop.delivery_id)
                .first()
            )

            if outcome:
                outcome.outcome_time = actual_departure
                outcome.outcome = "DELIVERED"
                outcome.reason_code = None
                outcome.ground_truth_label = "RULE_BASED_SIMULATION"
            else:
                outcome = DeliveryOutcome(
                    delivery_id=stop.delivery_id,
                    outcome_time=actual_departure,
                    outcome="DELIVERED",
                    reason_code=None,
                    ground_truth_label="RULE_BASED_SIMULATION"
                )
                db.add(outcome)

            if old_stop_status != "COMPLETED":
                db.add(
                    EventHistory(
                        entity_type="RouteStop",
                        entity_id=stop.stop_id,
                        event_type="STOP_COMPLETED",
                        event_time=datetime.now(),
                        old_value=old_stop_status,
                        new_value="COMPLETED",
                        details="Simulated actual arrival/departure"
                    )
                )

            if old_delivery_status != "DELIVERED":
                db.add(
                    EventHistory(
                        entity_type="Delivery",
                        entity_id=delivery.delivery_id,
                        event_type="DELIVERY_STATUS_CHANGED",
                        event_time=datetime.now(),
                        old_value=old_delivery_status,
                        new_value="DELIVERED",
                        details="Delivery completed through route simulation"
                    )
                )

            results.append({
                "stop_id": stop.stop_id,
                "delivery_id": stop.delivery_id,
                "delivery_status": delivery.status,
                "outcome": "DELIVERED",
                "arrival": actual_arrival.isoformat(),
                "departure": actual_departure.isoformat()
            })

        route.status = "COMPLETED"

        db.commit()

        return results

    except Exception:
        db.rollback()
        raise
