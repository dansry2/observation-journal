import secrets
from app.database import SessionLocal
from app.models.user import User, InvitationKey
from app.utils.security import get_password_hash
from sqlalchemy.sql import func

db = SessionLocal()

admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin"),
        full_name="Администратор",
        role="admin"
    )
    db.add(admin)
    db.flush()
    print("Админ создан: admin / admin")
else:
    print("Админ уже существует")

key_code = secrets.token_hex(4).upper()
key = InvitationKey(
    key_code=key_code,
    created_by=admin.id,
    created_at=func.now()
)
db.add(key)
db.commit()

print(f"Ключ приглашения: {key_code}")
db.close()
