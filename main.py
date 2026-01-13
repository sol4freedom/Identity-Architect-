from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from geopy.geocoders import Nominatim

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

# --- THE ASTROLOGY ENGINE ---
@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received: {data}")

    try:
        # 1. GET GPS COORDINATES
        geolocator = Nominatim(user_agent="identity_architect_app")
        location = geolocator.geocode(data.city)
        
        if location:
            lat = location.latitude
            lon = location.longitude
        else:
            lat = 51.48
            lon = 0.00
            
        # 2. CONFIGURE CHART
        date = Datetime(data.date.replace("-", "/"), data.time, data.tz)
        pos = GeoPos(lat, lon)
        
        # *** THE FIX: ONLY ASK FOR PLANETS (NO ASTEROIDS) ***
        # This prevents the 'seas_18.se1' file error
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC
        ]
        
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # 3. GET DATA POINTS
        sun = chart.get(const.SUN)
        rising = chart.get(const.ASC)
        midheaven = chart.get(const.MC)
        house_2 = chart.get(const.HOUSE2)

        # 4. GENERATE REPORT
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Coordinates:**
        📍 Location: {data.city} ({lat:.2f}, {lon:.2f})
        
        **The Core You:**
        ☀️ **Sun Sign:** {sun.sign}
        🏹 **Rising Sign:** {rising.sign}
        
        **Money & Career Codes:**
        💼 **Career (Midheaven):** {midheaven.sign}
        *The energy of your public legacy.*
        
        💰 **Money (2nd House):** {house_2.sign}
        *Your natural path to resources.*
        
        **Current Focus:** {data.struggle}
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
