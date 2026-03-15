"""
SQLAlchemy models for database tables.
"""
from sqlalchemy import Column, Text, Float, Integer, DateTime, types
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from src.api.db import Base
import json


class JSONBCompatible(types.TypeDecorator):
    """A JSONB type that falls back to Text for SQLite (used in tests)."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and dialect.name != "postgresql":
            return json.loads(value)
        return value


class POI(Base):
    """
    SQLAlchemy model for the 'poi' table.
    Represents a Point of Interest with location, description, and metadata.
    """
    __tablename__ = "poi"

    id = Column(Text, primary_key=True)
    label = Column(Text)
    description = Column(Text)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    uri = Column(Text)
    type = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    department_code = Column(Text, nullable=True)
    theme = Column(Text, nullable=True)
    last_update = Column(DateTime)
    raw_json = Column(JSONBCompatible)
    source_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())