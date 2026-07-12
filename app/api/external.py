from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.observation import ObservationDay, HourlyWeather, EquipmentLog, ObservationDuty
from ..models.uv_plane import UVPlaneDay, UVPlaneEntry
from ..models.error_log import ErrorLogDay, ErrorLogEntry
from ..models.other_tables import ComponentMovement, AntennaNote, DailyNote
from ..models.reference import Antenna, WeatherType, EquipmentRange, UVSlot, UVStatus, FrequencyRange
from ..models.user import User
from ..utils.api_deps import get_api_key
from ..models.api_key import ApiKey

router = APIRouter(prefix="/api/v1", tags=["external-api"])

@router.get("/observations")
def api_observations(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    obs_list = db.query(ObservationDay).filter(ObservationDay.date >= date_from, ObservationDay.date <= date_to, ObservationDay.is_active == True).order_by(ObservationDay.date).all()
    result = []
    for obs in obs_list:
        weather = db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == obs.id).all()
        equipment = db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == obs.id).all()
        duty = db.query(ObservationDuty).filter(ObservationDuty.observation_day_id == obs.id).all()
        duty_users = []
        for d in duty:
            u = db.query(User).filter(User.id == d.user_id).first()
            if u:
                duty_users.append(u.full_name)
        result.append({"date": str(obs.date), "weather": [{"hour": w.hour, "temperature": w.temperature, "weather_type_id": w.weather_type_id} for w in weather], "equipment": [{"range_id": e.equipment_range_id, "time_start": e.time_start, "time_stop": e.time_stop, "note": e.note} for e in equipment], "duty": duty_users})
    return result

@router.get("/uv-plane")
def api_uv_plane(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    entries = db.query(UVPlaneDay).filter(UVPlaneDay.date >= date_from, UVPlaneDay.date <= date_to, UVPlaneDay.is_active == True).order_by(UVPlaneDay.date, UVPlaneDay.slot_id).all()
    result = {}
    for day in entries:
        ents = db.query(UVPlaneEntry).filter(UVPlaneEntry.uv_plane_day_id == day.id).all()
        key = f"{day.date}_{day.slot_id}"
        if key not in result:
            result[key] = {"date": str(day.date), "slot_id": day.slot_id, "entries": []}
        for e in ents:
            result[key]["entries"].append({"antenna": e.antenna_code, "status": e.status})
    return list(result.values())

@router.get("/errors")
def api_errors(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    entries = db.query(ErrorLogDay).filter(ErrorLogDay.date >= date_from, ErrorLogDay.date <= date_to, ErrorLogDay.is_active == True).order_by(ErrorLogDay.date, ErrorLogDay.grid_id).all()
    result = {}
    for day in entries:
        ents = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
        key = f"{day.date}_{day.grid_id}"
        if key not in result:
            result[key] = {"date": str(day.date), "grid_id": day.grid_id, "entries": []}
        for e in ents:
            result[key]["entries"].append({"antenna": e.antenna_code, "error": e.error_description})
    return list(result.values())

@router.get("/movements")
def api_movements(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    entries = db.query(ComponentMovement).filter(ComponentMovement.date >= date_from, ComponentMovement.date <= date_to).order_by(ComponentMovement.date).all()
    return [{"date": str(e.date), "component": e.component_name, "from_antenna": e.from_antenna, "to_antenna": e.to_antenna, "note": e.note} for e in entries]

@router.get("/antenna-notes")
def api_antenna_notes(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    entries = db.query(AntennaNote).filter(AntennaNote.date >= date_from, AntennaNote.date <= date_to).order_by(AntennaNote.date).all()
    result = {}
    for e in entries:
        key = str(e.date)
        if key not in result:
            result[key] = {"date": str(e.date), "notes": []}
        result[key]["notes"].append({"antenna": e.antenna_code, "note": e.note})
    return list(result.values())

@router.get("/notes")
def api_notes(date_from: date = Query(...), date_to: date = Query(...), db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    entries = db.query(DailyNote).filter(DailyNote.date >= date_from, DailyNote.date <= date_to).order_by(DailyNote.date).all()
    return [{"date": str(e.date), "title": e.title, "description": e.description} for e in entries]

@router.get("/references")
def api_references(db: Session = Depends(get_db), api_key: ApiKey = Depends(get_api_key)):
    return {
        "weather_types": [{"id": w.id, "name": w.name} for w in db.query(WeatherType).all()],
        "antennas": [{"code": a.code, "frequency_range_id": a.frequency_range_id} for a in db.query(Antenna).order_by(Antenna.code).all()],
        "equipment_ranges": [{"id": r.id, "name": r.name} for r in db.query(EquipmentRange).all()],
        "uv_slots": [{"id": s.id, "time": s.slot_time} for s in db.query(UVSlot).all()],
        "uv_statuses": [{"id": s.id, "text": s.text} for s in db.query(UVStatus).all()],
        "frequency_ranges": [{"id": f.id, "name": f.name} for f in db.query(FrequencyRange).all()]
    }
