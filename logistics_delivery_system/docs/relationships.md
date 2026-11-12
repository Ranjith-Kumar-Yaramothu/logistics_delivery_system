# Entity relationships and cardinality

- CustomerSite 1:N Order
- CustomerSite 1:N Delivery
- Order 1:N Delivery (the generator creates one delivery per order; schema permits multiple)
- Vehicle 1:N VehicleCapacity (effective-dated capacity history)
- Driver 1:N Shift
- Vehicle 1:N Route over time
- Driver 1:N Route over time
- Delivery 1:0..1 TimeWindow in this starter implementation
- Delivery 1:N RouteStop across planning history; enforce at most one active assignment in application logic
- Route 1:N RouteStop
- Delivery 1:N DeliveryOutcome (attempt history)
- Any entity 1:N EventHistory

Vehicle and Delivery are operationally many-to-many over time through RouteStop, with Route as the assignment grouping. Driver and Route are also many-to-many over time if driver changes are recorded as new route assignments; this starter uses one driver per route.

Effective dates are stored on VehicleCapacity. Events and outcomes are append-only; status columns are current snapshots, not substitutes for event history.
