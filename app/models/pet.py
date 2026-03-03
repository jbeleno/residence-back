"""Pet model."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.catalog import PetSpecies
    from app.models.core import Property


class Pet(TimestampMixin, Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pet_species_id: Mapped[int] = mapped_column(ForeignKey("pet_species.id"), nullable=False)
    breed: Mapped[Optional[str]] = mapped_column(String(100))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    vaccination_up_to_date: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    pet_species: Mapped["PetSpecies"] = relationship(lazy="joined")
    property: Mapped["Property"] = relationship(lazy="selectin")
