from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FruitSample(Base):
    __tablename__ = "fruit_samples"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sample_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    fruit_type: Mapped[str] = mapped_column(String(80), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="collecting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("fruit_samples.id"), index=True)
    device_id: Mapped[str] = mapped_column(String(80), default="ESP32_01")
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    gas_raw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gas_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    voc_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    sample: Mapped[FruitSample] = relationship(back_populates="readings")
