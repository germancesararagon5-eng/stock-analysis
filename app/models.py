from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class BrokerConfig(Base):
    __tablename__ = "broker_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    api_key = Column(String(255), nullable=True)
    api_secret = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=True)
    sandbox = Column(Boolean, default=True)
    active = Column(Boolean, default=False)
    extra = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False)
    strategy = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal = Column(String(10), nullable=False)
    confidence = Column(Float, default=0.0)
    strategy = Column(String(50), default="scalping")
    interval = Column(String(10), default="5m")
    periods = Column(Integer, default=100)
    price_at_prediction = Column(Float, nullable=True)
    reasons = Column(JSON, nullable=True)
    indicators_snapshot = Column(JSON, nullable=True)
    outcome = Column(String(10), nullable=True, index=True)
    price_at_outcome = Column(Float, nullable=True)
    price_change_pct = Column(Float, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WhatsAppConfig(Base):
    __tablename__ = "whatsapp_configs"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), default="")
    connected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
