from datetime import datetime

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
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Satellite(Base):
    __tablename__ = "satellites"
    __table_args__ = (
        UniqueConstraint("norad_id", name="uq_satellites_norad_id"),
        UniqueConstraint("norad_cat_id", name="uq_satellites_norad_cat_id"),
        Index("ix_satellites_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    norad_id: Mapped[int | None] = mapped_column(BigInteger)
    name: Mapped[str | None] = mapped_column(String(255))
    object_type: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    norad_cat_id: Mapped[int | None] = mapped_column(BigInteger)
    object_name: Mapped[str | None] = mapped_column(String(255))
    object_id: Mapped[str | None] = mapped_column(String(100))
    owner_country: Mapped[str | None] = mapped_column(String(100))
    launch_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decay_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rcs_size: Mapped[str | None] = mapped_column(String(50))
    decay_status: Mapped[str | None] = mapped_column(String(50))
    line1: Mapped[str | None] = mapped_column(String(100))
    line2: Mapped[str | None] = mapped_column(String(100))
    epoch: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(80))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GPHistory(Base):
    __tablename__ = "gp_history"
    __table_args__ = (
        UniqueConstraint("norad_cat_id", "epoch", name="uq_gp_history_norad_epoch"),
        Index("ix_gp_history_norad_epoch", "norad_cat_id", "epoch"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    norad_cat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
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
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Conjunction(Base):
    __tablename__ = "conjunctions"
    __table_args__ = (
        UniqueConstraint(
            "norad_cat_id_1",
            "norad_cat_id_2",
            "tca",
            name="uq_conjunction_pair_tca",
        ),
        Index("ix_conjunctions_tca", "tca"),
        Index("ix_conjunctions_max_prob", "max_prob"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    norad_cat_id_1: Mapped[int] = mapped_column(BigInteger, nullable=False)
    norad_cat_id_2: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tca: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    min_range_km: Mapped[float | None] = mapped_column(Float)
    rel_speed_kms: Mapped[float | None] = mapped_column(Float)
    max_prob: Mapped[float | None] = mapped_column(Float)
    dse_1: Mapped[float | None] = mapped_column(Float)
    dse_2: Mapped[float | None] = mapped_column(Float)
    dilution: Mapped[float | None] = mapped_column(Float)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    object_name_1: Mapped[str | None] = mapped_column(String(255))
    object_name_2: Mapped[str | None] = mapped_column(String(255))
    is_constellation_artifact: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    risk_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
