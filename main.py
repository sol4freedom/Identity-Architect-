import sys, base64, datetime, json, logging, re, io
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import pytz

# --- REPORTLAB PDF ENGINE ---
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- LORE DATABASES ---
CITY_DB = {
    "minneapolis": (44.97, -93.26, "America/Chicago"), "london": (51.50, -0.12, "Europe/London"),
    "new york": (40.71, -74.00, "America/New_York"), "ashland": (42.19, -122.70, "America/Los_Angeles"),
    "los angeles": (34.05, -118.24, "America/Los_Angeles"), "sao paulo": (-23.55, -46.63, "America/Sao_Paulo")
}

LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first.",
    2: "The Peacemaker. You are the diplomat of the soul.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy.",
    4: "The Master Builder. You are the architect of the future.",
    5: "The Freedom Seeker. You are the wind that cannot be caged.",
    6: "The Cosmic Guardian. You are the protector of the hearth.",
    7: "The Mystic Sage. You are the walker between worlds.",
    8: "The Sovereign. You are the CEO of the material plane.",
    9: "The Humanitarian. You are the old soul on one last mission.",
    11: "The Illuminator. You are the lightning rod.",
    22: "The Master Architect. You are the bridge between heaven and earth.",
    33: "The Avatar of Love. You are the teacher of teachers."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. Wealth is a frequency. Align with your Jupiter sign."),
    "relationship": ("The Quest for Connection", "Disharmony. Honor your Venus placement to magnetize your tribe."),
    "purpose": ("The Quest for Meaning", "The Void. Your North Node defines your signal. Stop doing and start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Your Saturn placement holds your boundaries. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. Your Rising Sign is your compass. Return to your core strategy.")
}

LINE_LORE = {1:"The Investigator", 2:"The Natural", 3:"The Experimenter", 4:"The Networker", 5:"The Fixer", 6:"The Role Model"}

SIGN_LORE = {
    "Aries": "The Warrior", "Taurus": "The Builder", "Gemini": "The Messenger", "Cancer": "The Protector",
    "Leo": "The Radiant", "Virgo": "The Alchemist", "Libra": "The Diplomat", "Scorpio": "The Sorcerer",
    "Sagittarius": "The Philosopher", "Capricorn": "The Architect", "Aquarius": "The Revolutionary", "Pisces": "The Mystic"
}

KEY_LORE = {
    1: "The Creator", 2: "The Receptive", 3: "The Innovator", 4: "The Logic Master", 5: "The Fixer",
    6: "The Peacemaker", 7: "The Leader", 8: "The Stylist", 9: "The Focuser", 10: "The Self",
    11: "The Idealist", 12: "The Articulate", 13: "The Listener", 14: "The Power House", 15: "The Humanist",
    16: "The Master", 17: "The Opinion", 18: "The Improver", 19: "The Sensitive", 20: "The Now",
    21: "The Controller", 22: "The Grace", 23: "The Assimilator", 24: "The Rationalizer", 25: "The Spirit",
    26: "The Egoist", 27: "The Nurturer", 28: "The Risk Taker", 29: "The Devoted", 30: "The Passion",
    31: "The Voice", 32: "The Conservative", 33: "The Reteller", 34: "The Power", 35: "The Progress",
    36: "The Crisis", 37: "The Family", 38: "The Fighter", 39: "The Provocateur", 40: "The Aloneness",
    41: "The Fantasy", 42: "The Finisher", 43: "The Insight", 44: "The Alert", 45: "The Gatherer",
    46: "The Determination", 47: "The Realization", 48: "The Depth", 49: "The Catalyst", 50: "The Values",
    51: "The Shock", 52: "The Stillness", 53: "The Starter", 54: "The Ambition", 55: "The Spirit",
    56: "The Storyteller", 57: "The Intuitive", 58: "The Joy", 59: "The Sexual", 60: "The Limitation",
    61: "The Mystery", 62: "The Detail", 63: "The Doubter", 64: "The Confusion"
}

# --- HELPERS ---
def safe_get_date(d):
    if not d: return None
    return str(d).split("T")[0]

def clean_time(t):
    if not t: return "12:00"
    s = str(t).upper().strip()
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if "PM" in s and h < 12: h += 12
        if "AM" in s and h == 12: h = 0
        return f"{h:02d}:{mn:02d}"
    return "12:00"

def get_gate(d):
    if d is None: return 1
    gates = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
    return gates[int((d%360)/5.625)]

def resolve_loc(c):
    for k in CITY_DB:
        if k in str(c).lower(): return CITY_DB[k]
    try:
        g = Nominatim(user_agent="ia_app_v2")
        l = g.geocode(c)
        if l:
            from timezonefinder import TimezoneFinder
            return l.latitude, l.longitude, TimezoneFinder().timezone_at(lng=l.longitude, lat=l.latitude) or "UTC"
    except: pass
    return 51.50, -0.12, "Europe/London"

# --- PDF BUILDER ---
def create_pdf(name, chaps, chart):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], alignment=1, spaceAfter=20, fontSize=24, textColor=HexColor("#D4AF37"))
    header_style = ParagraphStyle('ChapterHead', parent=styles['Heading2'], spaceBefore=15, spaceAfter=10, fontSize=16, textColor=HexColor("#2c3e50"))
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], spaceAfter=12, fontSize=11, leading=14)

    story.append(Spacer(1, 60))
    story.append(Paragraph("THE LEGEND OF YOU", title_style))
    story.append(Paragraph(f"The Epic of {name}", styles['Italic']))
    story.append(Spacer(1, 40))
    story.append(PageBreak())

    for c in chaps:
        story.append(Paragraph(c['title'], header_style))
        # Support bolding and line breaks in PDF
        clean_body = c['body'].replace("**", "<b>", 1).replace("**", "</b>", 1).replace("\n", "<br/>")
        story.append(Paragraph(clean_body, body_style))
    
    story.append(PageBreak())
    
    story.append(Paragraph("Planetary Inventory", header_style))
    for k, v in chart.items():
        txt = f"<b>{k}:</b> {v['Sign']} (Archetype {v['Gate']}) - {KEY_LORE.get(v['Gate'], '')}"
        story.append(Paragraph(txt, body_style))

    doc.build(story)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# --- MAIN ENDPOINT ---
@app.post("/calculate")
async def calculate(request: Request):
    d = await request.json()
    name = d.get("name", "Traveler")
    dob = safe_get_date(d.get("dob") or d.get("date")) or datetime.date.today().strftime("%Y-%m-%d")
    tob = clean_time(d.get("tob") or d.get("time"))
    city = d.get("city", "London")
    struggle = d.get("struggle", "general")

    try:
        lat, lon, tz = resolve_loc(city)
        dt = Datetime(dob.replace("-", "/"), tob, 0)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        c_data = {}
        for p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            obj = chart.get(getattr(const, p.upper()))
            c_data[p] = {"Sign": obj.sign, "Gate": get_gate(obj.lon)}
        
        asc = chart.get(const.ASC)
        c_data["Rising"] = {"Sign": asc.sign, "Gate": get_gate(asc.lon)}
        
        p_sun = chart.get(const.SUN)
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1
        d_line = (int(((p_sun.lon - 88) % 360) / 0.9375) % 6) + 1
        orient = f"{LINE_LORE.get(p_line, '')} / {LINE_LORE.get(d_line, '')}"
        
        try:
            lp = sum([int(n) for n in dob if n
