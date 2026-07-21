from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from .database import journal_engine, users_engine, JournalBase, UsersBase
from .models import *
from .api import auth, observations, uv_plane, errors, movements, other, external, users, backups

JournalBase.metadata.create_all(bind=journal_engine)
UsersBase.metadata.create_all(bind=users_engine)

app = FastAPI(title="Журнал наблюдений")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(observations.router)
app.include_router(errors.router)
app.include_router(uv_plane.router)
app.include_router(movements.router)
app.include_router(other.router)
app.include_router(external.router)
app.include_router(users.router)
app.include_router(backups.router)

# Раздача фронтенда (после API)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_path):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        import os as _os
        file_path = _os.path.join(frontend_path, full_path)
        if _os.path.exists(file_path) and not _os.path.isdir(file_path):
            return FileResponse(file_path)
        return FileResponse(_os.path.join(frontend_path, "index.html"))
    
    from starlette.responses import FileResponse

@app.get("/")
def root():
    return {"message": "API работает"}
