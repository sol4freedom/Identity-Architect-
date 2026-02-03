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

# --- DATA LORE ---
CITY_DB = {
    "minneapolis": (44.97, -93.26, "America/Chicago"), "london": (51.50, -0.12, "Europe/London"),
    "new york": (40.71, -74.00, "America/New_York"), "sao paulo": (-23.55, -46.63, "America/Sao_Paulo"),
    "ashland": (42.19, -122.70, "America/Los_Angeles"), "los angeles": (34.05, -118.24, "America/Los_Angeles")
}

LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master invisible threads.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world.",
    4: "The Master Builder. You are the architect of the future. While others dream, you lay the bricks.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money and power.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness.",
    22: "The Master Architect. You are the bridge between heaven and earth. You turn visions into reality.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. You feel blocked financially not because you lack skill, but because you are fighting against your own energy flow. Wealth is a frequency. Align with your Jupiter sign."),
    "relationship": ("The Quest for Connection", "Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement to magnetize your tribe."),
    "purpose": ("The Quest for Meaning", "The Void. You feel lost because you are looking for a destination, not a frequency. Your North Node defines your signal. Stop doing and start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Your body is the hardware for your consciousness, and it is overheating. Your Saturn placement holds your boundaries. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. You feel adrift because you are a unique design in a standardized world. Your Rising Sign is your compass. Return to your core strategy.")
}

LINE_LORE = {1:"The Investigator", 2:"The Natural", 3:"The Experimenter", 4:"The Networker", 5:"The Fixer", 6:"The Role Model"}

SIGN_LORE = {
    "Aries": "The Warrior.", "Taurus": "The Builder.", "Gemini": "The Messenger.", "Cancer": "The Protector.",
    "Leo": "The Radiant.", "Virgo": "The Alchemist.", "Libra": "The Diplomat.", "Scorpio": "The Sorcerer.",
    "Sagittarius": "The Philosopher.", "Capricorn": "The Architect.", "Aquarius": "The Revolutionary.", "Pisces": "The Mystic."
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
def safe_get_date(date_input):
    if not date_input: return None
    s = str(date_input).strip()
    return s.split("T")[0] if "T" in s else s

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
        g = Nominatim(user_agent="ia_v99_final")
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
    
    c1 = f"It is said that before a soul enters the world, it chooses a specific geometry of energy. For you, {name}, that geometry began with the **Sun in {sun['Sign']}**. This is not merely a zodiac sign; it is your fuel source. As **{s_lore}**, you are designed to burn with a specific intensity. However, raw energy requires a vessel. To navigate the physical plane, you adopted the mask of the **{ris['Sign']} Rising**. To the outside world, you appear as **{r_lore}**. This is your armor, your style, and your first line of defense. The tension between your inner {sun['Sign']} fire and your outer {ris['Sign']} shield is the primary dynamic of your origin story."
    c2 = f"But a warrior is nothing without a reason to fight. Beneath the armor lies a secret engine: your **Moon in {moon['Sign']}**. While the world sees your actions, only you feel the pull of **{m_lore}**. This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. It governs your emotional tides and your deepest needs. Ignoring this voice is what leads to burnout; honoring it is the secret to your endless regeneration."
    c3 = f"Every hero needs a road to walk. Yours is the **Path of the {lp}**. This is not a random wander; it is a destiny defined as: **{LIFE_PATH_LORE.get(lp, '')}** The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, but the view from the top is the purpose you have been searching for."
    c4 = f"To aid you on this path, you were gifted a specific weapon—a superpower woven into your DNA. In the language of the Archetypes, you carry the energy of **Archetype {sun['Gate']}: {gate_name}**. This is not a skill you learned in school; it is a frequency you emit naturally. When you trust this power, doors open without force. It is the sword in your hand."
    c5 = f"But power without control is dangerous. Your operating manual is defined by your Orientation: **{orient}**. You are not designed to move like everyone else. Your specific strategy requires you to honor your nature—whether that is to wait in your hermitage, to experiment fearlessly, or to network with your tribe. Deviation from this strategy is the root of your frustration."
    c6 = f"Every story has an antagonist. Yours takes the form of **{dragon}**. {d_desc} This struggle you feel is not a punishment from the universe. It is the friction necessary to sharpen your blade. The dragon guards the treasure. By facing your Shadow and applying your Archetype, you do not just slay the dragon; you integrate it."

    return [{"title": "🌟 THE ORIGIN", "body": c1}, {"title": "❤️ THE HEART", "body": c2}, {"title": "🏔️ THE PATH", "body": c3}, {"title": "⚔️ THE WEAPON", "body": c4}, {"title": "🗺️ THE STRATEGY", "body": c5}, {"title": "🐉 THE DRAGON", "body": c6}]

def clean_txt(t):
    if not t: return ""
    t = re.sub(r'[^\x00-\x7F]+', '', t) 
    return t.replace("—", "-").replace("’", "'").replace("**", "").encode('latin-1', 'replace').decode('latin-1')

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
    except: return ""

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
            body_html = c['body'].replace("**", "<b>").replace("**", "</b>").replace("\n", "<br>")
            grid_html += f"<div class='card'><h3>{c['title']}</h3><p>{body_html}</p></div>"
            
        html = f"""
        <html><head><style>
        body {{ font-family: 'Helvetica', sans-serif; padding: 20px; background: #fdfdfd; }}
        h2 {{ text-align: center; color: #D4AF37; font-size: 2rem; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 6px 15px rgba(0,0,0,0.08); border-top: 5px solid #D4AF37; }}
        .card h3 {{ margin-top: 0; color: #2c3e50; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
        .card p {{ color: #555; line-height: 1.6; font-size: 1rem; }}
        .btn {{ display: block; width: 220px; margin: 40px auto; padding: 15px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .btn:hover {{ background: #b8952b; }}
        </style></head><body>
        <h2>The Legend of {name}</h2>
        <div class="grid">{grid_html}</div>
        <a href="data:application/pdf;base64,{pdf}" download="The_Legend_of_You.pdf" class="btn">⬇️ DOWNLOAD LEGEND</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": "<h3>The stars are cloudy. Please try again.</h3>"}
