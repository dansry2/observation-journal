from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.observation import ObservationDay, HourlyWeather, EquipmentLog, ObservationDuty
from ..models.error_log import ErrorLogDay, ErrorLogEntry

router = APIRouter(prefix="/api/v1", tags=["external-api"])

@router.get("/observations")
def api_observations(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db)):
    obs_list = db.query(ObservationDay).filter(
        ObservationDay.date >= date_from, 
        ObservationDay.date <= date_to, 
        ObservationDay.is_active == True
    ).order_by(ObservationDay.date).all()
    
    result = []
    for obs in obs_list:
        weather = db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == obs.id).all()
        equipment = db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == obs.id).all()
        duty = db.query(ObservationDuty).filter(ObservationDuty.observation_day_id == obs.id).all()
        
        result.append({
            "date": str(obs.date), 
            "weather": [{"hour": w.hour, "temperature": w.temperature, "weather_type_id": w.weather_type_id} for w in weather], 
            "equipment": [{"range_id": e.equipment_range_id, "time_start": e.time_start, "time_stop": e.time_stop, "note": e.note} for e in equipment], 
            "duty": []
        })
    return result

@router.get("/errors")
def api_errors(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db)):
    entries = db.query(ErrorLogDay).filter(
        ErrorLogDay.date >= date_from, 
        ErrorLogDay.date <= date_to, 
        ErrorLogDay.is_active == True
    ).order_by(ErrorLogDay.date, ErrorLogDay.grid_id).all()
    
    result = {}
    for day in entries:
        ents = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
        key = f"{day.date}_{day.grid_id}"
        if key not in result:
            result[key] = {"date": str(day.date), "grid_id": day.grid_id, "entries": [], "is_ok": day.is_ok}
        for e in ents:
            # Если антенна исправна и есть end_time — берём broken_until из даты записи
            broken_until = getattr(e, 'broken_until', None)
            if e.is_ok and e.end_time and not broken_until:
                broken_until = str(day.date)
            
            result[key]["entries"].append({
                "antenna": e.antenna_code, 
                "error": e.error_description, 
                "is_ok": e.is_ok, 
                "start_time": e.start_time, 
                "end_time": e.end_time,
                "broken_since": getattr(e, 'broken_since', None),
                "broken_until": broken_until
            })
    return list(result.values())

@router.get("/references")
def api_references():
    from ..references import GRID_TO_NAME, WEATHER_TYPES, ANTENNAS
    return {
        "weather_types": [{"id": k, "name": v} for k, v in WEATHER_TYPES.items()],
        "antennas": [{"code": a, "frequency_range_id": None} for a in ANTENNAS],
        "equipment_ranges": [{"id": k, "name": v} for k, v in GRID_TO_NAME.items()],
        "uv_slots": [],
        "uv_statuses": [],
        "frequency_ranges": []
    }
