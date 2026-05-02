"""Cloudflare R2 (S3-compatible) object storage client.

Uploads images and returns a public URL the frontend can render directly.
The bucket is configured with R2.dev public access; private buckets would
require presigned URLs instead — not implemented here.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import BadRequestError

logger = logging.getLogger(__name__)

# Whitelist of safe image content types (frontend will render these inline).
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def _build_client():
    if not (
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
        and settings.R2_BUCKET_NAME
    ):
        raise RuntimeError(
            "R2 storage is not configured. Set R2_ACCOUNT_ID, "
            "R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME "
            "in the environment."
        )
    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",  # R2 uses 'auto'
        config=Config(signature_version="s3v4"),
    )


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def validate_image_upload(filename: str, content_type: str, size_bytes: int) -> str:
    """Validate filename + size + content type. Returns the file extension."""
    if size_bytes <= 0:
        raise BadRequestError("Archivo vacío")

    max_bytes = settings.R2_MAX_UPLOAD_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise BadRequestError(
            f"El archivo supera el máximo de {settings.R2_MAX_UPLOAD_MB} MB."
        )

    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestError(
            f"Extensión '{ext}' no permitida. Usa jpg, png, webp o gif."
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        # Fall back to guessing from extension if the browser sent
        # application/octet-stream.
        guessed, _ = mimetypes.guess_type(filename)
        if guessed not in ALLOWED_CONTENT_TYPES:
            raise BadRequestError(
                f"Tipo de archivo '{content_type}' no permitido."
            )
    return ext


def upload_image(
    fileobj: BinaryIO,
    *,
    folder: str,
    filename: str,
    content_type: str,
) -> str:
    """Upload a file to R2 under <folder>/<uuid>.<ext> and return its public URL.

    The bucket must have R2.dev public access enabled and
    R2_PUBLIC_BASE_URL configured. If not, we still upload but return
    the S3-style key (caller can build a presigned URL later).
    """
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "bin").lower()
    key = f"{folder.strip('/')}/{uuid.uuid4().hex}.{ext}"

    try:
        client = _get_client()
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=fileobj,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("R2 upload failed for key=%s", key)
        raise BadRequestError("No se pudo subir el archivo. Reintenta.") from e

    if settings.R2_PUBLIC_BASE_URL:
        base = settings.R2_PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/{key}"
    # Bucket private — return the key, caller is expected to presign.
    return key


def delete_object(public_url_or_key: str) -> None:
    """Best-effort delete of an uploaded object given its public URL or key."""
    if not public_url_or_key:
        return
    key = public_url_or_key
    if settings.R2_PUBLIC_BASE_URL:
        base = settings.R2_PUBLIC_BASE_URL.rstrip("/") + "/"
        if key.startswith(base):
            key = key[len(base):]
    try:
        _get_client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except Exception:
        logger.warning("R2 delete failed for key=%s (ignored)", key)
