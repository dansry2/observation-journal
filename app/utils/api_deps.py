from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from ..database import UsersSessionLocal
from ..models.api_key import ApiKey

api_key_header = APIKeyHeader(name="X-API-Key")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_api_key(api_key: str = Security(api_key_header)):
    db = UsersSessionLocal()
    try:
        keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()
        for k in keys:
            if pwd_context.verify(api_key, k.key_hash):
                return k
        raise HTTPException(status_code=403, detail="Неверный API-ключ")
    finally:
        db.close()
