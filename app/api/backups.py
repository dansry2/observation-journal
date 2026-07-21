
import os
from fastapi import APIRouter, Depends, HTTPException
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/admin/backups", tags=["admin"])

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups")

@router.get("/")
def list_backups(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")
    
    if not os.path.exists(BACKUP_DIR):
        return {"backups": []}
    
    files = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith("journal_") and f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            files.append({
                "name": f,
                "size": size,
                "size_mb": round(size / 1024 / 1024, 2),
                "date": f.replace("journal_", "").replace(".db", "")
            })
    
    return {"backups": files[:30]}
