from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class FruitSample(Base):
    __tablename__ = "fruit_samples"
    id = Column(Integer, primary_key=True)
    sample_id = Column(String(32), unique=True, index=True, nullable=False)
    fruit_type = Column(String(60), index=True, nullable=False)
    variety = Column(String(80), nullable=True)
    source = Column(String(120), nullable=True)
    status = Column(String(32), default="collecting")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sensors = relationship("SensorReading", back_populates="sample", cascade="all, delete-orphan")
    images = relationship("FruitImage", back_populates="sample", cascade="all, delete-orphan")
    results = relationship("FusionResult", back_populates="sample", cascade="all, delete-orphan")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True)
    sample_id = Column(String(32), ForeignKey("fruit_samples.sample_id"), index=True, nullable=False)
    device_id = Column(String(80), index=True, default="ESP32_01")
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    mq135_raw = Column(Float, nullable=True)
    gas_ppm = Column(Float, nullable=True)
    voc_index = Column(Float, nullable=True)
    rssi = Column(Float, nullable=True)
    uptime_ms = Column(Float, nullable=True)
    extra_metrics = Column(JSON, default=dict)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    sample = relationship("FruitSample", back_populates="sensors")

class FruitImage(Base):
    __tablename__ = "fruit_images"
    id = Column(Integer, primary_key=True)
    sample_id = Column(String(32), ForeignKey("fruit_samples.sample_id"), index=True, nullable=False)
    angle = Column(String(30), default="unknown")
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=True)
    ground_truth = Column(String(30), nullable=True, index=True)
    url = Column(String(500), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    analysis = Column(JSON, default=dict)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    sample = relationship("FruitSample", back_populates="images")

class FusionResult(Base):
    __tablename__ = "fusion_results"
    id = Column(Integer, primary_key=True)
    sample_id = Column(String(32), ForeignKey("fruit_samples.sample_id"), index=True, nullable=False)
    freshness_score = Column(Float, nullable=False)
    sensor_score = Column(Float, nullable=True)
    vision_score = Column(Float, nullable=True)
    label = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)
    risk = Column(String(30), nullable=False)
    explanation = Column(Text, nullable=True)
    components = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sample = relationship("FruitSample", back_populates="results")
