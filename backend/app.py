from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import datetime

app = Flask(__name__)
pp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'  # Relative path to SQLite DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, origins=["*"])


API_KEY = "04de74770f1697780a363fd798708378"
DB = SQLAlchemy(app)

# Initialize DB table
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            temp_min REAL,
            temp_max REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def validate_dates(start, end):
    try:
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        return start_date <= end_date
    except:
        return False

def get_weather(location, start_date, end_date):
    # For simplicity, fetch current weather from OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
    try:
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200:
            return {"temp_min": 0, "temp_max": 0, "description": "Unknown"}
        temp = data["main"]
        desc = data["weather"][0]["description"]
        return {
            "temp_min": temp["temp_min"] if "temp_min" in temp else temp["temp"],
            "temp_max": temp["temp_max"] if "temp_max" in temp else temp["temp"],
            "description": desc
        }
    except:
        return {"temp_min": 0, "temp_max": 0, "description": "Unknown"}

@app.route('/weather', methods=['POST'])
def create_weather():
    data = request.json
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not validate_dates(start_date, end_date):
        return jsonify({"error": "Invalid date range"}), 400

    weather = get_weather(location, start_date, end_date)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        INSERT INTO weather_requests (location, start_date, end_date, temp_min, temp_max, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (location, start_date, end_date, weather['temp_min'], weather['temp_max'], weather['description']))
    conn.commit()
    conn.close()

    return jsonify({"message": "Weather data saved", "data": weather})

@app.route('/weather', methods=['GET'])
def read_weather():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM weather_requests ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    result = [dict(r) for r in rows]
    return jsonify(result)

@app.route('/weather/<int:id>', methods=['PUT'])
def update_weather(id):
    data = request.json
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not validate_dates(start_date, end_date):
        return jsonify({"error": "Invalid date range"}), 400

    weather = get_weather(location, start_date, end_date)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        UPDATE weather_requests
        SET location=?, start_date=?, end_date=?, temp_min=?, temp_max=?, description=?
        WHERE id=?
    ''', (location, start_date, end_date, weather['temp_min'], weather['temp_max'], weather['description'], id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Weather record updated", "data": weather})

@app.route('/weather/<int:id>', methods=['DELETE'])
def delete_weather(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM weather_requests WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Record deleted"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
