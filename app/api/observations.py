from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.observation import ObservationDay, HourlyWeather, EquipmentLog, ObservationDuty
from ..database import get_user_name
from ..models.user import User
from ..schemas.observation import ObservationCreate, ObservationResponse, ObservationBrief, ObservationHistory
from ..utils.deps import get_current_user, get_optional_user, get_active_user, get_optional_user


router = APIRouter(prefix="/observations", tags=["journal"])
@router.post("/check-conflicts", response_model=None)
def check_conflicts(data: ObservationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active = db.query(ObservationDay).filter(ObservationDay.date == data.date, ObservationDay.is_active == True).first()
    if not active:
        return {"conflict": False}
    
    old_temp = {}
    old_weather_type = {}
    for w in db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == active.id).all():
        if w.temperature is not None:
            old_temp[w.hour] = w.temperature
        if w.weather_type_id is not None:
            old_weather_type[w.hour] = w.weather_type_id
    
    old_start = {}
    old_stop = {}
    for e in db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == active.id).all():
        if e.time_start:
            old_start[e.equipment_range_id] = e.time_start
        if e.time_stop:
            old_stop[e.equipment_range_id] = e.time_stop
    
    for w in (data.weather or []):
        # Конфликт только если в базе было значение И новое значение отличается
        if w.hour in old_temp and w.temperature is not None and w.temperature != old_temp[w.hour]:
            return {"conflict": True}
        if w.hour in old_weather_type and w.weather_type_id is not None and w.weather_type_id != old_weather_type[w.hour]:
            return {"conflict": True}
    
    for e in (data.equipment or []):
        if e.equipment_range_id in old_start and e.time_start and e.time_start != old_start[e.equipment_range_id]:
            return {"conflict": True}
        if e.equipment_range_id in old_stop and e.time_stop and e.time_stop != old_stop[e.equipment_range_id]:
            return {"conflict": True}
    
    return {"conflict": False}

    old_weather = {}
    for w in db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == active.id).all():
        if w.temperature is not None or w.weather_type_id is not None:
            old_weather[w.hour] = True
    
    old_equipment = {}
    for e in db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == active.id).all():
        if e.time_start or e.time_stop:
            old_equipment[e.equipment_range_id] = True
    
    for w in (data.weather or []):
        if w.hour in old_weather and w.temperature is not None:
            return {"conflict": True}
        if w.hour in old_weather and w.weather_type_id is not None:
            return {"conflict": True}
    
    for e in (data.equipment or []):
        if e.equipment_range_id in old_equipment and e.time_start:
            return {"conflict": True}
        if e.equipment_range_id in old_equipment and e.time_stop:
            return {"conflict": True}
    
    return {"conflict": False}


def _merge_and_create(data: ObservationCreate, db: Session, current_user: User):
    active = db.query(ObservationDay).filter(
        ObservationDay.date == data.date,
        ObservationDay.is_active == True
    ).first()

    new_version = 1
    old_weather = {}
    old_equipment = {}
    old_duty = set()

    if active:
        new_version = active.version + 1
        active.is_active = False
        for w in db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == active.id).all():
            old_weather[w.hour] = (w.temperature, w.weather_type_id)
        for e in db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == active.id).all():
            old_equipment[e.equipment_range_id] = (e.time_start, e.time_stop, e.note)
        for d in db.query(ObservationDuty).filter(ObservationDuty.observation_day_id == active.id).all():
            old_duty.add(d.user_id)
        db.flush()

    obs = ObservationDay(
        date=data.date,
        version=new_version,
        is_active=True,
        change_note=data.change_note,
        duty_custom=data.duty_custom,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(obs)
    db.flush()

    new_weather = {}
    for w in (data.weather or []):
        new_weather[w.hour] = (w.temperature, w.weather_type_id)

    all_hours = set(list(old_weather.keys()) + list(new_weather.keys()))
    for hour in sorted(all_hours):
        temp, weather_id = new_weather.get(hour, old_weather.get(hour, (None, None)))
        db.add(HourlyWeather(observation_day_id=obs.id, hour=hour, temperature=temp, weather_type_id=weather_id))

    new_equipment = {}
    for e in (data.equipment or []):
        new_equipment[e.equipment_range_id] = (e.time_start, e.time_stop, e.note)

    all_ranges = set(list(old_equipment.keys()) + list(new_equipment.keys()))
    for rid in all_ranges:
        start, stop, note = new_equipment.get(rid, old_equipment.get(rid, (None, None, None)))
        db.add(EquipmentLog(observation_day_id=obs.id, equipment_range_id=rid, time_start=start, time_stop=stop, note=note))

    merged_duty = old_duty | set(data.duty_user_ids or [])
    for uid in merged_duty:
        db.add(ObservationDuty(observation_day_id=obs.id, user_id=uid))

    db.commit()
    db.refresh(obs)
    return obs

@router.post("/", response_model=ObservationResponse)
def create_or_update_observation(
    data: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    obs = _merge_and_create(data, db, current_user)
    return _build_response(obs, db)

@router.get("/{obs_date}", response_model=ObservationResponse)
def get_observation(
    obs_date: date,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    obs = db.query(ObservationDay).filter(
        ObservationDay.date == obs_date,
        ObservationDay.is_active == True
    ).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Not found")
    return _build_response(obs, db)

@router.get("/{obs_date}/history", response_model=ObservationHistory)
def get_history(
    obs_date: date,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    versions = db.query(ObservationDay).filter(
        ObservationDay.date == obs_date
    ).order_by(ObservationDay.version.desc()).all()

    if not versions:
        raise HTTPException(status_code=404, detail="Not found")

    result = []
    for v in versions:
        creator_name = get_user_name(v.created_by)
        updater_name = get_user_name(v.updated_by)
        result.append(ObservationBrief(
            id=v.id,
            date=v.date,
            version=v.version,
            is_active=v.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(v.created_at),
            change_note=v.change_note
        ))
    return ObservationHistory(date=obs_date, versions=result)

@router.get("/", response_model=list[ObservationBrief])
def list_observations(
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    obs_list = db.query(ObservationDay).filter(
        ObservationDay.is_active == True
    ).order_by(ObservationDay.date.desc()).limit(100).all()

    result = []
    for obs in obs_list:
        creator_name = get_user_name(obs.created_by)
        updater_name = get_user_name(obs.updated_by)
        result.append(ObservationBrief(
            id=obs.id,
            date=obs.date,
            version=obs.version,
            is_active=obs.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(obs.created_at),
            change_note=obs.change_note
        ))
    return result

def _build_response(obs: ObservationDay, db: Session) -> dict:
    weather = db.query(HourlyWeather).filter(HourlyWeather.observation_day_id == obs.id).all()
    equipment = db.query(EquipmentLog).filter(EquipmentLog.observation_day_id == obs.id).all()
    duty = db.query(ObservationDuty).filter(ObservationDuty.observation_day_id == obs.id).all()
    creator_name = get_user_name(obs.created_by)
    updater_name = get_user_name(obs.updated_by)

    return {
        "id": obs.id,
        "date": obs.date,
        "version": obs.version,
        "weather": [{"hour": w.hour, "temperature": w.temperature, "weather_type_id": w.weather_type_id} for w in weather],
        "equipment": [{"equipment_range_id": e.equipment_range_id, "time_start": e.time_start, "time_stop": e.time_stop, "note": e.note} for e in equipment],
        "duty_user_ids": [d.user_id for d in duty],
        "created_by": creator_name,
        "updated_by": updater_name,
        "created_at": str(obs.created_at) if obs.created_at else None,
        "updated_at": str(obs.updated_at) if obs.updated_at else None,
        "change_note": obs.change_note,
        "duty_custom": obs.duty_custom or ""
    }
