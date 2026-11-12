from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey,
    UniqueConstraint, Text
)
from sqlalchemy.orm import relationship
from backend.database import Base

class CustomerSite(Base):
    __tablename__ = "customer_sites"
    site_id = Column(String(30), primary_key=True)
    site_name = Column(String(120), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String(60), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class CustomerOrder(Base):
    __tablename__ = "orders"
    order_id = Column(String(30), primary_key=True)
    site_id = Column(String(30), ForeignKey("customer_sites.site_id"), nullable=False)
    order_date = Column(Date, nullable=False)
    priority = Column(String(15), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)

class Vehicle(Base):
    __tablename__ = "vehicles"
    vehicle_id = Column(String(20), primary_key=True)
    vehicle_type = Column(String(30), nullable=False)
    registration_no = Column(String(30), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    restricted_region = Column(String(60), nullable=True)

class VehicleCapacity(Base):
    __tablename__ = "vehicle_capacities"
    capacity_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    max_weight_kg = Column(Float, nullable=False)
    max_volume_m3 = Column(Float, nullable=False)
    max_stops = Column(Integer, nullable=False)

class Driver(Base):
    __tablename__ = "drivers"
    driver_id = Column(String(20), primary_key=True)
    driver_name = Column(String(120), nullable=False)
    license_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class Shift(Base):
    __tablename__ = "shifts"
    shift_id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(20), ForeignKey("drivers.driver_id"), nullable=False)
    shift_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

class Delivery(Base):
    __tablename__ = "deliveries"
    delivery_id = Column(String(30), primary_key=True)
    order_id = Column(String(30), ForeignKey("orders.order_id"), nullable=False)
    site_id = Column(String(30), ForeignKey("customer_sites.site_id"), nullable=False)
    demand_weight_kg = Column(Float, nullable=False)
    demand_volume_m3 = Column(Float, nullable=False)
    service_minutes = Column(Integer, nullable=False)
    requested_date = Column(Date, nullable=False)
    priority = Column(String(15), nullable=False)
    status = Column(String(20), nullable=False)
    issue_type = Column(String(60), nullable=True)

class TimeWindow(Base):
    __tablename__ = "time_windows"
    time_window_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_id = Column(String(30), ForeignKey("deliveries.delivery_id"), nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    __table_args__ = (UniqueConstraint("delivery_id", name="uq_timewindow_delivery"),)

class TravelTimeMatrix(Base):
    __tablename__ = "travel_time_matrix"
    matrix_id = Column(Integer, primary_key=True, autoincrement=True)
    from_site_id = Column(String(30), ForeignKey("customer_sites.site_id"), nullable=False)
    to_site_id = Column(String(30), ForeignKey("customer_sites.site_id"), nullable=False)
    scenario_date = Column(Date, nullable=False)
    scenario = Column(String(20), nullable=False)
    distance_km = Column(Float, nullable=False)
    travel_minutes = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("from_site_id", "to_site_id", "scenario_date", "scenario",
                                      name="uq_travel_pair_day_scenario"),)

class Route(Base):
    __tablename__ = "routes"
    route_id = Column(String(30), primary_key=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    driver_id = Column(String(20), ForeignKey("drivers.driver_id"), nullable=False)
    route_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    planned_distance_km = Column(Float, default=0, nullable=False)
    planned_duration_minutes = Column(Integer, default=0, nullable=False)

class RouteStop(Base):
    __tablename__ = "route_stops"
    stop_id = Column(String(60), primary_key=True)
    route_id = Column(String(30), ForeignKey("routes.route_id"), nullable=False)
    delivery_id = Column(String(30), ForeignKey("deliveries.delivery_id"), nullable=False)
    sequence_no = Column(Integer, nullable=False)
    planned_arrival = Column(DateTime, nullable=False)
    planned_departure = Column(DateTime, nullable=False)
    actual_arrival = Column(DateTime, nullable=True)
    actual_departure = Column(DateTime, nullable=True)
    stop_status = Column(String(20), nullable=False)
    __table_args__ = (UniqueConstraint("route_id", "sequence_no", name="uq_route_sequence"),)

class DeliveryOutcome(Base):
    __tablename__ = "delivery_outcomes"
    outcome_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_id = Column(String(30), ForeignKey("deliveries.delivery_id"), nullable=False)
    outcome_time = Column(DateTime, nullable=False)
    outcome = Column(String(20), nullable=False)
    reason_code = Column(String(60), nullable=True)
    ground_truth_label = Column(String(30), nullable=True)

class EventHistory(Base):
    __tablename__ = "event_history"
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(60), nullable=False)
    event_type = Column(String(60), nullable=False)
    event_time = Column(DateTime, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
