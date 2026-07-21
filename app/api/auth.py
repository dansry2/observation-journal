from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from ..database import get_users_db
from ..models.user import User, InvitationKey
from ..schemas.user import UserCreate, UserLogin, Token
from ..utils.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_users_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    # Все зарегистрированные могут редактировать
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        email=data.email,
        role="user"
    )
    db.add(user)
    db.commit()
    
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return {"access_token": token}

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_users_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return {"access_token": token}
