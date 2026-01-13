from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
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
        try:
            return float(v)
        except:
            return 0

    @validator('date', pre=True)
    def clean_date(cls, v):
        if "T" in v: return v.split("T")[0]
        return v

@app.get("/")
def home():
    return {"message": "Server is Online"}

# --- THE ASTROLOGY ENGINE ---
@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received: {data}")

    try:
        # 1. Parse Date and Time
        # Format: 2024/01/01
        date_parts = data.date.split("-")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])

        # Format: 14:30
        time_parts = data.time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])

        # 2. Configure Location & Time (Using 'flatlib')
        # (For this test, we default to 0,0 lat/long if we don't have it yet)
        date = Datetime(data.date.replace("-", "/"), data.time, data.tz)
        pos = GeoPos(0, 0) 
        
        # 3. Calculate the Chart
        chart = Chart(date, pos)

        # 4. Get the Planets
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        mars = chart.get(const.MARS)

        # 5. Generate the Report
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Blueprint:**
        ☀️ **Sun Sign:** {sun.sign} (The Conscious Self)
        🌙 **Moon Sign:** {moon.sign} (The Emotional Self)
        🔥 **Mars Sign:** {mars.sign} (Your Drive & Passion)
        
        **Current Focus:** {data.struggle}
        
        This is a REAL calculation based on your birth date: {data.date}.
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
