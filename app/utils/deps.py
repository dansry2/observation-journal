from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
from ..config import settings
from ..database import get_users_db
from ..models.user import User

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_users_db)
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Не авторизован")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    # Админ — не из базы
    if role == "admin":
        return type('User', (), {
            'id': 0, 'username': username, 'role': 'admin',
            'full_name': 'Администратор'
        })()
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

def get_active_user(current_user = Depends(get_current_user)):
    if current_user.role == "viewer":
        raise HTTPException(status_code=403, detail="Только для чтения")
    return current_user

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_users_db)
):
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except:
        return None
