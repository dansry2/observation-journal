from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os
from .database import journal_engine, users_engine, JournalBase, UsersBase
from .models import *
from .api import auth, observations, errors, external, users, admin, backups
from .config import settings

JournalBase.metadata.create_all(bind=journal_engine)
UsersBase.metadata.create_all(bind=users_engine)

app = FastAPI(title="Журнал наблюдений", root_path=settings.SUBPATH)

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

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

def add_base_tag(html, base_path):
    if base_path and base_path != "/":
        base_path = base_path.rstrip("/") + "/"
        html = html.replace("<head>", f"<head><base href=\"{base_path}\">")
    return html

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(frontend_path, "index.html")
    with open(index_path, "r") as f:
        html = f.read()
    if settings.SUBPATH and settings.SUBPATH != "/":
        html = add_base_tag(html, settings.SUBPATH)
    return Response(content=html, media_type="text/html")

@app.get("/api")
def root():
    return {"message": "API работает"}
