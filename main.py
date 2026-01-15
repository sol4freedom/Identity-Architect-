from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

# --- BACKEND CONFIG ---
from flatlib.config import setBackend
setBackend(const.BACKEND_MOSHIER)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GENE KEYS DATA ---
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

def get_gene_key(degree):
    if degree is None: return 0
    index = int(degree / 5.625)
    if index >= 64: index = 0
    return RAVE_ORDER[index]

# --- ARCHETYPE LIBRARY ---
INTERPRETATIONS = {
    "Aries": "The Pioneer", "Taurus": "The Builder", "Gemini": "The Messenger",
    "Cancer": "The Nurturer", "Leo": "The Creator", "Virgo": "The Editor",
    "Libra": "The Diplomat", "Scorpio": "The Alchemist", "Sagittarius": "The Explorer",
    "Capricorn": "The Architect", "Aquarius": "The Futurist", "Pisces": "The Guide"
}

# --- INPUT DATA ---
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
        
        # We fetch ALL planets now
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # Get the Objects
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        mercury = chart.get(const.MERCURY)
        venus = chart.get(const.VENUS)
        mars = chart.get(const.MARS)
        jupiter = chart.get(const.JUPITER)
        saturn = chart.get(const.SATURN)
        uranus = chart.get(const.URANUS)
        neptune = chart.get(const.NEPTUNE)
        pluto = chart.get(const.PLUTO)
        
        rising = chart.get(const.HOUSE1)
        mc = chart.get(const.HOUSE10)

        # 3. CALCULATE GENE KEYS
        lifes_work_key = get_gene_key(sun.lon)
        evolution_key = get_gene_key((sun.lon + 180) % 360)

        # 4. GENERATE THE "NEIGHBORHOOD" HTML REPORT
        report_html = f"""
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #2D2D2D;">
            
            <div style="text-align: center; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #D4AF37; margin: 0; letter-spacing: 2px;">THE INTEGRATED SELF</h2>
                <span style="font-size: 14px; color: #888;">PREPARED FOR {data.name.upper()}</span>
            </div>

            <div style="background-color: #F9F9F9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #4A4A4A; margin-top: 0;">🗝️ THE CORE CODES</h3>
                <p><strong>🧬 Life's Work:</strong> <span style="color: #C71585; font-weight: bold;">Gene Key {lifes_work_key}</span> ({sun.sign})</p>
                <p><strong>🌍 Evolution:</strong> <span style="color: #C71585; font-weight: bold;">Gene Key {evolution_key}</span></p>
                <p><strong>🏹 Rising Sign:</strong> {rising.sign} ({INTERPRETATIONS.get(rising.sign)})</p>
            </div>

            <div style="border-left: 5px solid #2C3E50; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #2C3E50; margin: 0;">THE BOARDROOM</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">STRATEGY & GROWTH</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li>🤝 <strong>The Broker (Mercury):</strong> {mercury.sign}</li>
                    <li>👔 <strong>The CEO (Saturn):</strong> {saturn.sign}</li>
                    <li>💰 <strong>The Mogul (Jupiter):</strong> {jupiter.sign}</li>
                </ul>
            </div>

            <div style="border-left: 5px solid #27AE60; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #27AE60; margin: 0;">THE SANCTUARY</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">CONNECTION & CARE</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li>❤️ <strong>The Heart (Moon):</strong> {moon.sign}</li>
                    <li>🎨 <strong>The Muse (Venus):</strong> {venus.sign}</li>
                    <li>🌫️ <strong>The Dreamer (Neptune):</strong> {neptune.sign}</li>
                </ul>
            </div>

            <div style="border-left: 5px solid #C0392B; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #C0392B; margin: 0;">THE STREETS</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">POWER & DRIVE</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li>🔥 <strong>The Hustle (Mars):</strong> {mars.sign}</li>
                    <li>⚡ <strong>The Disruptor (Uranus):</strong> {uranus.sign}</li>
                    <li>🕵️ <strong>The Kingpin (Pluto):</strong> {pluto.sign}</li>
                </ul>
            </div>

            <div style="background-color: #F0F4F8; padding: 15px; border-radius: 8px; font-size: 14px; text-align: center; color: #555;">
                <p><strong>Current Struggle:</strong> {data.struggle}</p>
                <p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {INTERPRETATIONS.get(rising.sign)}.</em></p>
            </div>

        </div>
        """

        return {"report": report_html}

    except Exception as e:
        return {"report": f"<p style='color:red'>Calculation Error: {str(e)}</p>"}
