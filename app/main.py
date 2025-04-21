# app/main.py
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
import app.models
from app.routes import auth
from app.routes.vault import router as vault_router
from app.database import engine
from app.database.base import Base

# -------- tag metadata (for Swagger groups) --------
tags_metadata = [
    {"name": "Auth",  "description": "Registration & login endpoints"},
    {"name": "Vault", "description": "Encrypted password‑vault storage"},
]

# -------- instantiate FastAPI --------
app = FastAPI(
    title="BlockPass Password Manager – Centralized API",
    description="""
A simple REST service that lets you:

* **Register** and get a user ID  
* **Login** and receive a JWT  
* **Store encrypted vault items**
""",
    version="0.1.0",
    contact={"name": "Davit Davtyan", "url": "https://github.com/yourrepo"},
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# -------- define OAuth2 password‑flow scheme (for docs only) --------
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="oauth2Password",
)

# -------- stash the original openapi() so we don’t recurse --------
_original_openapi = app.openapi

# -------- override the OpenAPI schema to use OAuth2 password flow --------
def custom_openapi() -> Dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    # call the original, not app.openapi()
    schema = _original_openapi()

    comps = schema.setdefault("components", {})
    security_schemes = comps.setdefault("securitySchemes", {})

    # remove any default bearerAuth if present
    security_schemes.pop("bearerAuth", None)

    # add our password‑flow scheme
    security_schemes["oauth2Password"] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/auth/login",
                "scopes": {}
            }
        }
    }

    # apply that scheme to every vault endpoint
    for path in ("/vault/", "/vault/{item_id}"):
        if path in schema["paths"]:
            for method in schema["paths"][path]:
                schema["paths"][path][method]["security"] = [{"oauth2Password": []}]

    app.openapi_schema = schema
    return schema

# hook it up
app.openapi = custom_openapi

# -------- create SQL tables if engine exists --------
if engine is not None:
    Base.metadata.create_all(bind=engine)

# -------- mount routers --------
app.include_router(auth.router)
app.include_router(vault_router)

# -------- root ping --------
@app.get("/", tags=["Auth"])
def root():
    return {"msg": "BlockPass API is running"}