import sqlite3

conn = sqlite3.connect('weather.db')
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
