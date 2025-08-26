# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app.database import init_db, get_session
from app import crud, schemas
from fastapi import APIRouter
from app.utils import fetch_youtube_videos, generate_google_maps_link
from app.database import get_session
from sqlmodel import Session, select
from app.models import WeatherRequest



app = FastAPI(title="Weather App Backend")



origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Weather backend running 🚀"}

# CREATE
@app.post("/api/requests", response_model=schemas.WeatherRequestRead)
async def create_request(req: schemas.WeatherRequestCreate, session: Session = Depends(get_session)):
    try:
        return await crud.create_request(session, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# READ all
@app.get("/api/requests", response_model=list[schemas.WeatherRequestRead])
def read_requests(session: Session = Depends(get_session)):
    return crud.get_requests(session)

# READ one
@app.get("/api/requests/{request_id}", response_model=schemas.WeatherRequestRead)
def read_request(request_id: int, session: Session = Depends(get_session)):
    db_req = crud.get_request(session, request_id)
    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found")
    return db_req

# UPDATE
@app.put("/api/requests/{request_id}", response_model=schemas.WeatherRequestRead)
async def update_request(request_id: int, req: schemas.WeatherRequestUpdate, session: Session = Depends(get_session)):
    try:
        db_req = await crud.update_request(session, request_id, req)
        if not db_req:
            raise HTTPException(status_code=404, detail="Request not found")
        return db_req
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# DELETE
@app.delete("/api/requests/{request_id}")
def delete_request(request_id: int, session: Session = Depends(get_session)):
    db_req = crud.delete_request(session, request_id)
    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Deleted successfully"}


@app.get("/api/extras/{location}")
async def get_extras(location: str, session: Session = Depends(get_session)):
    # Try to find location from DB
    statement = select(WeatherRequest).where(WeatherRequest.resolved_name.ilike(f"%{location}%"))
    result = session.exec(statement).first()

    lat, lon, country = None, None, None
    if result:
        lat, lon, country = result.lat, result.lon, result.country

    # Fetch YouTube videos safely
    try:
        videos = await fetch_youtube_videos(location)
    except Exception:
        videos = []  # fallback if YouTube fails

    # Only create maps link if we found coordinates
    maps_link = None
    if lat and lon:
        maps_link = generate_google_maps_link(lat, lon)

    return {
        "location": location,
        "videos": videos,
        "country": country,
        "google_maps": maps_link
    }


