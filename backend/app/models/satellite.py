from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, synonym

from ..db.base import Base


class Satellite(Base):
    __tablename__ = "satellites"
    __table_args__ = (
        Index("uq_satellites_norad_cat_id", "norad_cat_id", unique=True),
        Index("ix_satellites_object_name", "object_name"),
        Index("ix_satellites_object_type", "object_type"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    norad_cat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    norad_id = synonym("norad_cat_id")
    object_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name = synonym("object_name")
    object_id: Mapped[str | None] = mapped_column(String(100))
    object_type: Mapped[str | None] = mapped_column(String(50))
    owner_country: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(50))
    launch_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decay_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rcs_size: Mapped[str | None] = mapped_column(String(50))
    decay_status: Mapped[str | None] = mapped_column(String(50))
    line1: Mapped[str | None] = mapped_column(String(100))
    line2: Mapped[str | None] = mapped_column(String(100))
    epoch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GPHistory(Base):
    __tablename__ = "gp_history"
    __table_args__ = (UniqueConstraint("norad_cat_id", "epoch", name="uq_gp_norad_epoch"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    norad_cat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mean_motion: Mapped[float | None] = mapped_column(Float)
    eccentricity: Mapped[float | None] = mapped_column(Float)
    inclination: Mapped[float | None] = mapped_column(Float)
    ra_of_asc_node: Mapped[float | None] = mapped_column(Float)
    arg_of_pericenter: Mapped[float | None] = mapped_column(Float)
    mean_anomaly: Mapped[float | None] = mapped_column(Float)
    bstar: Mapped[float | None] = mapped_column(Float)
    mean_motion_dot: Mapped[float | None] = mapped_column(Float)
    mean_motion_ddot: Mapped[float | None] = mapped_column(Float)
    element_set_no: Mapped[int | None] = mapped_column(Integer)
    rev_at_epoch: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Conjunction(Base):
    __tablename__ = "conjunctions"
    __table_args__ = (
        UniqueConstraint("norad_cat_id_1", "norad_cat_id_2", "tca", name="uq_conjunction_pair_tca"),
        Index("ix_conjunctions_tca", "tca"),
        Index("ix_conjunctions_risk_tier", "risk_tier"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    norad_cat_id_1: Mapped[int] = mapped_column(BigInteger, nullable=False)
    norad_cat_id_2: Mapped[int] = mapped_column(BigInteger, nullable=False)
    object_name_1: Mapped[str | None] = mapped_column(String(255))
    object_name_2: Mapped[str | None] = mapped_column(String(255))
    tca: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    min_range_km: Mapped[float | None] = mapped_column(Float)
    rel_speed_kms: Mapped[float | None] = mapped_column(Float)
    max_prob: Mapped[float | None] = mapped_column(Float)
    dse_1: Mapped[float | None] = mapped_column(Float)
    dse_2: Mapped[float | None] = mapped_column(Float)
    dilution: Mapped[float | None] = mapped_column(Float)
    is_constellation_artifact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    risk_tier: Mapped[str | None] = mapped_column(String(10))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
