from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import datetime

app = FastAPI()

# --- VITAL: ALLOW WIX TO TALK TO THIS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains. For extra security, change "*" to your Wix URL later.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. THE DATA MODEL ---
# This defines what your Wix form sends to us
class UserRequest(BaseModel):
    name: str
    date: str  # Format: "YYYY-MM-DD"
    time: str  # Format: "HH:MM"
    tz: float  # Timezone offset (e.g., -5.0)
    struggle: str

# --- 2. THE LOGIC (The Math) ---
RAVE_MANDALA_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

def get_gate_and_line(lon):
    segment_size = 360 / 64
    index = int(lon / segment_size)
    adjusted_index = (index - 3) % 64 
    gate = RAVE_MANDALA_ORDER[adjusted_index]
    position_in_gate = lon % segment_size
    line = int((position_in_gate / segment_size) * 6) + 1
    return gate, line

def calculate_profile(date_str, time_str, tz_offset):
    # Hardcoded Lat/Lon (NYC) for prototype simplicity
    lat, lon = 40.71, -74.00 
    
    # Parse Date/Time
    dt_str = f"{date_str} {time_str}"
    try:
        date_obj = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    except ValueError:
        # Fallback for seconds if included
        date_obj = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

    geo = GeoPos(lat, lon)
    
    # Calculate Conscious
    chart_conscious = Chart(Datetime(date_obj.strftime('%Y/%m/%d'), date_obj.strftime('%H:%M'), f"{tz_offset}"), geo)
    
    # Calculate Unconscious (~88 days prior)
    design_date = date_obj - datetime.timedelta(days=88)
    chart_unconscious = Chart(Datetime(design_date.strftime('%Y/%m/%d'), design_date.strftime('%H:%M'), f"{tz_offset}"), geo)

    return {
        "Sun_Conscious": get_gate_and_line(chart_conscious.get(const.SUN).lon),
        "Earth_Conscious": get_gate_and_line(chart_conscious.get(const.EARTH).lon),
        "Sun_Unconscious": get_gate_and_line(chart_unconscious.get(const.SUN).lon),
        "Moon_Unconscious": get_gate_and_line(chart_unconscious.get(const.MOON).lon),
        "Mercury_Conscious": get_gate_and_line(chart_conscious.get(const.MERCURY).lon),
        "Venus_Conscious": get_gate_and_line(chart_conscious.get(const.VENUS).lon),
        "Mars_Unconscious": get_gate_and_line(chart_unconscious.get(const.MARS).lon),
        "Jupiter_Conscious": get_gate_and_line(chart_conscious.get(const.JUPITER).lon),
    }

def generate_report(struggle, data, name):
    life_work = data['Sun_Conscious'][0]
    core_wound = data['Mars_Unconscious'][0]
    mercury = data['Mercury_Conscious'][0]
    pearl = data['Jupiter_Conscious'][0]
    
    # Note: Using \n for newlines so it formats correctly in Wix Text Boxes
    report = f"THE ORIGIN CODE AUDIT FOR {name.upper()}\n\n"
    
    if struggle == "Passion":
        report += f"DIAGNOSIS: You are looking for a job title instead of an energy frequency.\n\n"
        report += f"YOUR COORDINATES: Life's Work Gene Key: {life_work}\n"
        report += f"PRESCRIPTION: Stop looking externally. Audit your day for when you feel the energy of Key {life_work}. That is your compass."

    elif struggle == "Toxic Relationships":
        report += f"DIAGNOSIS: You are mechanically re-playing a wound.\n\n"
        report += f"YOUR COORDINATES: Core Wound Gene Key: {core_wound}\n"
        report += f"PRESCRIPTION: You attract partners who trigger Key {core_wound} because your soul wants to heal it. Observe the trigger, don't react to it."

    elif struggle == "Overthinking":
        report += f"DIAGNOSIS: Your mind is trying to solve a puzzle it wasn't designed to hold.\n\n"
        report += f"YOUR COORDINATES: Mental Processor Gene Key: {mercury}\n"
        report += f"PRESCRIPTION: Use the R.I.D. Wave Protocol. Your mind (Key {mercury}) is a tool for communication, not anxiety."
        
    elif struggle == "Money/Career":
        report += f"DIAGNOSIS: You are working against your prosperity flow.\n\n"
        report += f"YOUR COORDINATES: Prosperity Pearl Gene Key: {pearl}\n"
        report += f"PRESCRIPTION: You don't need to hustle harder. You need to align with the frequency of Key {pearl}."

    else:
        report += "DIAGNOSIS: General misalignment detected. Initiate the R.I.D. Protocol."
        
    return report

# --- 3. THE ENDPOINT (The Doorway) ---
@app.post("/calculate")
async def calculate(request: UserRequest):
    try:
        # 1. Calculate Chart
        chart_data = calculate_profile(request.date, request.time, request.tz)
        
        # 2. Generate Text
        report_text = generate_report(request.struggle, chart_data, request.name)
        
        # 3. Return JSON to Wix
        return {"report": report_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run locally for testing:
# uvicorn main:app --reload
