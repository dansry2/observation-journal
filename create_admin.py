import sys
from app.database import UsersSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash
from app.config import settings
from sqlalchemy.sql import func

db = UsersSessionLocal()

if len(sys.argv) < 3:
    # Без аргументов — создаём админа
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
    
    # Создаём ключ для приглашения
    import secrets
    key_code = secrets.token_hex(4).upper()
    from app.models.user import InvitationKey
    key = InvitationKey(key_code=key_code, created_by=admin.id, created_at=func.now())
    db.add(key)
    db.commit()
    print(f"Ключ приглашения: {key_code}")
else:
    # С аргументами: python3 create_admin.py логин пароль "ФИО"
    username = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else username
    
    if db.query(User).filter(User.username == username).first():
        print(f"Пользователь {username} уже существует")
    else:
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role="user"
        )
        db.add(user)
        db.commit()
        print(f"Пользователь создан: {username} / {password} ({full_name})")

db.close()
