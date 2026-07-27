import sys
from app.database import UsersSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

db = UsersSessionLocal()

if len(sys.argv) < 3:
    print("Использование: python3 create_admin.py логин пароль 'ФИО'")
    print("Админ задаётся через переменные окружения ADMIN_USERNAME / ADMIN_PASSWORD")
    db.close()
    exit(1)

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
    print(f"Пользователь создан: {username} ({full_name})")

db.close()
