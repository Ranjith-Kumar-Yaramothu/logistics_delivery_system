# Data dictionary

| Entity | Primary key | Important fields | Validation |
|---|---|---|---|
| CustomerSite | site_id | name, address, latitude, longitude, region | coordinates within configured region for baseline |
| Order | order_id | site_id, order_date, priority, status | site FK; priority LOW/NORMAL/HIGH |
| Delivery | delivery_id | order_id, site_id, weight, volume, service_minutes | positive demand; order/site FKs |
| Vehicle | vehicle_id | type, registration_no, active | registration unique |
| VehicleCapacity | capacity_id | vehicle_id, effective dates, weight, volume, stops | positive capacities; effective_to >= effective_from |
| Driver | driver_id | name, license_type, active | unique immutable driver ID |
| Shift | shift_id | driver_id, start_time, end_time | end after start |
| TravelTimeMatrix | matrix_id | from/to site, date, scenario, distance, minutes | positive distance/time; unique directed pair/date/scenario |
| TimeWindow | time_window_id | delivery_id, window_start, window_end | end after start; one current window per delivery in starter schema |
| Route | route_id | vehicle, driver, date, status, distance, duration | valid vehicle/driver FKs |
| RouteStop | stop_id | route, delivery, sequence, planned/actual times | unique route sequence; delivery FK |
| DeliveryOutcome | outcome_id | delivery, time, outcome, reason_code | failed outcomes require reason code |
| EventHistory | event_id | entity, event, time, old/new values | append-only history |

## Enumerations
- Priority: LOW, NORMAL, HIGH
- Delivery status: PENDING, ASSIGNED, UNASSERVED, DELIVERED, FAILED
- Route status: PLANNED, IN_PROGRESS, COMPLETED, EXCEPTION
- Outcome: DELIVERED, FAILED
