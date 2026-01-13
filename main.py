from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from geopy.geocoders import Nominatim # <--- The GPS Tool

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
        # We ask the internet: "Where is this city?"
        geolocator = Nominatim(user_agent="identity_architect_app")
        location = geolocator.geocode(data.city)
        
        if location:
            lat = location.latitude
            lon = location.longitude
        else:
            # Fallback if city not found (Default to Greenwich)
            lat = 51.48
            lon = 0.00
            
        # 2. CONFIGURE CHART
        # We feed the GPS (lat/lon) into the chart calculator
        date = Datetime(data.date.replace("-", "/"), data.time, data.tz)
        pos = GeoPos(lat, lon)
        chart = Chart(date, pos, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)

        # 3. GET KEY DATA POINTS
        sun = chart.get(const.SUN)
        rising = chart.get(const.ASC) # The Ascendant (Self)
        midheaven = chart.get(const.MC) # The Midheaven (Career/Legacy)
        house_2 = chart.get(const.HOUSE2) # Money/Assets

        # 4. GENERATE THE READOUT
        # This is where we interpret the math for the user
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Coordinates:**
        📍 Location: {data.city} ({lat:.2f}, {lon:.2f})
        
        **The Core You:**
        ☀️ **Sun Sign:** {sun.sign} (Your Essence)
        🏹 **Rising Sign:** {rising.sign} (Your Path)
        
        **Money & Career Codes:**
        💼 **Career (Midheaven):** {midheaven.sign}
        *This is the energy you are meant to bring to your public work.*
        
        💰 **Money (2nd House):** {house_2.sign}
        *This is the style in which you naturally generate resources.*
        
        **Current Focus:** {data.struggle}
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
