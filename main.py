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

# --- THE WISDOM LIBRARY (The "Translator") ---
# This matches Signs to Meanings based on the placement (Sun vs Career vs Money)
INTERPRETATIONS = {
    "Aries": {
        "Sun": "The Pioneer. You are here to start things and lead with courage.",
        "Rising": "You meet the world with action. Your path opens when you take a risk.",
        "Career": "The Warrior Leader. You thrive in high-stakes, independent roles.",
        "Money": "You generate wealth through quick action and entrepreneurial ventures."
    },
    "Taurus": {
        "Sun": "The Builder. You are here to ground energy and create lasting value.",
        "Rising": "You meet the world with stability. Your path opens when you slow down.",
        "Career": "The Artisan. You thrive building things of quality and tangible worth.",
        "Money": "You generate wealth through accumulation, assets, and steady growth."
    },
    "Gemini": {
        "Sun": "The Messenger. You are here to connect ideas and people.",
        "Rising": "You meet the world with curiosity. Your path opens when you ask questions.",
        "Career": "The Broadcaster. You thrive in media, teaching, or connecting networks.",
        "Money": "You generate wealth through multiple streams, communication, and trade."
    },
    "Cancer": {
        "Sun": "The Nurturer. You are here to protect and grow what matters.",
        "Rising": "You meet the world with feeling. Your path opens when you trust intuition.",
        "Career": "The Guardian. You thrive in roles that support, heal, or shelter others.",
        "Money": "You generate wealth through family, real estate, or emotional connection."
    },
    "Leo": {
        "Sun": "The Creator. You are here to shine and express your unique self.",
        "Rising": "You meet the world with radiance. Your path opens when you are seen.",
        "Career": "The Star. You thrive in leadership, performance, or creative direction.",
        "Money": "You generate wealth through personal branding, creativity, and risk."
    },
    "Virgo": {
        "Sun": "The Alchemist. You are here to refine and perfect the details.",
        "Rising": "You meet the world with analysis. Your path opens when you serve.",
        "Career": "The Editor. You thrive in systems, health, and optimizing processes.",
        "Money": "You generate wealth through service, precision, and skilled craft."
    },
    "Libra": {
        "Sun": "The Harmonizer. You are here to bring balance and beauty.",
        "Rising": "You meet the world with grace. Your path opens through partnership.",
        "Career": "The Diplomat. You thrive in law, design, or mediation.",
        "Money": "You generate wealth through partnerships, art, and client relations."
    },
    "Scorpio": {
        "Sun": "The Transformer. You are here to dive deep and reveal truth.",
        "Rising": "You meet the world with intensity. Your path opens when you let go.",
        "Career": "The Detective. You thrive in research, psychology, or crisis management.",
        "Money": "You generate wealth through investments, transformation, and shared resources."
    },
    "Sagittarius": {
        "Sun": "The Explorer. You are here to seek truth and expand horizons.",
        "Rising": "You meet the world with optimism. Your path opens when you explore.",
        "Career": "The Philosopher. You thrive in publishing, travel, or teaching wisdom.",
        "Money": "You generate wealth through teaching, international ventures, or vision."
    },
    "Capricorn": {
        "Sun": "The Architect. You are here to build structures that last.",
        "Rising": "You meet the world with authority. Your path opens when you commit.",
        "Career": "The CEO. You thrive in hierarchy, management, and long-term strategy.",
        "Money": "You generate wealth through discipline, reputation, and hard work."
    },
    "Aquarius": {
        "Sun": "The Visionary. You are here to innovate and break norms.",
        "Rising": "You meet the world with originality. Your path opens when you rebel.",
        "Career": "The Futurist. You thrive in tech, social change, or groups.",
        "Money": "You generate wealth through networks, innovation, and unique ideas."
    },
    "Pisces": {
        "Sun": "The Mystic. You are here to dream and dissolve boundaries.",
        "Rising": "You meet the world with empathy. Your path opens when you surrender.",
        "Career": "The Guide. You thrive in spiritual, artistic, or healing roles.",
        "Money": "You generate wealth through intuition, art, or charitable work."
    }
}

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
        city_lower = data.city.lower()
        lat = 51.48
        lon = 0.00
        tz_offset = data.tz

        if "sao paulo" in city_lower or "são paulo" in city_lower:
            lat = -23.55
            lon = -46.63
            tz_offset = -3
        elif "fargo" in city_lower:
            lat = 46.87
            lon = -96.79
            tz_offset = -5
        else:
            try:
                geolocator = Nominatim(user_agent="identity_architect_sol_v1", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat = location.latitude
                    lon = location.longitude
            except: pass

        # 2. CALCULATE
        date = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        chart = Chart(date, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # 3. GET SIGNS
        sun_sign = chart.get(const.SUN).sign
        moon_sign = chart.get(const.MOON).sign
        rising_sign = chart.get(const.HOUSE1).sign
        mc_sign = chart.get(const.HOUSE10).sign
        house2_sign = chart.get(const.HOUSE2).sign

        # 4. TRANSLATE (The Wisdom Step)
        # We look up the English meaning from the dictionary above
        sun_meaning = INTERPRETATIONS.get(sun_sign, {}).get("Sun", "Shine bright.")
        rising_meaning = INTERPRETATIONS.get(rising_sign, {}).get("Rising", "Follow your path.")
        career_meaning = INTERPRETATIONS.get(mc_sign, {}).get("Career", "Build your legacy.")
        money_meaning = INTERPRETATIONS.get(house2_sign, {}).get("Money", "Create resources.")

        # 5. GENERATE REPORT
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Your Core Energy:**
        ☀️ **Sun in {sun_sign}:** {sun_meaning}
        🏹 **Rising in {rising_sign}:** {rising_meaning}
        
        **Your Path to Success (Money/Career):**
        💼 **Career Style ({mc_sign}):** {career_meaning}
        *This is the energy you must embody to find fulfillment in work.*
        
        💰 **Money Path ({house2_sign}):** {money_meaning}
        *This is your natural way of attracting resources.*
        
        **Coaching Insight:**
        You mentioned your struggle is **{data.struggle}**. 
        To overcome this, look at your Rising Sign ({rising_sign}). 
        {rising_meaning}
        """

        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"report": f"Calculation Error: {str(e)}"}
