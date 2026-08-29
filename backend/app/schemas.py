from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SampleCreate(BaseModel):
    fruit_type: str = Field(min_length=2, max_length=80)
    notes: str | None = Field(default=None, max_length=500)


class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sample_code: str
    fruit_type: str
    notes: str | None
    status: str
    created_at: datetime


class SensorReadingCreate(BaseModel):
    sample_code: str
    device_id: str = "ESP32_01"
    temperature: float | None = None
    humidity: float | None = None
    gas_raw: int | None = None
    gas_ppm: float | None = None
    voc_index: float | None = None


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sample_id: int
    device_id: str
    temperature: float | None
    humidity: float | None
    gas_raw: int | None
    gas_ppm: float | None
    voc_index: float | None
    captured_at: datetime


class OverviewOut(BaseModel):
    total_samples: int
    total_readings: int
    latest_sample: SampleOut | None
    latest_reading: SensorReadingOut | None
