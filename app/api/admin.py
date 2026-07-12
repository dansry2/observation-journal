from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, InvitationKey
from ..utils.deps import get_current_user
from ..utils.security import get_password_hash
import secrets

router = APIRouter(prefix="/admin/keys", tags=["admin"])

@router.get("/")
def list_keys(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    
    keys = db.query(InvitationKey).order_by(InvitationKey.created_at.desc()).all()
    result = []
    for k in keys:
        creator = db.query(User).filter(User.id == k.created_by).first()
        used = db.query(User).filter(User.id == k.used_by).first()
        result.append({
            "id": k.id,
            "key_code": k.key_code,
            "is_active": k.is_active,
            "created_by": creator.full_name if creator else None,
            "created_at": str(k.created_at),
            "used_by": used.full_name if used else None,
            "used_at": str(k.used_at) if k.used_at else None
        })
    return result

@router.post("/")
def create_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    
    key_code = secrets.token_hex(4).upper()
    key = InvitationKey(key_code=key_code, created_by=current_user.id)
    db.add(key)
    db.commit()
    return {"key_code": key_code, "message": "Ключ создан"}

@router.put("/{key_id}/deactivate")
def deactivate_key(key_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    
    key = db.query(InvitationKey).filter(InvitationKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    key.is_active = False
    db.commit()
    return {"message": "Ключ деактивирован"}
