from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_users_db
from ..models.user import User
from ..utils.security import get_password_hash
from ..utils.deps import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: str

@router.post("/users")
def create_user(data: CreateUserRequest, db: Session = Depends(get_users_db), current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        role="user"
    )
    db.add(user)
    db.commit()
    return {"message": f"Пользователь {data.username} создан"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_users_db), current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удалён"}
