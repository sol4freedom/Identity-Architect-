import sys, base64, datetime, json, logging, re
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- COMPACT DATA ---
CITY_DB = {"london": (51.5, -0.12, "Europe/London"), "new york": (40.7, -74.0, "America/New_York")}

LIFE_PATH_LORE = {
    1: "The Primal Leader. A destiny of independence and leading the tribe into a new era.",
    2: "The Peacemaker. A hero's journey to master the invisible threads of cooperation.",
    3: "The Creative Spark. A destiny to lift the heaviness of the world through expression.",
    4: "The Master Builder. A story of endurance, legacy, and building strong foundations.",
    5: "The Freedom Seeker. A path of radical adaptability and breaking chains.",
    6: "The Cosmic Guardian. A journey of responsibility and nurturing the tribe.",
    7: "The Mystic Sage. A solitary climb up the mountain of truth to find wisdom.",
    8: "The Sovereign. A destiny involving the mastery of money, power, and influence.",
    9: "The Humanitarian. A story of letting go and healing the world with compassion.",
    11: "The Illuminator. The lightning rod. Walking the line between genius and madness.",
    22: "The Master Architect. The bridge between heaven and earth, turning visions to reality.",
    33: "The Avatar of Love. The teacher of teachers, uplifting humanity through service."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. You block flow by fighting your nature. Align with Jupiter."),
    "relationship": ("The Quest for Connection", "Disharmony. You use a script not yours. Honor your Venus."),
    "purpose": ("The Quest for Meaning", "The Void. You look for a place, not a frequency. Stop doing, start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Running wrong software overheats the hardware. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. A unique design in a standard world. Trust your internal compass.")
}

LINE_LORE = {
    1: "Investigator (Foundation)", 2: "Natural (Hermit)", 3: "Experimenter (Explorer)",
    4: "Networker (Weaver)", 5: "Fixer (General)", 6: "Role Model (Sage)"
}

SIGN_LORE = {
    "Aries": "The Warrior", "Taurus": "The Builder", "Gemini": "The Messenger", "Cancer": "The Protector",
    "Leo": "The Radiant", "Virgo": "The Alchemist", "Libra": "The Diplomat", "Scorpio": "The Sorcerer",
    "Sagittarius": "The Philosopher", "Capricorn": "The Architect", "Aquarius": "The Revolutionary", "Pisces": "The Mystic"
}

KEY_LORE = {
    1: "The Creator (Spark)", 2: "The Receptive (Womb)", 3: "The Innovator (Chaos)", 4: "Logic Master (Formula)",
    5: "The Fixer (Rhythm)", 6: "Peacemaker (Diplomat)", 7: "The Leader (Guide)", 8: "The Stylist (Rebel)",
    9: "The Focuser (Detail)", 10: "The Self (Being)", 11: "Idealist (Light)", 12: "Articulate (Voice)",
    13: "Listener (Vault)", 14: "Power House (Fuel)", 15: "Humanist (Flow)", 16: "Master (Skill)",
    17: "Opinion (Eye)", 18: "Improver (Healer)", 19: "Sensitive (Barometer)", 20: "The Now (Clarity)",
    21: "Controller (Manager)", 22: "Grace (Open Door)", 23: "Assimilator (Razor)", 24: "Rationalizer (Inventor)",
    25: "Spirit (Shaman)", 26: "Egoist (Dealmaker)", 27: "Nurturer (Guardian)", 28: "Risk Taker (Daredevil)",
    29: "Devoted (Commitment)", 30: "Passion (Fire)", 31: "Voice (Elected)", 32: "Conservative (Root)",
    33: "Reteller (Historian)", 34: "Power (Giant)", 35: "Progress (Hunger)", 36: "Crisis (Survivor)",
    37: "Family (Glue)", 38: "Fighter (Warrior)", 39: "Provocateur (Poker)", 40: "Aloneness (Builder)",
    41: "Fantasy (Seed)", 42: "Finisher (Closer)", 43: "Insight (Breakthrough)", 44: "Alert (Instinct)",
    45: "Gatherer (Monarch)", 46: "Determination (Vessel)", 47: "Realization (Epiphany)", 48: "Depth (Well)",
    49: "Catalyst (Rebel)", 50: "Values (Custodian)", 51: "Shock (Thunder)", 52: "Stillness (Mountain)",
    53: "Starter (Pressure)", 54: "Ambition (Climber)", 55: "Spirit (Cup)", 56: "Storyteller (Wanderer)",
    57: "Intuitive (Ear)", 58: "Joy (Vitality)", 59: "Sexual (Breaker)", 60: "Limitation (Acceptance)",
    61: "Mystery (Knower)", 62: "Detail (Bridge)", 63: "Doubter (Question)", 64: "Confusion (Resolver)"
}

# --- HELPERS ---
def safe_get_date(date_input):
    if not date_input: return None
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

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
    return {0:25, 1:17, 2:21, 3:51, 4:42, 5:3, 6:27, 7:24, 8:2, 9:23, 10:8, 11:20, 12:16, 13:35, 14:45, 15:12, 16:15, 17:52, 18:39, 19:53, 20:62, 21:56, 22:31, 23:33, 24:7, 25:4, 26:29, 27:59, 28:40, 29:64, 30:47, 31:6, 32:46, 33:18, 34:48, 35:57, 36:32, 37:50, 38:28, 39:44, 40:1, 41:43, 42:14, 43:34, 44:9, 45:5, 46:26, 47:11, 48:10, 49:58, 50:38, 51:54, 52:61, 53:60, 54:41, 55:19, 56:13, 57:49, 58:30, 59:55, 60:37, 61:63, 62:22, 63:36}.get(int((d%360)/5.625), 1)

def resolve_loc(c):
    for k in CITY_DB:
        if k in str(c).lower(): return CITY_DB[k]
    try:
        g = Nominatim(user_agent="ia_v99")
        l = g.geocode(c)
        if l:
            from timezonefinder import TimezoneFinder
            return l.latitude, l.longitude, TimezoneFinder().timezone_at(lng=l.longitude, lat=l.latitude) or "UTC"
    except: pass
    return 51.50, -0.12, "Europe/London"

def get_tz(d, t, z):
    try:
        dt = datetime.datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
        return pytz.timezone(z).utcoffset(dt).total_seconds() / 3600.0
    except: return 0.0

def gen_chapters(name, chart, orient, lp, struggle):
    sun, moon, ris = chart['Sun'], chart['Moon'], chart['Rising']
    s_lore, m_lore, r_lore = SIGN_LORE.get(sun['Sign']), SIGN_LORE.get(moon['Sign']), SIGN_LORE.get(ris['Sign'])
    gate_name = KEY_LORE.get(sun['Gate'], "Energy")
    dragon, d_desc = struggle[0].replace("The Quest for ", ""), struggle[1]
    
    return [
        {"title": "🌟 THE ORIGIN", "body": f"The universe created a frequency named {name}. Born under {sun['Sign']} ({s_lore}), this is your core. But you wear the mask of {ris['Sign']} ({r_lore}). Your journey is to reconcile these two."},
        {"title": "❤️ THE HEART", "body": f"Beneath the armor lies your Moon in {moon['Sign']} ({m_lore}). This is your secret engine. Ignoring it drains you; honoring it regenerates you."},
        {"title": "🏔️ THE PATH", "body": f"Your road is Life Path {lp}. {LIFE_PATH_LORE.get(lp, '')} It is a steep climb, but the view is your purpose."},
        {"title": "⚔️ THE WEAPON", "body": f"Your superpower is Archetype {sun['Gate']}: {gate_name}. When trusted, doors open. It is the sword in your hand."},
        {"title": "🗺️ THE STRATEGY", "body": f"Your manual is {orient}. You are not designed to move like others. Trust your specific style to avoid frustration."},
        {"title": "🐉 THE DRAGON", "body": f"Your antagonist is {dragon}. {d_desc} This struggle is not a punishment, but the friction needed to sharpen your blade."}
    ]

def clean_txt(t):
    if not t: return ""
    t = re.sub(r'[^\x00-\x7F]+', '', t) 
    return t.replace("—", "-").replace("’", "'").encode('latin-1', 'replace').decode('latin-1')

def create_pdf(name, chaps, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 10, 'THE LEGEND OF YOU', 0, 1, 'C')
        pdf.set_font("Helvetica", 'I', 12)
        pdf.cell(0, 10, clean_txt(f"The Epic of {name}"), 0, 1, 'C')
        pdf.ln(10)
        
        for c in chaps:
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, clean_txt(c['title']), 0, 1)
            pdf.set_font("Helvetica", '', 11)
            pdf.multi_cell(0, 6, clean_txt(c['body']))
            pdf.ln(5)
            
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Planetary Inventory", 0, 1)
        pdf.ln(5)
        for k, v in chart.items():
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 8, clean_txt(f"{k}: {v['Sign']} (Archetype {v['Gate']})"), 0, 1)
            pdf.set_font("Helvetica", '', 10)
            pdf.multi_cell(0, 5, clean_txt(KEY_LORE.get(v['Gate'], "")))
            pdf.ln(2)
            
        return base64.b64encode(pdf.output()).decode('utf-8')
    except Exception as e:
        logger.error(f"PDF Fail: {e}")
        return ""

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
        off = get_tz(dob, tob, tz)
        dt = Datetime(dob.replace("-", "/"), tob, off)
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
            lp = sum([int(n) for n in dob if n.isdigit()])
            while lp > 9 and lp not in [11, 22, 33]: lp = sum(int(n) for n in str(lp))
        except: lp = 0
        
        s_data = STRUGGLE_LORE.get(struggle, STRUGGLE_LORE["general"])
        
        chaps = gen_chapters(name, c_data, orient, lp, s_data)
        pdf = create_pdf(name, chaps, c_data)
        
        grid_html = ""
        for c in chaps:
            grid_html += f"<div class='card'><h3>{c['title']}</h3><p>{c['body']}</p></div>"
            
        html = f"""
        <html><head><style>
        body {{ font-family: 'Helvetica', sans-serif; padding: 20px; background: #fdfdfd; }}
        h2 {{ text-align: center; color: #D4AF37; font-size: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; max-width: 1000px; margin: 0 auto; }}
        .card {{ background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #D4AF37; }}
        .card h3 {{ margin-top: 0; color: #2c3e50; font-size: 1.1rem; }}
        .btn {{ display: block; width: 200px; margin: 30px auto; padding: 12px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; }}
        </style></head><body>
        <h2>The Legend of {name}</h2>
        <div class="grid">{grid_html}</div>
        <a href="data:application/pdf;base64,{pdf}" download="The_Legend_of_You.pdf" class="btn">⬇️ DOWNLOAD PDF</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": "<h3>The stars are cloudy. Please try again.</h3>"}
