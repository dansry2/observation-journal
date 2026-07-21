from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.other_tables import ComponentMovement, AntennaNote, DailyNote
from ..database import get_user_name
from ..models.user import User
from ..schemas.other import MovementCreate, MovementResponse, AntennaNoteCreate, AntennaNoteResponse, DailyNoteCreate, DailyNoteResponse
from ..utils.deps import get_current_user, get_optional_user, get_optional_user, get_active_user, get_optional_user

router = APIRouter(tags=["other"])

@router.post("/movements", response_model=MovementResponse)
def create_movements(data: MovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    for m in data.movements:
        db.add(ComponentMovement(date=data.date, component_name=m.component_name, from_antenna=m.from_antenna, to_antenna=m.to_antenna, note=m.note, created_by=current_user.id))
    db.commit()
    return _build_movement_response(data.date, db)

@router.get("/movements/{obs_date}", response_model=MovementResponse)
def get_movements(obs_date: date, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    return _build_movement_response(obs_date, db)

@router.put("/movements/{obs_date}", response_model=MovementResponse)
def update_movements(obs_date: date, data: MovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    db.query(ComponentMovement).filter(ComponentMovement.date == obs_date).delete()
    for m in data.movements:
        db.add(ComponentMovement(date=obs_date, component_name=m.component_name, from_antenna=m.from_antenna, to_antenna=m.to_antenna, note=m.note, created_by=current_user.id))
    db.commit()
    return _build_movement_response(obs_date, db)

def _build_movement_response(obs_date, db):
    entries = db.query(ComponentMovement).filter(ComponentMovement.date == obs_date).all()
    creator_name = get_user_name(entries[0].created_by) if entries else None
    return {"date": obs_date, "movements": [{"component_name": e.component_name, "from_antenna": e.from_antenna, "to_antenna": e.to_antenna, "note": e.note} for e in entries], "created_by": creator_name}

@router.post("/antenna-notes", response_model=AntennaNoteResponse)
def create_antenna_notes(data: AntennaNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    for n in data.notes:
        existing = db.query(AntennaNote).filter(AntennaNote.date == data.date, AntennaNote.antenna_code == n.antenna_code).first()
        if existing:
            existing.note = n.note
            existing.updated_by = current_user.id
        else:
            db.add(AntennaNote(date=data.date, antenna_code=n.antenna_code, note=n.note, created_by=current_user.id, updated_by=current_user.id))
    db.commit()
    return _build_antenna_note_response(data.date, db)

@router.get("/antenna-notes/{obs_date}", response_model=AntennaNoteResponse)
def get_antenna_notes(obs_date: date, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    return _build_antenna_note_response(obs_date, db)

def _build_antenna_note_response(obs_date, db):
    entries = db.query(AntennaNote).filter(AntennaNote.date == obs_date).all()
    creator_name = get_user_name(entries[0].created_by) if entries else None
    updater_name = get_user_name(entries[0].updated_by) if entries else None
    return {"date": obs_date, "notes": [{"antenna_code": e.antenna_code, "note": e.note} for e in entries], "created_by": creator_name, "updated_by": updater_name}

@router.post("/notes", response_model=DailyNoteResponse)
def create_note(data: DailyNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    note = DailyNote(date=data.date, title=data.title, description=data.description, created_by=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "date": note.date, "title": note.title, "description": note.description, "created_by": current_user.full_name, "created_at": str(note.created_at)}

@router.get("/notes/{obs_date}", response_model=list[DailyNoteResponse])
def get_notes(obs_date: date, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    notes = db.query(DailyNote).filter(DailyNote.date == obs_date).all()
    result = []
    for n in notes:
        creator_name = get_user_name(n.created_by)
        result.append({"id": n.id, "date": n.date, "title": n.title, "description": n.description, "created_by": creator_name, "created_at": str(n.created_at)})
    return result

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    note = db.query(DailyNote).filter(DailyNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(note)
    db.commit()
    return {"ok": True}
