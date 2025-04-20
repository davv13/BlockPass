# app/main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

from app.routes import auth
from app.database import engine
from app.database.base import Base

# -------- tag metadata (for Swagger groups) --------
tags_metadata = [
    {"name": "Auth", "description": "Registration & login endpoints"},
    # later: {"name": "Vault", "description": "Encrypted password storage"}
]

# -------- FastAPI app instance --------
app = FastAPI(
    title="BlockPass Password Manager – Centralized API",
    description="""
A simple REST service that lets you:

* **Register** and get a user ID  
* **Login** and receive a JWT  
* (coming soon) **Store encrypted vault items**
""",
    version="0.1.0",
    contact={"name": "Davit Davtyan", "url": "https://github.com/yourrepo"},
    openapi_tags=tags_metadata,
    docs_url="/docs",          # disable default /docs
    redoc_url="/redoc",      # keep ReDoc if you like
)

# # -------- optional custom Swagger UI --------
# @app.get("/docs", include_in_schema=False)
# def custom_docs():
#     return get_swagger_ui_html(
#         openapi_url=app.openapi_url,
#         title="BlockPass API Docs",
#         swagger_favicon_url="https://raw.githubusercontent.com/.../favicon.png",
#         swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.7.2/swagger-ui.min.css",
#     )

# -------- create SQL tables if engine exists --------
if engine is not None:
    Base.metadata.create_all(bind=engine)

# -------- include routers --------
app.include_router(auth.router)

# -------- root ping --------
@app.get("/", tags=["Auth"])
def root():
    return {"msg": "BlockPass API is running"}
