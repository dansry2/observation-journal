from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.error_log import ErrorLogDay, ErrorLogEntry
from ..database import get_user_name
from ..models.user import User
from ..schemas.error_log import ErrorLogCreate, ErrorLogResponse, ErrorLogBrief, ErrorLogHistory
from ..utils.deps import get_current_user, get_optional_user, get_optional_user, get_active_user, get_optional_user

router = APIRouter(prefix="/errors-grid", tags=["errors"])
@router.post("/check-conflicts", response_model=None)
def check_conflicts(data: ErrorLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    active = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == data.date, ErrorLogDay.grid_id == data.grid_id, ErrorLogDay.is_active == True
    ).first()
    if not active:
        return {"conflict": False}
    
    old_errors = {}
    for e in db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == active.id).all():
        if e.error_description is not None:
            old_errors[e.antenna_code] = e.error_description
    
    for e in (data.entries or []):
        if e.antenna_code in old_errors and e.error_description is not None and e.error_description != old_errors[e.antenna_code]:
            return {"conflict": True}
    
    return {"conflict": False}


def _merge_and_create(data: ErrorLogCreate, db: Session, current_user: User):
    active = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == data.date,
        ErrorLogDay.grid_id == data.grid_id,
        ErrorLogDay.is_active == True
    ).first()

    new_version = 1
    old_entries = {}

    if active:
        new_version = active.version + 1
        active.is_active = False
        for e in db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == active.id).all():
            old_entries[e.antenna_code] = (e.error_description, e.is_ok, e.start_time, e.end_time)
        db.flush()

    day = ErrorLogDay(
        date=data.date, grid_id=data.grid_id, version=new_version,
        is_ok=data.is_ok,
        is_active=True, change_note=data.change_note,
        created_by=current_user.id, updated_by=current_user.id
    )
    db.add(day)
    db.flush()

    new_entries = {}
    for e in (data.entries or []):
        new_entries[e.antenna_code] = (e.error_description, e.is_ok, e.start_time, e.end_time)

    all_antennas = set(list(old_entries.keys()) + list(new_entries.keys()))
    for code in all_antennas:
        if code in new_entries:
            desc, is_ok, start_time, end_time = new_entries[code]
        else:
            desc, is_ok, start_time, end_time = old_entries.get(code, (None, True, None, None))

        # Если антенна починена и есть открытая поломка - закрываем её
        if is_ok and end_time:
            for old_entry in db.query(ErrorLogEntry).join(ErrorLogDay).filter(
                ErrorLogEntry.antenna_code == code,
                ErrorLogEntry.is_ok == False,
                ErrorLogEntry.end_time == None
            ).all():
                # Сохраняем оригинальный broken_since
                original_broken_since = old_entry.broken_since
                # Обновляем исходную запись: добавляем время конца и дату починки
                old_entry.end_time = end_time
                old_entry.broken_until = str(day.date)
                broken_since = original_broken_since or str(day.date)

        broken_until_value = str(day.date) if end_time else None
        db.add(ErrorLogEntry(
            error_log_day_id=day.id, 
            antenna_code=code, 
            error_description=desc, 
            is_ok=is_ok, 
            start_time=start_time, 
            end_time=end_time, 
            broken_since=broken_since if 'broken_since' in locals() else str(day.date),
            broken_until=broken_until_value
        ))

    db.commit()
    db.refresh(day)
    return day

@router.post("/", response_model=ErrorLogResponse)
def create_or_update(data: ErrorLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    day = _merge_and_create(data, db, current_user)
    return _build_response(day, db)

@router.get("/{obs_date}/{grid_id}", response_model=ErrorLogResponse)
def get_active(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    day = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.is_active == True
    ).first()
    
    if not day:
        open_entries = _get_open_entries(db, obs_date, grid_id)
        if not open_entries:
            raise HTTPException(status_code=404, detail="Not found")
        day = ErrorLogDay(date=obs_date, grid_id=grid_id, version=0, is_active=True)
        db.add(day)
        db.flush()
        for e in open_entries:
            broken_date = e.broken_since or str(day.date)
            db.add(ErrorLogEntry(
                error_log_day_id=day.id,
                antenna_code=e.antenna_code,
                error_description=e.error_description,
                is_ok=e.is_ok,
                start_time=e.start_time,
                end_time=e.end_time,
                broken_since=broken_date
            ))
        db.commit()
    
    return _build_response(day, db)

@router.get("/{obs_date}/{grid_id}/history", response_model=ErrorLogHistory)
def get_history(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    versions = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id
    ).order_by(ErrorLogDay.version.desc()).all()

    if not versions:
        raise HTTPException(status_code=404, detail="Not found")

    result = []
    for v in versions:
        creator_name = get_user_name(v.created_by)
        updater_name = get_user_name(v.updated_by)
        result.append(ErrorLogBrief(
            id=v.id, date=v.date, grid_id=v.grid_id, version=v.version,
            is_active=v.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(v.created_at), change_note=v.change_note
        ))
    return ErrorLogHistory(date=obs_date, grid_id=grid_id, versions=result)

def _get_open_entries(db, date, grid_id):
    open_entries = db.query(ErrorLogEntry).join(ErrorLogDay).filter(
        ErrorLogDay.date < date,
        ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.is_active == True,
        ErrorLogEntry.is_ok == False,
        ErrorLogEntry.end_time == None
    ).all()
    return open_entries

def _build_response(day, db):
    entries = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
    open_entries = _get_open_entries(db, day.date, day.grid_id)

    # Для каждой антенны берём последнюю запись
    latest_by_antenna = {}
    for e in list(entries) + list(open_entries):
        if e.antenna_code not in latest_by_antenna or e.id > latest_by_antenna[e.antenna_code].id:
            latest_by_antenna[e.antenna_code] = e
    unique_entries = list(latest_by_antenna.values())

    entries_result = []
    for e in unique_entries:
        entry = {
            "antenna_code": e.antenna_code,
            "error_description": e.error_description,
            "is_ok": e.is_ok,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "broken_since": getattr(e, 'broken_since', None) or str(day.date)
        }
        if e.end_time:
            # Берём дату починки из записи
            entry["broken_until"] = getattr(e, 'broken_until', None) or str(day.date)
        if not e.is_ok:
            entry["broken_since"] = e.broken_since or str(day.date)
        entries_result.append(entry)

    return {
        "id": day.id, "date": day.date, "grid_id": day.grid_id, "version": day.version,
        "entries": entries_result,
        "created_at": str(day.created_at), "change_note": day.change_note,
        "is_ok": day.is_ok
    }

