from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.uv_plane import UVPlaneDay, UVPlaneEntry
from ..database import get_user_name
from ..models.user import User
from ..schemas.uv_plane import UVPlaneCreate, UVPlaneResponse, UVPlaneBrief, UVPlaneHistory
from ..utils.deps import get_current_user, get_optional_user, get_optional_user, get_active_user, get_optional_user

router = APIRouter(prefix="/uv", tags=["uv-plane"])
@router.post("/check-conflicts", response_model=None)
def check_conflicts(data: UVPlaneCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    active = db.query(UVPlaneDay).filter(
        UVPlaneDay.date == data.date, UVPlaneDay.slot_id == data.slot_id, UVPlaneDay.is_active == True
    ).first()
    if not active:
        return {"conflict": False}
    
    old_statuses = {}
    for e in db.query(UVPlaneEntry).filter(UVPlaneEntry.uv_plane_day_id == active.id).all():
        if e.status is not None:
            old_statuses[e.antenna_code] = e.status
    
    for e in (data.entries or []):
        if e.antenna_code in old_statuses and e.status is not None and e.status != old_statuses[e.antenna_code]:
            return {"conflict": True}
    
    return {"conflict": False}


def _merge_and_create(data: UVPlaneCreate, db: Session, current_user: User):
    active = db.query(UVPlaneDay).filter(
        UVPlaneDay.date == data.date,
        UVPlaneDay.slot_id == data.slot_id,
        UVPlaneDay.is_active == True
    ).first()

    new_version = 1
    old_entries = {}

    if active:
        new_version = active.version + 1
        active.is_active = False
        for e in db.query(UVPlaneEntry).filter(UVPlaneEntry.uv_plane_day_id == active.id).all():
            old_entries[e.antenna_code] = e.status
        db.flush()

    day = UVPlaneDay(
        date=data.date,
        slot_id=data.slot_id,
        version=new_version,
        is_active=True,
        change_note=data.change_note,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(day)
    db.flush()

    new_entries = {}
    for e in (data.entries or []):
        new_entries[e.antenna_code] = e.status

    all_antennas = set(list(old_entries.keys()) + list(new_entries.keys()))
    for code in all_antennas:
        status = new_entries.get(code, old_entries.get(code))
        db.add(UVPlaneEntry(uv_plane_day_id=day.id, antenna_code=code, status=status))

    db.commit()
    db.refresh(day)
    return day

@router.post("/", response_model=UVPlaneResponse)
def create_or_update(data: UVPlaneCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    day = _merge_and_create(data, db, current_user)
    return _build_response(day, db)

@router.get("/{obs_date}/{slot_id}", response_model=UVPlaneResponse)
def get_active(obs_date: date, slot_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    day = db.query(UVPlaneDay).filter(
        UVPlaneDay.date == obs_date,
        UVPlaneDay.slot_id == slot_id,
        UVPlaneDay.is_active == True
    ).first()
    if not day:
        raise HTTPException(status_code=404, detail="Not found")
    return _build_response(day, db)

@router.get("/{obs_date}/{slot_id}/history", response_model=UVPlaneHistory)
def get_history(obs_date: date, slot_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    versions = db.query(UVPlaneDay).filter(
        UVPlaneDay.date == obs_date,
        UVPlaneDay.slot_id == slot_id
    ).order_by(UVPlaneDay.version.desc()).all()

    if not versions:
        raise HTTPException(status_code=404, detail="Not found")

    result = []
    for v in versions:
        creator_name = get_user_name(v.created_by)
        updater_name = get_user_name(v.updated_by)
        result.append(UVPlaneBrief(
            id=v.id, date=v.date, slot_id=v.slot_id, version=v.version,
            is_active=v.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(v.created_at), change_note=v.change_note
        ))
    return UVPlaneHistory(date=obs_date, slot_id=slot_id, versions=result)

def _build_response(day: UVPlaneDay, db: Session) -> dict:
    entries = db.query(UVPlaneEntry).filter(UVPlaneEntry.uv_plane_day_id == day.id).all()
    creator_name = get_user_name(day.created_by)
    updater_name = get_user_name(day.updated_by)
    return {
        "id": day.id, "date": day.date, "slot_id": day.slot_id, "version": day.version,
        "entries": [{"antenna_code": e.antenna_code, "status": e.status} for e in entries],
        "created_by": creator_name,
        "updated_by": updater_name,
        "created_at": str(day.created_at), "change_note": day.change_note
    }
