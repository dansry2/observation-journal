from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from .database import journal_engine, users_engine, JournalBase, UsersBase
from .models import *
from .api import auth, observations, errors, external, users, admin, backups

JournalBase.metadata.create_all(bind=journal_engine)
UsersBase.metadata.create_all(bind=users_engine)

app = FastAPI(title="Журнал наблюдений")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(observations.router)
app.include_router(errors.router)
app.include_router(external.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(backups.router)

# Раздача фронтенда
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_path):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            from starlette.responses import FileResponse
            return FileResponse(file_path)
        from starlette.responses import FileResponse
        return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/api")
def root():
    return {"message": "API работает"}
