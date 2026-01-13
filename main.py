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

    # 1. TIMEZONE FIXER
    @validator('tz', pre=True)
    def parse_timezone(cls, v):
        if v is None: return 0
        try:
            return float(v)
        except:
            return 0

    # 2. DATE FIXER
    @validator('date', pre=True)
    def clean_date(cls, v):
        if "T" in v: return v.split("T")[0]
        return v

    # 3. TIME FIXER (The New Magic Fix)
    @validator('time', pre=True)
    def clean_time(cls, v):
        # If it comes in as "07:30:00.000", chop off the dot
        if "." in v:
            v = v.split(".")[0] 
        # Ensure we just send HH:MM to be safe
        parts = v.split(":")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}"
        return v

@app.get("/")
def home():
    return {"message": "Server is Online"}

# --- THE ASTROLOGY ENGINE ---
@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received: {data}")

    try:
        # 1. Configure Location & Time
        # We assume UTC (0 offset) for now to ensure stability
        date = Datetime(data.date.replace("-", "/"), data.time, data.tz)
        pos = GeoPos(0, 0) 
        
        # 2. Calculate the Chart
        chart = Chart(date, pos)

        # 3. Get the Planets
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        mars = chart.get(const.MARS)
        mercury = chart.get(const.MERCURY)
        venus = chart.get(const.VENUS)

        # 4. Generate the Report
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Cosmic Blueprint:**
        ☀️ **Sun:** {sun.sign}
        🌙 **Moon:** {moon.sign}
        🔥 **Mars:** {mars.sign}
        💬 **Mercury:** {mercury.sign}
        ❤️ **Venus:** {venus.sign}
        
        **Current Focus:** {data.struggle}
        
        This chart was calculated for {data.date} at {data.time}.
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
