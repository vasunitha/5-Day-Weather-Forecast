import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const apiKey = "04de74770f1697780a363fd798708378";
const BACKEND_URL = "https://five-day-weather-forecast-v93k.onrender.com/weather"; // Flask backend
const GOOGLE_MAPS_KEY = "AIzaSyB26mb59DX5eePZVVygX_2k_pRKPgKnxRA";
const YOUTUBE_API_KEY = "AIzaSyB26mb59DX5eePZVVygX_2k_pRKPgKnxRA";

function App() {
  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [weatherData, setWeatherData] = useState(null);
  const [savedWeather, setSavedWeather] = useState([]);
  const [editId, setEditId] = useState(null);
  const [mapUrl, setMapUrl] = useState("");
  const [youtubeVideos, setYoutubeVideos] = useState([]);
  const [activeTab, setActiveTab] = useState("weather"); // weather, map, videos

  useEffect(() => {
    fetchSavedWeather();
  }, []);

  const fetchSavedWeather = async () => {
    try {
      const res = await axios.get(BACKEND_URL);
      setSavedWeather(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const getCoordinates = async (loc) => {
    loc = loc.trim().replace(/,$/, "");
    const zipMatch = loc.match(/^(\d+)(?:,([A-Za-z]{2}))?$/);
    if (zipMatch) {
      const zip = zipMatch[1];
      const country = zipMatch[2] || "US";
      try {
        const res = await axios.get(
          `https://api.openweathermap.org/data/2.5/weather?zip=${zip},${country}&appid=${apiKey}`
        );
        const { coord, name, sys } = res.data;
        return { lat: coord.lat, lon: coord.lon, name, country: sys.country };
      } catch {
        alert("Zip code not found!");
        return null;
      }
    }
    try {
      const res = await axios.get(
        `https://api.openweathermap.org/geo/1.0/direct?q=${loc}&limit=1&appid=${apiKey}`
      );
      if (res.data.length === 0) {
        alert("Location not found!");
        return null;
      }
      const { lat, lon, name, country } = res.data[0];
      return { lat, lon, name, country };
    } catch {
      alert("Error fetching coordinates");
      return null;
    }
  };

  const filterDailyByDateRange = (daily, start, end) => {
    if (!start || !end) return daily;
    const startMs = new Date(start).getTime();
    const endMs = new Date(end).getTime();
    return daily.filter(d => d.dt * 1000 >= startMs && d.dt * 1000 <= endMs);
  };

  const fetchWeatherFromCoords = async (coords) => {
    try {
      const res = await axios.get(
        `https://api.openweathermap.org/data/3.0/onecall?lat=${coords.lat}&lon=${coords.lon}&appid=${apiKey}&units=metric`
      );
      let dailyData = res.data.daily.slice(0, 5);
      dailyData = filterDailyByDateRange(dailyData, startDate, endDate);

      setMapUrl(`https://www.google.com/maps/embed/v1/view?key=${GOOGLE_MAPS_KEY}&center=${coords.lat},${coords.lon}&zoom=10`);

      const ytRes = await axios.get(
        `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${coords.name} travel&maxResults=3&type=video&key=${YOUTUBE_API_KEY}`
      );
      setYoutubeVideos(ytRes.data.items);

      return {
        location: coords.name + (coords.country ? `, ${coords.country}` : ""),
        current: res.data.current,
        daily: dailyData,
        temp_min: Math.min(...dailyData.map(d => d.temp.min)),
        temp_max: Math.max(...dailyData.map(d => d.temp.max)),
        description: dailyData[0].weather[0].description,
        icon: dailyData[0].weather[0].icon
      };
    } catch (err) {
      alert("Error fetching weather data");
      console.error(err);
      return null;
    }
  };

  const getWeather = async () => {
    if (!location) return;
    let coords = null;
    if (location.includes(",")) {
      const parts = location.split(",").map(p => p.trim());
      const lat = parseFloat(parts[0]);
      const lon = parseFloat(parts[1]);
      coords = !isNaN(lat) && !isNaN(lon) ? { lat, lon, name: "Your Location", country: "" } : await getCoordinates(location);
    } else {
      coords = await getCoordinates(location);
    }
    if (!coords) return;
    const data = await fetchWeatherFromCoords(coords);
    setWeatherData(data);
  };

  const saveWeather = async () => {
    if (!weatherData || !startDate || !endDate) {
      alert("Please fetch weather and enter start/end dates");
      return;
    }
    const payload = {
      location: weatherData.location,
      start_date: startDate,
      end_date: endDate,
      temp_min: weatherData.temp_min,
      temp_max: weatherData.temp_max,
      description: weatherData.description
    };
    try {
      if (editId) await axios.put(`${BACKEND_URL}/${editId}`, payload);
      else await axios.post(BACKEND_URL, payload);
      setStartDate(""); setEndDate(""); setEditId(null); fetchSavedWeather();
    } catch (err) { console.error(err); }
  };

  const deleteRecord = async (id) => { try { await axios.delete(`${BACKEND_URL}/${id}`); fetchSavedWeather(); } catch (err) { console.error(err); } };
  const editRecord = (rec) => { setEditId(rec.id); setLocation(rec.location); setStartDate(rec.start_date); setEndDate(rec.end_date); };

  const formatDate = dt => new Date(dt * 1000).toLocaleDateString(undefined, { weekday:'short', month:'short', day:'numeric' });

  const exportJSON = (data) => {
    if (!data.length) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "weather_data.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = (data) => {
    if (!data.length) return;
    const header = Object.keys(data[0]).join(",");
    const rows = data.map(d => Object.values(d).join(",")).join("\n");
    const blob = new Blob([header + "\n" + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "weather_data.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportMarkdown = (data) => {
    if (!data.length) return;
    let md = "| " + Object.keys(data[0]).join(" | ") + " |\n";
    md += "| " + Object.keys(data[0]).map(() => "---").join(" | ") + " |\n";
    data.forEach(d => {
      md += "| " + Object.values(d).join(" | ") + " |\n";
    });
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "weather_data.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app">
      <h1>Weather App 🌤️</h1>

      {/* Search & Dates & Buttons */}
      <div className="search" style={{display:'flex', flexDirection:'column', gap:'10px'}}>
        <div style={{display:'flex', gap:'10px', flexWrap:'wrap'}}>
          <input type="text" placeholder="City, Zip, or coords" value={location} onChange={e=>setLocation(e.target.value)} onKeyDown={e=>e.key==='Enter'&&getWeather()}/>
          <button onClick={getWeather}>Search</button>
          <button onClick={()=>navigator.geolocation.getCurrentPosition(async pos=>{
            const coords={lat: pos.coords.latitude, lon: pos.coords.longitude, name:"Your Location", country:""};
            const data=await fetchWeatherFromCoords(coords); setWeatherData(data); setLocation(data.location);
          }, ()=>alert("Enable location access"))}>Use My Location</button>
        </div>

        <div style={{display:'flex', gap:'50px', flexWrap:'wrap', alignItems:'center'}}>
          <div style={{display:'flex', flexDirection:'column'}}>
            <label>Start Date</label>
            <input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)}/>
          </div>
          <div style={{display:'flex', flexDirection:'column'}}>
            <label>End Date</label>
            <input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)}/>
          </div>
          <button onClick={saveWeather}>{editId ? "Update Record" : "Save Record"}</button>

          {/* Export Buttons */}
          <button onClick={() => exportJSON(savedWeather)}>Export JSON</button>
          <button onClick={() => exportCSV(savedWeather)}>Export CSV</button>
          <button onClick={() => exportMarkdown(savedWeather)}>Export Markdown</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{marginTop:'20px', display:'flex', gap:'10px'}}>
        <button onClick={() => setActiveTab("weather")} style={{fontWeight: activeTab === "weather" ? "bold" : "normal"}}>Weather</button>
        <button onClick={() => setActiveTab("map")} style={{fontWeight: activeTab === "map" ? "bold" : "normal"}}>Map</button>
        <button onClick={() => setActiveTab("videos")} style={{fontWeight: activeTab === "videos" ? "bold" : "normal"}}>Videos</button>
      </div>

      {/* Conditional Displays */}
      {weatherData && activeTab === "weather" && (
        <div className="weather-card">
          <h2>{weatherData.location}</h2>
          <p><img src={`http://openweathermap.org/img/wn/${weatherData.icon}@2x.png`} alt={weatherData.description}/> {weatherData.description}</p>
          <p>Temp: {weatherData.temp_min}°C - {weatherData.temp_max}°C</p>
          <h3>5-Day Forecast</h3>
          <div className="forecast-container" style={{display:'flex', flexWrap:'wrap', gap:'10px', justifyContent:'center'}}>
            {weatherData.daily.map((d, i)=>(
              <div key={i} style={{flex:'1 1 40%', minWidth:'150px', background:'#e0f7fa', padding:'10px', borderRadius:'8px', textAlign:'center'}}>
                <p style={{fontWeight:'bold'}}>{formatDate(d.dt)}</p>
                <img src={`http://openweathermap.org/img/wn/${d.weather[0].icon}@2x.png`} alt={d.weather[0].description}/>
                <p>{d.weather[0].description}</p>
                <p>Min: {d.temp.min}°C</p><p>Max: {d.temp.max}°C</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "map" && mapUrl && (
        <div style={{marginTop:'20px'}}>
          <h3>Map</h3>
          <iframe width="100%" height="250" src={mapUrl} style={{borderRadius:'10px'}} allowFullScreen></iframe>
        </div>
      )}

      {activeTab === "videos" && youtubeVideos.length > 0 && (
        <div style={{marginTop:'20px'}}>
          <h3>Videos</h3>
          <div style={{display:'flex', flexWrap:'wrap', gap:'10px', justifyContent:'center'}}>
            {youtubeVideos.map(v=>(
              <div key={v.id.videoId} style={{flex:'1 1 30%', minWidth:'200px'}}>
                <iframe width="100%" height="150" src={`https://www.youtube.com/embed/${v.id.videoId}`} title={v.snippet.title} frameBorder="0" allowFullScreen></iframe>
                <p style={{textAlign:'center', fontWeight:'bold'}}>{v.snippet.title}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Saved Weather */}
      <h2>Saved Weather Records</h2>
      <div style={{display:'flex', flexDirection:'column', gap:'10px'}}>
        {savedWeather.map(rec=>(
          <div key={rec.id} style={{display:'flex', alignItems:'center', gap:'10px', border:'1px solid #ccc', borderRadius:'8px', padding:'10px', background:'#fafafa'}}>
            <p style={{minWidth:'120px', fontWeight:'bold'}}>{rec.location}</p>
            <div>
              <p>{rec.start_date} - {rec.end_date}</p>
              <p>Min: {rec.temp_min}°C, Max: {rec.temp_max}°C</p>
              <p>{rec.description}</p>
            </div>
            <button onClick={()=>editRecord(rec)}>Edit</button>
            <button onClick={()=>deleteRecord(rec.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
