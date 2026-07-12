from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .models import *
from .api import auth, observations, uv_plane, errors, other, external, users, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Журнал наблюдений")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(observations.router)
app.include_router(uv_plane.router)
app.include_router(errors.router)
app.include_router(other.router)
app.include_router(external.router)
app.include_router(users.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "API работает"}
