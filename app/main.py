from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import auth, vault
from app.database.base import Base
from app.database import engine

from app.routes.views import router as views_router
from app.routes.vault import router as vault_router

app = FastAPI(
    title="BlockPass Password Manager",
    version="0.1.0",
    docs_url=None,  # turn off Swagger UI if you like
)

# serve /static (if you ever add local CSS/JS/images)
# app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)       # /auth
app.include_router(views_router)      # /register, /login, /vault (HTML)
app.include_router(vault_router)      # /vault (JSON) – now comes _after_ the HTML

# create tables
if engine:
    Base.metadata.create_all(bind=engine)
