# app/schemas.py
from datetime import date, datetime
from typing import List, Optional
from sqlmodel import SQLModel

class WeatherDayBase(SQLModel):
    date: date
    tmin: float
    tmax: float
    tavg: float

class WeatherDayRead(WeatherDayBase):
    id: int

class WeatherRequestBase(SQLModel):
    raw_query: str
    start_date: date
    end_date: date

class WeatherRequestCreate(WeatherRequestBase):
    pass

class WeatherRequestUpdate(SQLModel):
    raw_query: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class WeatherRequestRead(SQLModel):
    id: int
    raw_query: str
    resolved_name: str
    country: str
    lat: float
    lon: float
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime
    days: List[WeatherDayRead] = []
