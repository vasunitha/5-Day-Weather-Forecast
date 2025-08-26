# app/models.py
from typing import Optional, List
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship

class WeatherRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_query: str
    resolved_name: str
    country: str
    lat: float
    lon: float
    start_date: date
    end_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    days: List["WeatherDay"] = Relationship(back_populates="request", cascade_delete=True)


class WeatherDay(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="weatherrequest.id")
    date: date
    tmin: float
    tmax: float
    tavg: float

    request: WeatherRequest = Relationship(back_populates="days")
