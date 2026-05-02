"""Upload router – uploads images to Cloudflare R2 and persists URLs in DB.

Endpoints:
- POST /uploads/avatar              → current user's avatar
- POST /uploads/condo-logo          → admin: logo of current condominium
- POST /uploads/pet/{pet_id}        → resident or admin: photo of a pet
- POST /uploads/amenity/{amenity_id}→ admin: hero image of an amenity
- POST /uploads/news/{news_id}      → admin: cover image of a news article
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_role,
    get_current_user,
    require_admin,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.responses import success
from app.core.storage import delete_object, upload_image, validate_image_upload
from app.models.amenity import Amenity
from app.models.core import Condominium, Property, User, UserProperty
from app.models.news import NewsBoard
from app.models.pet import Pet

router = APIRouter(prefix="/uploads", tags=["Uploads"])


async def _read_and_validate(file: UploadFile) -> tuple[bytes, str, str]:
    contents = await file.read()
    ext = validate_image_upload(file.filename or "", file.content_type or "", len(contents))
    return contents, ext, file.content_type or "application/octet-stream"


@router.post("/avatar", status_code=201)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload the avatar of the current user. Replaces the previous one."""
    import io
    contents, _, content_type = await _read_and_validate(file)

    # Delete old avatar (best effort)
    if current_user.avatar_url:
        delete_object(current_user.avatar_url)

    url = upload_image(
        io.BytesIO(contents),
        folder=f"avatars/{current_user.id}",
        filename=file.filename or "avatar",
        content_type=content_type,
    )
    await db.execute(
        update(User).where(User.id == current_user.id).values(avatar_url=url)
    )
    await db.commit()
    return success({"avatar_url": url})


@router.post(
    "/condo-logo",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def upload_condo_logo(
    file: UploadFile = File(...),
    cid: UUID = Depends(get_current_condominium_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload the logo of the current condominium (admin / super_admin)."""
    import io
    contents, _, content_type = await _read_and_validate(file)

    result = await db.execute(select(Condominium).where(Condominium.id == cid))
    condo = result.scalars().first()
    if not condo:
        raise NotFoundError("Condominio no encontrado")

    if condo.logo_url:
        delete_object(condo.logo_url)

    url = upload_image(
        io.BytesIO(contents),
        folder=f"condos/{cid}/logo",
        filename=file.filename or "logo",
        content_type=content_type,
    )
    condo.logo_url = url
    await db.commit()
    return success({"logo_url": url})


@router.post("/pet/{pet_id}", status_code=201)
async def upload_pet_photo(
    pet_id: int,
    file: UploadFile = File(...),
    cid: UUID = Depends(get_current_condominium_id),
    role: str = Depends(get_current_role),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a pet's photo. Allowed for: any resident linked to the pet's
    property, or admin/super_admin of the condominium."""
    import io

    result = await db.execute(
        select(Pet, Property)
        .join(Property, Pet.property_id == Property.id)
        .where(Pet.id == pet_id, Property.condominium_id == cid)
    )
    row = result.first()
    if not row:
        raise NotFoundError("Mascota no encontrada en este condominio")
    pet, prop = row

    if role not in ("admin", "super_admin"):
        link = await db.execute(
            select(UserProperty).where(
                UserProperty.user_id == current_user.id,
                UserProperty.property_id == prop.id,
                UserProperty.is_active.is_(True),
            )
        )
        if link.scalars().first() is None:
            raise ForbiddenError(
                "Solo el dueño/residente de la mascota o un admin pueden subir esta foto"
            )

    contents, _, content_type = await _read_and_validate(file)

    if pet.photo_url:
        delete_object(pet.photo_url)

    url = upload_image(
        io.BytesIO(contents),
        folder=f"pets/{pet.id}",
        filename=file.filename or "pet",
        content_type=content_type,
    )
    pet.photo_url = url
    await db.commit()
    return success({"photo_url": url})


@router.post(
    "/amenity/{amenity_id}",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def upload_amenity_image(
    amenity_id: int,
    file: UploadFile = File(...),
    cid: UUID = Depends(get_current_condominium_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload the hero image of an amenity (admin / super_admin)."""
    import io

    result = await db.execute(
        select(Amenity).where(Amenity.id == amenity_id, Amenity.condominium_id == cid)
    )
    amenity = result.scalars().first()
    if not amenity:
        raise NotFoundError("Amenidad no encontrada en este condominio")

    contents, _, content_type = await _read_and_validate(file)

    if amenity.image_url:
        delete_object(amenity.image_url)

    url = upload_image(
        io.BytesIO(contents),
        folder=f"amenities/{amenity.id}",
        filename=file.filename or "amenity",
        content_type=content_type,
    )
    amenity.image_url = url
    await db.commit()
    return success({"image_url": url})


@router.post(
    "/news/{news_id}",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def upload_news_cover(
    news_id: int,
    file: UploadFile = File(...),
    cid: UUID = Depends(get_current_condominium_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload the cover image of a news article (admin / super_admin)."""
    import io

    result = await db.execute(
        select(NewsBoard).where(
            NewsBoard.id == news_id, NewsBoard.condominium_id == cid
        )
    )
    news = result.scalars().first()
    if not news:
        raise NotFoundError("Noticia no encontrada en este condominio")

    contents, _, content_type = await _read_and_validate(file)

    if news.cover_url:
        delete_object(news.cover_url)

    url = upload_image(
        io.BytesIO(contents),
        folder=f"news/{news.id}",
        filename=file.filename or "cover",
        content_type=content_type,
    )
    news.cover_url = url
    await db.commit()
    return success({"cover_url": url})
