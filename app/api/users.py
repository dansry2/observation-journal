from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_users_db
from ..models.user import User
from ..schemas.user import UserResponse
from ..utils.deps import get_optional_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_users_db), current_user: User = Depends(get_optional_user)):
    return db.query(User).order_by(User.full_name).all()
