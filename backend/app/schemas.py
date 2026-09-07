from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class SampleCreate(BaseModel):
    fruit_type: str = Field(default="Auto", min_length=1, max_length=60, pattern=r"^[A-Za-z][A-Za-z -]*$")
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
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    sample_id: str | None = None
    device_id: str = Field(default="ESP32_01", min_length=1, max_length=80)
    source: Literal["hardware", "simulator"] = "hardware"
    temperature: float = Field(ge=0, le=50)
    humidity: float = Field(ge=0, le=100)
    mq135_raw: float = Field(ge=0, le=4095)
    gas_ppm: float | None = Field(default=None, ge=0)
    voc_index: float | None = Field(default=None, ge=0)
    rssi: float | None = None
    uptime_ms: float | None = None
    extra_metrics: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def identify_test_data(self):
        # Source is a declared provenance label, not device authentication.
        if self.device_id.upper().startswith(("SIM", "TEST")) or self.extra_metrics.get("source") == "simulator":
            self.source = "simulator"
        return self

class VerificationIn(BaseModel):
    action: Literal["accept", "incorrect", "ground_truth"]
    ground_truth: Literal["fresh", "ripe", "overripe", "spoiled"] | None = None
    notes: str = Field(default="", max_length=2000)
    reviewer: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def require_label(self):
        if self.action == "ground_truth" and self.ground_truth is None:
            raise ValueError("Choose a FreshFusion ground-truth label")
        return self

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
