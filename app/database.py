from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# База пользователей
users_engine = create_engine(
    settings.USERS_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
UsersSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=users_engine)
UsersBase = declarative_base()

# База журналов
journal_engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)
JournalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=journal_engine)
JournalBase = declarative_base()

def get_db():
    db = JournalSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_users_db():
    db = UsersSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Хелпер: достать пользователя по id
def get_user_by_id(user_id: int):
    db = UsersSessionLocal()
    try:
        from .models.user import User
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

def get_user_name(user_id: int) -> str:
    user = get_user_by_id(user_id)
    return user.full_name if user else None
