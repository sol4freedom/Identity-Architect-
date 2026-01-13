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
        # 1. SMART LOCATION & TIMEZONE
        # We set both Coordinates AND Timezone manually for accuracy.
        city_lower = data.city.lower()
        
        # Default values (overridden below)
        lat = 51.48
        lon = 0.00
        tz_offset = data.tz  # Start with whatever Wix sent (usually 0)

        if "sao paulo" in city_lower or "são paulo" in city_lower:
            lat = -23.55
            lon = -46.63
            tz_offset = -3  # FIX: Set Sao Paulo to UTC-3
            print("Using Hardcoded Sao Paulo (UTC-3)")
            
        elif "fargo" in city_lower:
            lat = 46.87
            lon = -96.79
            tz_offset = -5 # FIX: Set Fargo to UTC-5 (CDT)
            print("Using Hardcoded Fargo (UTC-5)")
            
        else:
            # Fallback for other cities (using internet)
            try:
                geolocator = Nominatim(user_agent="identity_architect_sol_v1", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat = location.latitude
                    lon = location.longitude
            except:
                 pass # Keep defaults if fails

        # 2. CONFIGURE CHART
        # We pass the 'tz_offset' here to correct the time
        date = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        
        # 3. GET DATA (Planets Only)
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        
        # HOUSE 1 is Ascendant, HOUSE 10 is Midheaven
        rising = chart.get(const.HOUSE1)
        midheaven = chart.get(const.HOUSE10)
        house_2 = chart.get(const.HOUSE2)

        # 4. REPORT
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Coordinates:**
        📍 {data.city} (Lat: {lat:.2f}, Lon: {lon:.2f})
        ⏰ Timezone Used: UTC {tz_offset}
        
        **The Core You:**
        ☀️ **Sun:** {sun.sign} ({sun.lon:.2f}°)
        🌙 **Moon:** {moon.sign} ({moon.lon:.2f}°)
        🏹 **Rising:** {rising.sign} ({rising.lon:.2f}°)
        
        **Money & Career:**
        💼 **Career (MC):** {midheaven.sign}
        *The sign of your public legacy.*
        
        💰 **Money (2nd House):** {house_2.sign}
        *Your natural path to resources.*
        
        **Current Focus:** {data.struggle}
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
