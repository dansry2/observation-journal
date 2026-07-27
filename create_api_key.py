import sys
sys.path.insert(0, '.')
import secrets
from app.database import UsersSessionLocal as SessionLocal
from app.models.api_key import ApiKey
from app.utils.security import get_password_hash

db = SessionLocal()

raw_key = "ak_" + secrets.token_hex(16)
hashed = get_password_hash(raw_key)

key = ApiKey(key_hash=hashed, name="Ключ для отчётов", created_by=0)
db.add(key)
db.commit()

print(f"API-ключ создан: {raw_key}")
print("Сохраните его! Хэш в базе, исходный ключ больше не покажется.")
db.close()
