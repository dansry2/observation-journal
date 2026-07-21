import secrets
from app.database import UsersSessionLocal as SessionLocal
from app.models.user import User, InvitationKey
from app.utils.security import get_password_hash
from app.config import settings
from sqlalchemy.sql import func

db = SessionLocal()

admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
if not admin:
    admin = User(
        username=settings.ADMIN_USERNAME,
        password_hash=get_password_hash(settings.ADMIN_PASSWORD),
        full_name="Администратор",
        role="admin"
    )
    db.add(admin)
    db.flush()
    print(f"Админ создан: {settings.ADMIN_USERNAME}")
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
