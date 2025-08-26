# app/crud.py
from datetime import datetime
from sqlmodel import Session, select
from app import models, schemas, utils

# CREATE
async def create_request(session: Session, req: schemas.WeatherRequestCreate):
    # Validate location
    loc = await utils.resolve_location(req.raw_query)
    if not loc:
        raise ValueError("Location not found")

    # Validate dates
    ok, msg = utils.validate_date_range(req.start_date, req.end_date)
    if not ok:
        raise ValueError(msg)

    # Fetch weather
    days_data = await utils.fetch_weather(loc["lat"], loc["lon"], req.start_date, req.end_date)
    if not days_data:
        raise ValueError("No weather data found")

    # Create request row
    request = models.WeatherRequest(
        raw_query=req.raw_query,
        resolved_name=loc["name"],
        country=loc["country"],
        lat=loc["lat"],
        lon=loc["lon"],
        start_date=req.start_date,
        end_date=req.end_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(request)
    session.commit()
    session.refresh(request)

    # Add daily rows
    for d in days_data:
        day = models.WeatherDay(
            request_id=request.id,
            date=d["date"],
            tmin=d["tmin"],
            tmax=d["tmax"],
            tavg=d["tavg"]
        )
        session.add(day)
    session.commit()
    session.refresh(request)

    return request


# READ all
def get_requests(session: Session):
    stmt = select(models.WeatherRequest)
    return session.exec(stmt).all()


# READ one
def get_request(session: Session, request_id: int):
    return session.get(models.WeatherRequest, request_id)


# UPDATE
async def update_request(session: Session, request_id: int, req: schemas.WeatherRequestUpdate):
    request = session.get(models.WeatherRequest, request_id)
    if not request:
        return None

    # If user provided new values
    if req.raw_query:
        request.raw_query = req.raw_query
        loc = await utils.resolve_location(req.raw_query)
        if not loc:
            raise ValueError("Location not found")
        request.resolved_name = loc["name"]
        request.country = loc["country"]
        request.lat = loc["lat"]
        request.lon = loc["lon"]

    if req.start_date and req.end_date:
        ok, msg = utils.validate_date_range(req.start_date, req.end_date)
        if not ok:
            raise ValueError(msg)
        request.start_date = req.start_date
        request.end_date = req.end_date

    # Refresh daily data
    days_data = await utils.fetch_weather(request.lat, request.lon, request.start_date, request.end_date)
    session.query(models.WeatherDay).filter(models.WeatherDay.request_id == request.id).delete()
    for d in days_data:
        session.add(models.WeatherDay(
            request_id=request.id,
            date=d["date"],
            tmin=d["tmin"],
            tmax=d["tmax"],
            tavg=d["tavg"]
        ))

    request.updated_at = datetime.utcnow()
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


# DELETE
def delete_request(session: Session, request_id: int):
    request = session.get(models.WeatherRequest, request_id)
    if not request:
        return None
    session.delete(request)
    session.commit()
    return request
