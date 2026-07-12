from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.error_log import ErrorLogDay, ErrorLogEntry
from ..models.user import User
from ..schemas.error_log import ErrorLogCreate, ErrorLogResponse, ErrorLogBrief, ErrorLogHistory
from ..utils.deps import get_current_user

router = APIRouter(prefix="/errors", tags=["errors"])

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
            old_entries[e.antenna_code] = e.error_description
        db.flush()

    day = ErrorLogDay(
        date=data.date, grid_id=data.grid_id, version=new_version,
        is_active=True, change_note=data.change_note,
        created_by=current_user.id, updated_by=current_user.id
    )
    db.add(day)
    db.flush()

    new_entries = {}
    for e in (data.entries or []):
        new_entries[e.antenna_code] = e.error_description

    all_antennas = set(list(old_entries.keys()) + list(new_entries.keys()))
    for code in all_antennas:
        desc = new_entries.get(code, old_entries.get(code))
        db.add(ErrorLogEntry(error_log_day_id=day.id, antenna_code=code, error_description=desc))

    db.commit()
    db.refresh(day)
    return day

@router.post("/", response_model=ErrorLogResponse)
def create_or_update(data: ErrorLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = _merge_and_create(data, db, current_user)
    return _build_response(day, db)

@router.get("/{obs_date}/{grid_id}", response_model=ErrorLogResponse)
def get_active(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.is_active == True
    ).first()
    if not day:
        raise HTTPException(status_code=404, detail="Not found")
    return _build_response(day, db)

@router.get("/{obs_date}/{grid_id}/history", response_model=ErrorLogHistory)
def get_history(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    versions = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id
    ).order_by(ErrorLogDay.version.desc()).all()

    if not versions:
        raise HTTPException(status_code=404, detail="Not found")

    result = []
    for v in versions:
        creator = db.query(User).filter(User.id == v.created_by).first()
        updater = db.query(User).filter(User.id == v.updated_by).first()
        result.append(ErrorLogBrief(
            id=v.id, date=v.date, grid_id=v.grid_id, version=v.version,
            is_active=v.is_active,
            created_by=creator.full_name if creator else None,
            updated_by=updater.full_name if updater else None,
            created_at=str(v.created_at), change_note=v.change_note
        ))
    return ErrorLogHistory(date=obs_date, grid_id=grid_id, versions=result)

def _build_response(day, db):
    entries = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
    creator = db.query(User).filter(User.id == day.created_by).first()
    updater = db.query(User).filter(User.id == day.updated_by).first()
    return {
        "id": day.id, "date": day.date, "grid_id": day.grid_id, "version": day.version,
        "entries": [{"antenna_code": e.antenna_code, "error_description": e.error_description} for e in entries],
        "created_by": creator.full_name if creator else None,
        "updated_by": updater.full_name if updater else None,
        "created_at": str(day.created_at), "change_note": day.change_note
    }
