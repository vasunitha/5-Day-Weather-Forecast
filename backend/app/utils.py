# app/utils.py
import httpx
from datetime import date
import urllib.parse
import yt_dlp

GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"

# -------- Location Validation --------
async def resolve_location(query: str):
    """
    Resolve a location string (city, zip, coords) to lat/lon + metadata.
    Returns dict: {lat, lon, name, country} or None if not found.
    """

    # Case 1: Coordinates input (lat,lon)
    if "," in query:
        parts = [p.strip() for p in query.split(",")]
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                return {"lat": lat, "lon": lon, "name": "Custom Location", "country": ""}
            except ValueError:
                pass  # not valid numbers → fall back to search

    # Case 2: City/Zip → Use Open-Meteo Geocoding
    async with httpx.AsyncClient() as client:
        resp = await client.get(GEOCODE_API, params={"name": query, "count": 1})
        data = resp.json()
        if "results" in data and len(data["results"]) > 0:
            best = data["results"][0]
            return {
                "lat": best["latitude"],
                "lon": best["longitude"],
                "name": best["name"],
                "country": best.get("country", "")
            }

    return None


# -------- Date Validation --------
def validate_date_range(start: date, end: date):
    """
    Ensure start <= end and both are within a reasonable range.
    Returns (True, "") if ok, else (False, error_message).
    """
    if start > end:
        return False, "Start date must be before end date."

    if (end - start).days > 365:
        return False, "Date range too long (max 1 year)."

    if start.year < 1950:
        return False, "Start date too far in the past."

    if end.year > (date.today().year + 2):
        return False, "End date too far in the future."

    return True, ""

# app/utils.py 
async def fetch_weather(lat: float, lon: float, start_date: date, end_date: date):
    """
    Fetch daily weather (tmin, tmax, tavg) for given coords + date range.
    Uses Open-Meteo Archive API.
    Returns list of dicts: [{date, tmin, tmax, tavg}, ...]
    """
    WEATHER_API = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"],
        "timezone": "auto"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    days = []
    if "daily" in data:
        for i, d in enumerate(data["daily"]["time"]):
            days.append({
                "date": date.fromisoformat(d),
                "tmin": data["daily"]["temperature_2m_min"][i],
                "tmax": data["daily"]["temperature_2m_max"][i],
                "tavg": data["daily"]["temperature_2m_mean"][i],
            })
    return days

import urllib.parse
import yt_dlp

async def fetch_youtube_videos(query: str, max_results: int = 3):
    """Fetch a few YouTube video links for the given query."""
    search_url = f"ytsearch{max_results}:{query}"
    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True}
    videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        if "entries" in info:
            for entry in info["entries"]:
                videos.append({
                    "title": entry.get("title"),
                    "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
                })
    return videos


def generate_google_maps_link(lat: float, lon: float) -> str:
    """Generate a Google Maps link for given coordinates."""
    return f"https://www.google.com/maps?q={lat},{lon}"




# --- YouTube API (using free public search via no-key endpoint) ---
async def fetch_youtube_videos(query: str):
    """
    Fetch YouTube search results (limited to 3) for a given query.
    This uses the free "piped.video" API as a proxy (no API key required).
    """
    url = f"https://piped.video/api/v1/search?q={query}+travel"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        videos = []
        for item in data[:3]:  # limit to 3 videos
            videos.append({
                "title": item.get("title"),
                "url": f"https://www.youtube.com/watch?v={item.get('url').split('/')[-1]}"
            })
        return videos
    
# --- Google Maps link generator ---
def generate_google_maps_link(lat: float, lon: float) -> str:
    """Generate a Google Maps link for given coordinates."""
    return f"https://www.google.com/maps?q={lat},{lon}"