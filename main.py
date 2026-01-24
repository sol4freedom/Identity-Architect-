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

# --- DATA: LOCATIONS ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- DATA: LIFE PATH ---
LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone, conquer self-doubt, and lead the tribe.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master the invisible threads that connect people.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world.",
    4: "The Master Builder. You are the architect of the future. Your story is one of endurance and legacy.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money and influence.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness.",
    22: "The Master Architect. You are the bridge between heaven and earth. You turn visions into reality.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift humanity."
}

# --- DATA: STRUGGLE ---
STRUGGLE_LORE = {
    "wealth": {"title": "The Quest for Abundance", "desc": "Scarcity. You feel blocked because you are fighting your own flow. Align with your Jupiter sign."},
    "relationship": {"title": "The Quest for Connection", "desc": "Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement."},
    "purpose": {"title": "The Quest for Meaning", "desc": "The Void. You feel lost because you look for a destination, not a frequency. Stop doing and start being."},
    "health": {"title": "The Quest for Vitality", "desc": "Exhaustion. Your body is overheating from running wrong software. Surrender to your internal rhythm."},
    "general": {"title": "The Quest for Alignment", "desc": "Confusion. You are a unique design in a standardized world. Your Rising Sign is your compass."}
}

# --- DATA: ORIENTATION ---
LINE_LORE = {
    1: {"title": "Investigator", "desc": "The Foundation Builder. Certainty is your superpower."},
    2: {"title": "Natural", "desc": "The Reluctant Hero. You possess innate gifts you never studied for."},
    3: {"title": "Experimenter", "desc": "The Fearless Explorer. There are no mistakes, only discoveries."},
    4: {"title": "Networker", "desc": "The Tribal Weaver. Your power is connection."},
    5: {"title": "Fixer", "desc": "The General. You arrive, provide a solution, and vanish."},
    6: {"title": "Role Model", "desc": "The Sage. You live three lives: youth, observer, and example."}
}

# --- DATA: SIGNS ---
SIGN_LORE = {
    "Aries": "The Warrior", "Taurus": "The Builder", "Gemini": "The Messenger",
    "Cancer": "The Protector", "Leo": "The Radiant", "Virgo": "The Alchemist",
    "Libra": "The Diplomat", "Scorpio": "The Sorcerer", "Sagittarius": "The Philosopher",
    "Capricorn": "The Architect", "Aquarius": "The Revolutionary", "Pisces": "The Mystic"
}

# --- DATA: ARCHETYPES ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "The primal spark."}, 2: {"name": "The Receptive", "story": "The cosmic womb."},
    3: {"name": "The Innovator", "story": "The necessary chaos."}, 4: {"name": "The Logic Master", "story": "The answer to doubt."},
    5: {"name": "The Fixer", "story": "The power of waiting."}, 6: {"name": "The Peacemaker", "story": "The emotional diplomat."},
    7: {"name": "The Leader", "story": "The guide."}, 8: {"name": "The Stylist", "story": "The rebel."},
    9: {"name": "The Focuser", "story": "The detail."}, 10: {"name": "The Self", "story": "The art of being."},
    11: {"name": "The Idealist", "story": "The light-catcher."}, 12: {"name": "The Articulate", "story": "The voice."},
    13: {"name": "The Listener", "story": "The vault."}, 14: {"name": "The Power House", "story": "The fuel."},
    15: {"name": "The Humanist", "story": "The embrace."}, 16: {"name": "The Master", "story": "The virtuoso."},
    17: {"name": "The Opinion", "story": "The eye."}, 18: {"name": "The Improver", "story": "The healer."},
    19: {"name": "The Sensitive", "story": "The barometer."}, 20: {"name": "The Now", "story": "The clarity."},
    21: {"name": "The Controller", "story": "The manager."}, 22: {"name": "The Grace", "story": "The open door."},
    23: {"name": "The Assimilator", "story": "The remover."}, 24: {"name": "The Rationalizer", "story": "The inventor."},
    25: {"name": "The Spirit", "story": "The shaman."}, 26: {"name": "The Egoist", "story": "The dealmaker."},
    27: {"name": "The Nurturer", "story": "The guardian."}, 28: {"name": "The Risk Taker", "story": "The confronter."},
    29: {"name": "The Devoted", "story": "The commitment."}, 30: {"name": "The Passion", "story": "The fire."},
    31: {"name": "The Voice", "story": "The leader."}, 32: {"name": "The Conservative", "story": "The root."},
    33: {"name": "The Reteller", "story": "The historian."}, 34: {"name": "The Power", "story": "The giant."},
    35: {"name": "The Progress", "story": "The hunger."}, 36: {"name": "The Crisis", "story": "The light."},
    37: {"name": "The Family", "story": "The glue."}, 38: {"name": "The Fighter", "story": "The warrior."},
    39: {"name": "The Provocateur", "story": "The awakener."}, 40: {"name": "The Aloneness", "story": "The deliverer."},
    41: {"name": "The Fantasy", "story": "The seed."}, 42: {"name": "The Finisher", "story": "The closer."},
    43: {"name": "The Insight", "story": "The breakthrough."}, 44: {"name": "The Alert", "story": "The instinct."},
    45: {"name": "The Gatherer", "story": "The monarch."}, 46: {"name": "The Determination", "story": "The vessel."},
    47: {"name": "The Realization", "story": "The epiphany."}, 48: {"name": "The Depth", "story": "The well."},
    49: {"name": "The Catalyst", "story": "The revolutionary."}, 50: {"name": "The Values", "story": "The guardian."},
    51: {"name": "The Shock", "story": "The thunder."}, 52: {"name": "The Stillness", "story": "The mountain."},
    53: {"name": "The Starter", "story": "The pressure."}, 54: {"name": "The Ambition", "story": "The climber."},
    55: {"name": "The Spirit", "story": "The cup."}, 56: {"name": "The Storyteller", "story": "The wanderer."},
    57: {"name": "The Intuitive", "story": "The ear."}, 58: {"name": "The Joy", "story": "The vital."},
    59: {"name": "The Sexual", "story": "The breaker."}, 60: {"name": "The Limitation", "story": "The acceptance."},
    61: {"name": "The Mystery", "story": "The knower."}, 62: {"name": "The Detail", "story": "The bridge."},
    63: {"name": "The Doubter", "story": "The logic."}, 64: {"name": "The Confusion", "story": "The resolver."}
}

# --- LOGIC ---
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

def get_gate(deg):
    if deg is None: return 1
    deg %= 360
    return {0:25, 1:17, 2:21, 3:51, 4:42, 5:3, 6:27, 7:24, 8:2, 9:23, 10:8, 11:20, 12:16, 13:35, 14:45, 15:12, 16:15, 17:52, 18:39, 19:53, 20:62, 21:56, 22:31, 23:33, 24:7, 25:4, 26:29, 27:59, 28:40, 29:64, 30:47, 31:6, 32:46, 33:18, 34:48, 35:57, 36:32, 37:50, 38:28, 39:44, 40:1, 41:43, 42:14, 43:34, 44:9, 45:5, 46:26, 47:11, 48:10, 49:58, 50:38, 51:54, 52:61, 53:60, 54:41, 55:19, 56:13, 57:49, 58:30, 59:55, 60:37, 61:63, 62:22, 63:36}.get(int(deg/5.625), 1)

def resolve_loc(city):
    for k in CITY_DB:
        if k in str(city).lower(): return CITY_DB[k]
    try:
        g = Nominatim(user_agent="ia_v3")
        l = g.geocode(city)
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

def get_hd_data(deg):
    gate = get_gate(deg)
    info = KEY_LORE.get(gate, {"name": f"Archetype {gate}", "story": "Energy"})
    return {"gate": gate, "name": info["name"], "story": info["story"]}

def gen_story(name, c, orient, lp, struggle):
    sun, moon, ris = c['Sun'], c['Moon'], c['Rising']
    s_lore, m_lore, r_lore = SIGN_LORE.get(sun['Sign']), SIGN_LORE.get(moon['Sign']), SIGN_LORE.get(ris['Sign'])
    gate_name, gate_story = sun['Name'], KEY_LORE.get(sun['Gate'], {}).get("story", "")
    dragon = struggle[0].replace("The Quest for ", "")
    
    chaps = []
    chaps.append({"title": "🌟 THE ORIGIN", "body": f"Long ago, the universe created a frequency named {name}. Born under {sun['Sign']} ({s_lore}), this is your core. But to protect it, you wear the mask of {ris['Sign']} ({r_lore}). Your journey is to reconcile these two."})
    chaps.append({"title": "❤️ THE HEART", "body": f"Beneath the armor lies your Moon in {moon['Sign']} ({m_lore}). This is your secret engine. Ignoring it drains you; honoring it regenerates you."})
    chaps.append({"title": "🏔️ THE PATH", "body": f"Your road is Life Path {lp}. {LIFE_PATH_LORE.get(lp, '')} It is a steep climb, but the view is your purpose."})
    chaps.append({"title": "⚔️ THE WEAPON", "body": f"Your superpower is Archetype {sun['Gate']}: {gate_name}. {gate_story} When trusted, doors open. It is the sword in your hand."})
    chaps.append({"title": "🗺️ THE STRATEGY", "body": f"Your manual is {orient}. You are not designed to move like others. Trust your specific style to avoid frustration."})
    chaps.append({"title": "🐉 THE DRAGON", "body": f"Your antagonist is {dragon}. {struggle[1]} This struggle is not a punishment, but the friction needed to sharpen your blade."})
    chaps.append({"title": "📜 THE MAP", "body": f"This is the Legend of {name}. The stars have done their part; the rest is yours to write."})
    return chaps

def clean_txt(t):
    if not t: return ""
    return re.sub(r'[^\x00-\x7F]+', '', t).replace("—", "-").replace("’", "'").encode('latin-1', 'replace').decode('latin-1')

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
        pdf.set_font("Helvetica", '', 11)
        for k, v in chart.items():
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 8, clean_txt(f"{k}: {v['Sign']} (Archetype {v['Gate']}) - {v['Name']}"), 0, 1)
            pdf.set_font("Helvetica", '', 10)
            pdf.multi_cell(0, 5, clean_txt(v['Story']))
            pdf.ln(2)
            
        return base64.b64encode(pdf.output()).decode('utf-8')
    except: return ""

@app.post("/calculate")
async def calculate(request: Request):
    d = await request.json()
    name, dob, tob, city, struggle = d.get("name", "Traveler"), d.get("dob"), clean_time(d.get("tob")), d.get("city", "London"), d.get("struggle", "general")
    
    try:
        lat, lon, tz = resolve_location(city)
        off = get_tz(dob, tob, tz)
        dt = Datetime(dob.replace("-", "/"), tob, off)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        c_data = {}
        for p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            obj = chart.get(getattr(const, p.upper()))
            c_data[p] = {"Sign": obj.sign, **get_hd_data(obj.lon)}
        
        asc = chart.get(const.ASC)
        c_data["Rising"] = {"Sign": asc.sign, **get_hd_data(asc.lon)}
        
        p_sun = chart.get(const.SUN)
        d_sun_lon = (p_sun.lon - 88) % 360 # Approx Design Sun
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1
        d_line = (int(d_sun_lon / 0.9375) % 6) + 1
        
        orient = f"{LINE_LORE[p_line]['title']} / {LINE_LORE[d_line]['title']}"
        orient_body = f"{LINE_LORE[p_line]['desc']} {LINE_LORE[d_line]['desc']}"
        
        digits = [int(n) for n in dob if n.isdigit()]
        lp = sum(digits)
        while lp > 9 and lp not in [11, 22, 33]: lp = sum(int(n) for n in str(lp))
        
        s_adv = STRUGGLE_LORE.get(struggle, STRUGGLE_LORE["general"])
        topic, advice = s_adv["title"], s_adv["desc"]
        
        chapters = gen_story(name, c_data, orient, lp, (topic, advice))
        pdf = create_pdf(name, chapters, c_data)
        
        ch_html = "".join([f"<div class='chapter'><h3>{c['title']}</h3><p>{c['body']}</p></div>" for c in chapters])
        
        html = f"""
        <html><head><style>
        body {{ font-family: sans-serif; padding: 20px; color: #333; background: #fdfdfd; }}
        .chapter {{ background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 4px solid #D4AF37; }}
        h3 {{ margin: 0 0 10px; color: #2c3e50; }}
        .btn {{ display: block; width: 100%; max-width: 300px; margin: 20px auto; padding: 15px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; }}
        </style></head><body>
        <h2 style="text-align:center">The Legend of {name}</h2>
        {ch_html}
        <a href="data:application/pdf;base64,{pdf}" download="The_Legend_of_You.pdf" class="btn">⬇️ DOWNLOAD PDF</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": "Error calculating chart."}
