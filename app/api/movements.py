from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.movement import MovementDay, MovementEntry
from ..database import get_user_name
from ..models.user import User
from ..schemas.movement import MovementCreate, MovementResponse, MovementBrief, MovementHistory
from ..utils.deps import get_current_user, get_optional_user, get_optional_user, get_active_user, get_optional_user

router = APIRouter(prefix="/movements", tags=["movements"])

def _merge_and_create(data: MovementCreate, db: Session, current_user: User):
    active = db.query(MovementDay).filter(
        MovementDay.date == data.date, MovementDay.is_active == True
    ).first()

    new_version = 1
    old_movements = []

    if active:
        new_version = active.version + 1
        active.is_active = False
        for m in db.query(MovementEntry).filter(MovementEntry.movement_day_id == active.id).all():
            old_movements.append({
                "component_name": m.component_name,
                "from_antenna": m.from_antenna,
                "to_antenna": m.to_antenna,
                "note": m.note
            })
        db.flush()

    day = MovementDay(
        date=data.date, version=new_version, is_active=True,
        change_note=data.change_note,
        created_by=current_user.id, updated_by=current_user.id
    )
    db.add(day)
    db.flush()

    # Новые + старые (если не перезаписали)
    all_movements = {m["component_name"] + str(m.get("from_antenna","")) + str(m.get("to_antenna","")): m for m in old_movements}
    for m in (data.movements or []):
        key = m.component_name + str(m.from_antenna or "") + str(m.to_antenna or "")
        all_movements[key] = {"component_name": m.component_name, "from_antenna": m.from_antenna, "to_antenna": m.to_antenna, "note": m.note}

    for m in all_movements.values():
        db.add(MovementEntry(movement_day_id=day.id, **m))

    db.commit()
    db.refresh(day)
    return day

@router.post("/", response_model=MovementResponse)
def create_or_update(data: MovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    day = _merge_and_create(data, db, current_user)
    return _build_response(day, db)

@router.get("/{obs_date}", response_model=MovementResponse)
def get_active(obs_date: date, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    day = db.query(MovementDay).filter(MovementDay.date == obs_date, MovementDay.is_active == True).first()
    if not day:
        raise HTTPException(status_code=404, detail="Not found")
    return _build_response(day, db)

@router.get("/{obs_date}/history", response_model=MovementHistory)
def get_history(obs_date: date, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    versions = db.query(MovementDay).filter(MovementDay.date == obs_date).order_by(MovementDay.version.desc()).all()
    if not versions:
        raise HTTPException(status_code=404, detail="Not found")
    result = []
    for v in versions:
        creator_name = get_user_name(v.created_by)
        updater_name = get_user_name(v.updated_by)
        result.append(MovementBrief(
            id=v.id, date=v.date, version=v.version, is_active=v.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(v.created_at), change_note=v.change_note
        ))
    return MovementHistory(date=obs_date, versions=result)

def _build_response(day, db):
    entries = db.query(MovementEntry).filter(MovementEntry.movement_day_id == day.id).all()
    creator_name = get_user_name(day.created_by)
    updater_name = get_user_name(day.updated_by)
    return {
        "id": day.id, "date": day.date, "version": day.version,
        "movements": [{"component_name": e.component_name, "from_antenna": e.from_antenna, "to_antenna": e.to_antenna, "note": e.note} for e in entries],
        "created_by": creator_name,
        "updated_by": updater_name,
        "created_at": str(day.created_at), "change_note": day.change_note
    }
