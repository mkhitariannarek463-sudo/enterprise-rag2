import os
import shutil
import uuid

import structlog
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.exceptions import AppError
from app.logging_config import setup_logging
from app.ingest import ingest_document
from app.rag import ask as rag_ask
from fastapi import Depends
from app.auth_routes import router as auth_router
from app.dependencies import get_current_tenant_id

settings = get_settings()
setup_logging(settings.log_level)
log = structlog.get_logger()

app = FastAPI(title=settings.app_name)
app.include_router(auth_router)
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    log.warning("app_error", code=exc.code, message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}


class AskRequest(BaseModel):
    query: str


@app.post("/ask")
async def ask_endpoint(payload: AskRequest, tenant_id: str = Depends(get_current_tenant_id)):
    result = rag_ask(tenant_id, payload.query)
    return result  
@app.post("/documents/upload")
async def upload_endpoint(file: UploadFile = File(...), tenant_id: str = Depends(get_current_tenant_id)):
    os.makedirs("uploads", exist_ok=True)
    temp_path = os.path.join("uploads", f"{uuid.uuid4()}_{file.filename}")
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    document_id = ingest_document(temp_path, tenant_id, file.filename)
    return {"document_id": str(document_id)}