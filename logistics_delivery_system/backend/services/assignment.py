from sqlalchemy.orm import Session
from backend.models import Delivery, Vehicle, VehicleCapacity

def eligible_vehicles(db: Session, delivery: Delivery):
    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    eligible = []
    for vehicle in vehicles:
        capacity = (db.query(VehicleCapacity)
                    .filter(VehicleCapacity.vehicle_id == vehicle.vehicle_id)
                    .order_by(VehicleCapacity.effective_from.desc()).first())
        if not capacity:
            continue
        if delivery.demand_weight_kg <= capacity.max_weight_kg and delivery.demand_volume_m3 <= capacity.max_volume_m3:
            eligible.append(vehicle)
    return eligible
