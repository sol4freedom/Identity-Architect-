from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
from geopy.geocoders import Nominatim

# --- ASTROLOGY IMPORTS ---
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

# --- SECURITY ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA SHAPE ---
class UserInput(BaseModel):
    name: str
    date: str
    time: str
    city: str
    struggle: str
    tz: Union[float, int, str, None] = None

    @validator('tz', pre=True)
    def parse_timezone(cls, v):
        if v is None: return 0
        try: return float(v)
        except: return 0

    @validator('date', pre=True)
    def clean_date(cls, v):
        if "T" in v: return v.split("T")[0]
        return v

    @validator('time', pre=True)
    def clean_time(cls, v):
        if "." in v: v = v.split(".")[0]
        parts = v.split(":")
        if len(parts) >= 2: return f"{parts[0]}:{parts[1]}"
        return v

@app.get("/")
def home():
    return {"message": "Server is Online"}

# --- THE CALCULATOR ---
@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received: {data}")

    try:
        # 1. GPS LOOKUP (Fixed Timeout)
        # We give it 10 seconds to find the city
        geolocator = Nominatim(user_agent="identity_architect_app", timeout=10)
        location = geolocator.geocode(data.city)
        
        if location:
            lat = location.latitude
            lon = location.longitude
        else:
            lat = 51.48
            lon = 0.00
            
        # 2. CONFIGURE CHART (Safe Mode)
        date = Datetime(data.date.replace("-", "/"), data.time, data.tz)
        pos = GeoPos(lat, lon)
        
        # CRITICAL FIX: We explicitly ask ONLY for planets.
        # This prevents the "Moshier cannot calculate Asteroids" crash.
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC, const.HOUSE2
        ]
        
        # We pass 'IDs=safe_objects' so it doesn't try to look for missing files
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # 3. GET DATA
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        rising = chart.get(const.ASC)
        midheaven = chart.get(const.MC)
        
        # 4. REPORT
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Coordinates:**
        📍 {data.city} ({lat:.2f}, {lon:.2f})
        
        **The Core You:**
        ☀️ **Sun:** {sun.sign} ({sun.lon:.2f}°)
        🌙 **Moon:** {moon.sign} ({moon.lon:.2f}°)
        🏹 **Rising:** {rising.sign} ({rising.lon:.2f}°)
        
        **Money & Career:**
        💼 **Career (MC):** {midheaven.sign}
        *The sign of your public legacy.*
        
        **Current Focus:** {data.struggle}
        
        *(Generated using Safe Mode Engine)*
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
