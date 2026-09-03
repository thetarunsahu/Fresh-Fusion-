from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class SampleCreate(BaseModel):
    fruit_type: str = "Auto"
    variety: str | None = None
    source: str | None = None

class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sample_id: str
    fruit_type: str
    variety: str | None = None
    source: str | None = None
    status: str
    created_at: datetime

class SensorIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    sample_id: str | None = None
    device_id: str = "ESP32_01"
    temperature: float | None = None
    humidity: float | None = None
    mq135_raw: float | None = None
    gas_ppm: float | None = None
    voc_index: float | None = None
    rssi: float | None = None
    uptime_ms: float | None = None
    extra_metrics: dict[str, Any] = Field(default_factory=dict)

class SensorOut(SensorIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    captured_at: datetime

class FusionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    freshness_score: float
    sensor_score: float | None
    vision_score: float | None
    label: str
    confidence: float
    risk: str
    explanation: str | None
    components: dict[str, Any]
    created_at: datetime
