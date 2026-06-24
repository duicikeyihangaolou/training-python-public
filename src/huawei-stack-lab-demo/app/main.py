import logging
import os
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from app.storage.obs_client import ObjectStorage, build_obs_client

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        get_store().probe_bucket()
    except Exception:
        logger.exception("OBS bucket probe failed")
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}


@app.get("/")
def root():
    return {"msg": "lab-demo", "log_level": os.getenv("LOG_LEVEL", "info")}

def get_store() -> ObjectStorage:
    return ObjectStorage(build_obs_client(), os.environ["OBS_BUCKET"])

@app.post("/files")
async def upload_file(file: UploadFile = File(...)):
    body = await file.read()
    key = f"uploads/{uuid4().hex}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"
    get_store().upload_bytes(key, body, content_type=content_type)
    return {"key": key, "content_type": content_type}


@app.get("/files/{key:path}/download-url")
def presigned_download(key: str, expires: int = 3600):
    signed = get_store().create_presigned_download_url(key, expires=expires)
    return {"url": signed.signedUrl, "expires_in": expires}


@app.post("/files/upload-url")
def presigned_upload(filename: str, content_type: str = "application/octet-stream"):
    key = f"uploads/{uuid4().hex}/{filename}"
    expires = 3600
    signed = get_store().create_presigned_upload_url(
        key, content_type=content_type, expires=expires
    )
    return {
        "key": key,
        "url": signed.signedUrl,
        "headers": signed.actualSignedRequestHeaders,
        "expires_in": expires,
    }
