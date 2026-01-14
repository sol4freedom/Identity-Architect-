from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE RAVE MANDALA (Degree to Gene Key) ---
# Order of Gates starting from Aries 0°
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

def get_gene_key(degree):
    # Each gate is exactly 5.625 degrees
    index = int(degree / 5.625)
    # Handle wrap-around just in case
    if index >= 64: index = 0
    return RAVE_ORDER[index]

# --- MEANING LIBRARY ---
INTERPRETATIONS = {
    "Aries": "The Pioneer", "Taurus": "The Builder", "Gemini": "The Messenger",
    "Cancer": "The Nurturer", "Leo": "The Creator", "Virgo": "The Editor",
    "Libra": "The Diplomat", "Scorpio": "The Alchemist", "Sagittarius": "The Explorer",
    "Capricorn": "The Architect", "Aquarius": "The Futurist", "Pisces": "The Guide"
}

# --- INPUT DATA SHAPE ---
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

@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        # 1. SMART LOCATION
        city_lower = data.city.lower()
        lat, lon, tz_offset = 51.48, 0.00, data.tz

        if "sao paulo" in city_lower or "são paulo" in city_lower:
            lat, lon, tz_offset = -23.55, -46.63, -3
        elif "fargo" in city_lower:
            lat, lon, tz_offset = 46.87, -96.79, -5
        else:
            try:
                geolocator = Nominatim(user_agent="identity_architect_sol_v1", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat, lon = location.latitude, location.longitude
            except: pass

        # 2. CALCULATE ASTROLOGY
        date = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        safe_objects = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        rising = chart.get(const.HOUSE1)
        mc = chart.get(const.HOUSE10)
        house2 = chart.get(const.HOUSE2)

        # 3. CALCULATE GENE KEYS
        # Life's Work = Sun Position
        lifes_work_key = get_gene_key(sun.lon)
        
        # Evolution = Earth Position (Sun + 180 degrees)
        earth_lon = (sun.lon + 180) % 360
        evolution_key = get_gene_key(earth_lon)

        # 4. PREPARE THE ELEGANT HTML REPORT
        # We use HTML styles (colors, fonts, spacing) to make it look professional.
        
        report_html = f"""
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #2D2D2D;">
            
            <div style="text-align: center; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #D4AF37; margin: 0; letter-spacing: 2px;">THE INTEGRATED SELF</h2>
                <span style="font-size: 14px; color: #888;">PREPARED FOR {data.name.upper()}</span>
            </div>

            <div style="background-color: #F9F9F9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #4A4A4A; margin-top: 0;">🗝️ YOUR GENE KEYS</h3>
                <p>
                    <strong>🧬 Life's Work (Sun):</strong> <span style="color: #C71585; font-weight: bold;">Gene Key {lifes_work_key}</span><br>
                    <span style="font-size: 14px; color: #666;">The quality you are here to manifest in the world.</span>
                </p>
                <p>
                    <strong>🌍 Evolution (Earth):</strong> <span style="color: #C71585; font-weight: bold;">Gene Key {evolution_key}</span><br>
                    <span style="font-size: 14px; color: #666;">The challenge that helps you grow.</span>
                </p>
            </div>

            <div style="margin-bottom: 20px;">
                <h3 style="color: #4A4A4A;">🔮 COSMIC ARCHITECTURE</h3>
                <ul style="list-style-type: none; padding: 0;">
                    <li style="margin-bottom: 10px;">
                        ☀️ <strong>Core Self (Sun):</strong> {sun.sign} - <em>{INTERPRETATIONS.get(sun.sign, 'The Essence')}</em>
                    </li>
                    <li style="margin-bottom: 10px;">
                        🏹 <strong>The Path (Rising):</strong> {rising.sign} - <em>{INTERPRETATIONS.get(rising.sign, 'The Mask')}</em>
                    </li>
                    <li style="margin-bottom: 10px;">
                        🌙 <strong>Inner World (Moon):</strong> {moon.sign} - <em>{INTERPRETATIONS.get(moon.sign, 'The Emotions')}</em>
                    </li>
                </ul>
            </div>

            <div style="background-color: #F0F4F8; padding: 20px; border-radius: 8px; border-left: 5px solid #4682B4;">
                <h3 style="color: #4682B4; margin-top: 0;">🚀 CAREER & ABUNDANCE</h3>
                <p>
                    <strong>💼 Your Legacy (Midheaven in {mc.sign}):</strong><br>
                    {INTERPRETATIONS.get(mc.sign, "Build your legacy.")}
                </p>
                <p>
                    <strong>💰 Your Wealth Style (2nd House in {house2.sign}):</strong><br>
                    You attract resources through {house2.sign} energy.
                </p>
            </div>

            <div style="margin-top: 20px; font-size: 14px; color: #999; text-align: center;">
                Generated for {data.city} • Focus: {data.struggle}
            </div>
        </div>
        """

        return {"report": report_html}

    except Exception as e:
        return {"report": f"<p style='color:red'>Calculation Error: {str(e)}</p>"}
