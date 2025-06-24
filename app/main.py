from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.api.routes.upload import router as upload_router
from fastapi.openapi.utils import get_openapi


app = FastAPI(
    title="Your API",
    version="0.1.0",
    openapi_version="3.0.3",
)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )
    openapi_schema["openapi"] = "3.0.3"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(upload_router, prefix="/upload", tags=["midi"])