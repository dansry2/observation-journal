from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_users_db
from ..models.user import User
from ..schemas.user import UserLogin, Token
from ..utils.security import verify_password, create_access_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_users_db)):
    # Админа через переменное окружение
    if data.username == settings.ADMIN_USERNAME and data.password == settings.ADMIN_PASSWORD:
        token = create_access_token({"sub": data.username, "id": 0, "role": "admin"})
        return {"access_token": token}
    
    # Обычные юзеры в базе данных
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return {"access_token": token}
