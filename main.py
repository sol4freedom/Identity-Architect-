import sys, base64, datetime, json, logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATA: LOCATIONS ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- 2. DATA: THE TRANSLATOR (Hard Coded Map) ---
# This ensures 0 degrees Aries ALWAYS equals Gate 25.
def get_gate_from_degree(degree):
    if degree is None: return 1
    # Normalize to 0-360
    if degree < 0 or degree >= 360: degree = degree % 360
    
    # Each gate is 5.625 degrees
    step = int(degree / 5.625)
    
    # 0 = Aries Start, 63 = Pisces End
    gate_map = {
        0: 25, 1: 17, 2: 21, 3: 51, 4: 42, 5: 3, 6: 27, 7: 24,   # Aries
        8: 2, 9: 23, 10: 8, 11: 20, 12: 16, 13: 35, 14: 45, 15: 12, # Taurus
        16: 15, 17: 52, 18: 39, 19: 53, 20: 62, 21: 56, 22: 31, 23: 33, # Cancer
        24: 7, 25: 4, 26: 29, 27: 59, 28: 40, 29: 64, 30: 47, 31: 6, # Leo
        32: 46, 33: 18, 34: 48, 35: 57, 36: 32, 37: 50, 38: 28, 39: 44, # Libra
        40: 1, 41: 43, 42: 14, 43: 34, 44: 9, 45: 5, 46: 26, 47: 11, # Sag
        48: 10, 49: 58, 50: 38, 51: 54, 52: 61, 53: 60, 54: 41, 55: 19, # Cap
        56: 13, 57: 49, 58: 30, 59: 55, 60: 37, 61: 63, 62: 22, 63: 36  # Pisces
    }
    return gate_map.get(step, 1)

# --- 3. LOGIC ENGINES ---
def safe_get_date(date_input):
    if not date_input: return datetime.date.today().strftime("%Y-%m-%d")
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def resolve_location(city_name):
    city_lower = str(city_name).lower().strip()
    for key in CITY_DB:
        if key in city_lower: return CITY_DB[key]
    try:
        geolocator = Nominatim(user_agent="ia_debug_v1")
        loc = geolocator.geocode(city_name)
        if loc:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=loc.longitude, lat=loc.latitude) or "UTC"
            return loc.latitude, loc.longitude, tz
    except: pass
    return 51.50, -0.12, "Europe/London"

def get_tz_offset(date_str, time_str, tz_name):
    try:
        local = pytz.timezone(tz_name)
        dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        offset = local.utcoffset(dt).total_seconds() / 3600.0
        return offset
    except: return 0.0

# --- 4. API ENDPOINT (THE DIAGNOSTIC) ---
@app.post("/calculate")
async def calculate_chart(request: Request):
    data = {}
    try:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct: data = await request.json()
        else: data = dict(await request.form())
    except: pass
    
    name = data.get("name") or "Traveler"
    dob = safe_get_date(data.get("dob"))
    tob = data.get("tob") or "12:00"
    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"

    debug_log = []

    try:
        # 1. Resolve Location
        lat, lon, tz_name = resolve_location(city)
        tz_offset = get_tz_offset(dob, tob, tz_name)
        
        debug_log.append(f"📍 Location Found: {lat}, {lon} (Timezone: {tz_name}, Offset: {tz_offset})")

        # 2. Translate Input for Library
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        
        debug_log.append(f"📤 Sent to Library: {dob} {tob} (Offset {tz_offset})")

        # 3. Call The Library
        chart = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        # 4. Get the Raw Output
        sun_obj = chart.get(const.SUN)
        moon_obj = chart.get(const.MOON)
        asc_obj = chart.get(const.ASC)

        # 5. Translate Back (The Math Check)
        sun_gate = get_gate_from_degree(sun_obj.lon)
        moon_gate = get_gate_from_degree(moon_obj.lon)
        asc_gate = get_gate_from_degree(asc_obj.lon)

        debug_log.append(f"📥 Library Sun: {sun_obj.sign} at {sun_obj.lon:.2f}° --> Map says Gate {sun_gate}")
        debug_log.append(f"📥 Library Moon: {moon_obj.sign} at {moon_obj.lon:.2f}° --> Map says Gate {moon_gate}")

    except Exception as e:
        debug_log.append(f"❌ ERROR: {str(e)}")
        sun_obj, sun_gate = None, 1
        moon_obj, moon_gate = None, 1
        asc_obj, asc_gate = None, 1

    # --- RENDER THE DIAGNOSTIC REPORT ---
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
        .card {{ background: #fff; padding: 20px; border: 1px solid #ddd; margin-bottom: 20px; border-radius: 8px; }}
        .debug {{ background: #222; color: #0f0; padding: 15px; font-family: monospace; border-radius: 5px; }}
        h2 {{ margin-top: 0; }}
    </style>
    </head>
    <body>
        <div class="card">
            <h2>🔮 The Integrated Self (Diagnostic Mode)</h2>
            <p><strong>Prepared for:</strong> {name}</p>
        </div>

        <div class="card">
            <h3>☀️ Sun</h3>
            <p><strong>Sign:</strong> {sun_obj.sign if sun_obj else 'Error'}</p>
            <p><strong>Gate:</strong> {sun_gate}</p>
            
            <h3>🌙 Moon</h3>
            <p><strong>Sign:</strong> {moon_obj.sign if moon_obj else 'Error'}</p>
            <p><strong>Gate:</strong> {moon_gate}</p>
            
            <h3>🏹 Rising</h3>
            <p><strong>Sign:</strong> {asc_obj.sign if asc_obj else 'Error'}</p>
            <p><strong>Gate:</strong> {asc_gate}</p>
        </div>

        <div class="card debug">
            <h3>🔧 UNDER THE HOOD (DEBUG LOG)</h3>
            <ul style="list-style:none; padding:0;">
                {''.join(f'<li>{line}</li>' for line in debug_log)}
            </ul>
        </div>
    </body>
    </html>
    """
    return {"report": html}
