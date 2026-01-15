from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime 
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib.ephem import setBackend

# --- CONFIGURE BACKEND ---
try:
    setBackend(const.BACKEND_MOSHIER)
except: pass

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

# --- THE 64 ARCHETYPES (THE TRANSLATOR) ---
# Replaces "Gene Key X" with a descriptive title
KEY_NAMES = {
    1: "The Creator", 2: "The Receptive", 3: "The Innovator", 4: "The Logic Master",
    5: "The Fixer", 6: "The Peacemaker", 7: "The Leader", 8: "The Stylist",
    9: "The Focuser", 10: "The Self", 11: "The Idealist", 12: "The Articulate",
    13: "The Listener", 14: "The Power House", 15: "The Humanist", 16: "The Master",
    17: "The Opinion", 18: "The Improver", 19: "The Sensitive", 20: "The Now",
    21: "The Controller", 22: "The Grace", 23: "The Assimilator", 24: "The Rationalizer",
    25: "The Spirit", 26: "The Egoist", 27: "The Nurturer", 28: "The Risk Taker",
    29: "The Yes Man", 30: "The Passion", 31: "The Voice", 32: "The Conservative",
    33: "The Reteller", 34: "The Power", 35: "The Progress", 36: "The Crisis",
    37: "The Family", 38: "The Fighter", 39: "The Provocateur", 40: "The Aloneness",
    41: "The Fantasy", 42: "The Finisher", 43: "The Insight", 44: "The Alert",
    45: "The Gatherer", 46: "The Determination", 47: "The Realization", 48: "The Depth",
    49: "The Catalyst", 50: "The Values", 51: "The Shock", 52: "The Stillness",
    53: "The Starter", 54: "The Ambition", 55: "The Spirit", 56: "The Storyteller",
    57: "The Intuitive", 58: "The Joy", 59: "The Sexual", 60: "The Limitation",
    61: "The Mystery", 62: "The Detail", 63: "The Doubter", 64: "The Confusion"
}

def get_gene_key_name(degree):
    if degree is None: return "Unknown"
    index = int(degree / 5.625)
    if index >= 64: index = 0
    key_number = RAVE_ORDER[index]
    # Return just the name (e.g. "The Master") instead of "Gene Key 16"
    return KEY_NAMES.get(key_number, f"Archetype {key_number}")

# --- PLANET ARCHETYPES ---
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
                geolocator = Nominatim(user_agent="identity_architect_sol_v4", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat, lon = location.latitude, location.longitude
            except: pass

        # 2. CALCULATE ASTROLOGY (Personality/Black)
        date_obj = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        
        chart = Chart(date_obj, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # Get Objects
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
        
        # 3. CALCULATE DESIGN (Unconscious/Red)
        p_date = datetime.datetime.strptime(data.date, "%Y-%m-%d")
        d_date_obj = p_date - datetime.timedelta(days=88)
        d_date_str = d_date_obj.strftime("%Y/%m/%d")
        
        design_date_flatlib = Datetime(d_date_str, data.time, tz_offset)
        design_chart = Chart(design_date_flatlib, pos, IDs=[const.SUN, const.MOON], hsys=const.HOUSES_PLACIDUS)
        
        d_sun = design_chart.get(const.SUN)
        d_moon = design_chart.get(const.MOON)
        
        # 4. GET ARCHETYPE NAMES (No more Numbers!)
        lifes_work_name = get_gene_key_name(sun.lon)
        evolution_name = get_gene_key_name((sun.lon + 180) % 360)
        
        radiance_name = get_gene_key_name(d_sun.lon)
        purpose_name = get_gene_key_name((d_sun.lon + 180) % 360)
        attraction_name = get_gene_key_name(d_moon.lon)

        # 5. GENERATE REPORT (With Custom Category Names)
        report_html = (
            f'<div style="font-family: \'Helvetica Neue\', Helvetica, Arial, sans-serif; line-height: 1.6; color: #2D2D2D;">'
            
            f'<div style="text-align: center; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 20px;">'
            f'<h2 style="color: #D4AF37; margin: 0; letter-spacing: 2px;">THE INTEGRATED SELF</h2>'
            f'<span style="font-size: 14px; color: #888;">PREPARED FOR {data.name.upper()}</span>'
            f'</div>'
            
            f''
            f'<div style="background-color: #F9F9F9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
            f'<h3 style="color: #4A4A4A; margin-top: 0;">🗝️ THE CORE ID</h3>'
            f'<span style="font-size: 12px; color: #777; letter-spacing: 1px;">CONSCIOUS INTENT</span>'
            f'<p style="margin-top:10px;"><strong>🧬 The Calling:</strong> <span style="color: #C71585; font-weight: bold;">{lifes_work_name}</span> ({sun.sign})</p>'
            f'<p><strong>🌍 The Growth Edge:</strong> <span style="color: #C71585; font-weight: bold;">{evolution_name}</span></p>'
            f'<p><strong>🏹 The Path:</strong> {rising.sign} ({INTERPRETATIONS.get(rising.sign)})</p>'
            f'</div>'

            f''
            f'<div style="border-left: 5px solid #2C3E50; padding-left: 15px; margin-bottom: 20px;">'
            f'<h3 style="color: #2C3E50; margin: 0;">THE BOARDROOM</h3>'
            f'<span style="font-size: 12px; color: #777; letter-spacing: 1px;">STRATEGY & GROWTH</span>'
            f'<ul style="list-style: none; padding: 0; margin-top: 10px;">'
            f'<li>🤝 <strong>The Broker (Mercury):</strong> {mercury.sign}</li>'
            f'<li>👔 <strong>The CEO (Saturn):</strong> {saturn.sign}</li>'
            f'<li>💰 <strong>The Mogul (Jupiter):</strong> {jupiter.sign}</li>'
            f'</ul>'
            f'</div>'

            f''
            f'<div style="border-left: 5px solid #27AE60; padding-left: 15px; margin-bottom: 20px;">'
            f'<h3 style="color: #27AE60; margin: 0;">THE SANCTUARY</h3>'
            f'<span style="font-size: 12px; color: #777; letter-spacing: 1px;">CONNECTION & CARE</span>'
            f'<ul style="list-style: none; padding: 0; margin-top: 10px;">'
            f'<li>❤️ <strong>The Heart (Moon):</strong> {moon.sign}</li>'
            f'<li>🎨 <strong>The Muse (Venus):</strong> {venus.sign}</li>'
            f'<li>🌫️ <strong>The Dreamer (Neptune):</strong> {neptune.sign}</li>'
            f'</ul>'
            f'</div>'

            f''
            f'<div style="border-left: 5px solid #C0392B; padding-left: 15px; margin-bottom: 20px;">'
            f'<h3 style="color: #C0392B; margin: 0;">THE STREETS</h3>'
            f'<span style="font-size: 12px; color: #777; letter-spacing: 1px;">POWER & DRIVE</span>'
            f'<ul style="list-style: none; padding: 0; margin-top: 10px;">'
            f'<li>🔥 <strong>The Hustle (Mars):</strong> {mars.sign}</li>'
            f'<li>⚡ <strong>The Disruptor (Uranus):</strong> {uranus.sign}</li>'
            f'<li>🕵️ <strong>The Kingpin (Pluto):</strong> {pluto.sign}</li>'
            f'</ul>'
            f'</div>'
            
            f''
            f'<div style="background-color: #222; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
            f'<h3 style="color: #FF4500; margin-top: 0;">🔒 THE VAULT</h3>'
            f'<span style="font-size: 12px; color: #aaa; letter-spacing: 1px;">UNCONSCIOUS BLUEPRINT</span>'
            f'<p style="margin-top:10px;"><strong>⚡ The Aura (Radiance):</strong> <span style="color: #FFD700; font-weight: bold;">{radiance_name}</span></p>'
            f'<p><strong>⚓ The Root (Purpose):</strong> <span style="color: #FFD700; font-weight: bold;">{purpose_name}</span></p>'
            f'<p><strong>🧲 The Magnet:</strong> <span style="color: #FFD700; font-weight: bold;">{attraction_name}</span></p>'
            f'</div>'

            f'<div style="background-color: #F0F4F8; padding: 15px; border-radius: 8px; font-size: 14px; text-align: center; color: #555;">'
            f'<p><strong>Current Struggle:</strong> {data.struggle}</p>'
            f'<p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {INTERPRETATIONS.get(rising.sign)}.</em></p>'
            f'</div>'
            f'</div>'
        )

        return {"report": report_html}

    except Exception as e:
        return {"report": f"<p style='color:red'>Calculation Error: {str(e)}</p>"}
