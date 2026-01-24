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

CITY_DB = {"minneapolis": (44.9778, -93.2650, "America/Chicago"), "london": (51.5074, -0.1278, "Europe/London"), "new york": (40.7128, -74.0060, "America/New_York"), "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"), "ashland": (42.1946, -122.7095, "America/Los_Angeles")}

LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone, conquer self-doubt, and lead the tribe into a new era.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master the invisible threads that connect people, teaching the world that power lies in cooperation.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world using your words, art, and radiant optimism.",
    4: "The Master Builder. You are the architect of the future. While others dream, you lay the bricks. Your story is one of endurance and legacy.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability. You are here to break the chains of tradition.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility without breaking, nurturing the tribe.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth to look past the veil of illusion.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money, power, and influence.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go. You are here to heal the world with compassion.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness, channeling high-frequency insights.",
    22: "The Master Architect. You are the bridge between heaven and earth. You possess the rare ability to turn impossible visions into reality.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity through pure, unadulterated service."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. You feel blocked financially not because you lack skill, but because you are fighting against your own energy flow. Wealth is a frequency. Align with your Jupiter sign."),
    "relationship": ("The Quest for Connection", "Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement to magnetize your tribe."),
    "purpose": ("The Quest for Meaning", "The Void. You feel lost because you are looking for a destination, not a frequency. Your North Node defines your signal. Stop doing and start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Your body is the hardware for your consciousness, and it is overheating. Your Saturn placement holds your boundaries. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. You feel adrift because you are a unique design in a standardized world. Your Rising Sign is your compass. Return to your core strategy.")
}

LINE_LORE = {1: "The Investigator (Foundation Builder)", 2: "The Natural (Reluctant Hero)", 3: "The Experimenter (Fearless Explorer)", 4: "The Networker (Tribal Weaver)", 5: "The Fixer (The General)", 6: "The Role Model (The Sage)"}

SIGN_LORE = {
    "Aries": "The Warrior. You are the spark that starts the fire.", "Taurus": "The Builder. You are the earth; patient and unmovable.", "Gemini": "The Messenger. You are the wind; a kaleidoscope of stories.", "Cancer": "The Protector. You are the tide; deeply intuitive.", "Leo": "The Radiant. You are the sun; you do not just enter a room, you warm it.", "Virgo": "The Alchemist. You are the perfectionist; refining the world.", "Libra": "The Diplomat. You are the scales; existing in the delicate balance.", "Scorpio": "The Sorcerer. You are the depths; unafraid to dive into the dark.", "Sagittarius": "The Philosopher. You are the arrow; driven by a hunger for truth.", "Capricorn": "The Architect. You are the mountain peak; driven by legacy.", "Aquarius": "The Revolutionary. You are the lightning; breaking old structures.", "Pisces": "The Mystic. You are the ocean; dissolving boundaries."
}

KEY_LORE = {
    1: "The Creator (The Primal Spark)", 2: "The Receptive (The Cosmic Womb)", 3: "The Innovator (The Necessary Chaos)", 4: "The Logic Master (The Formula)", 5: "The Fixer (The Rhythm)", 6: "The Peacemaker (The Diplomat)", 7: "The Leader (The Guide)", 8: "The Stylist (The Rebel)", 9: "The Focuser (The Detail)", 10: "The Self (The Vessel)", 11: "The Idealist (The Light-Catcher)", 12: "The Articulate (The Voice)", 13: "The Listener (The Vault)", 14: "The Power House (The Fuel)", 15: "The Humanist (The Flow)", 16: "The Master (The Virtuoso)", 17: "The Opinion (The Eye)", 18: "The Improver (The Critic)", 19: "The Sensitive (The Barometer)", 20: "The Now (The Breath)", 21: "The Controller (The Manager)", 22: "The Grace (The Open Door)", 23: "The Assimilator (The Razor)", 24: "The Rationalizer (The Inventor)", 25: "The Spirit (The Shaman)", 26: "The Egoist (The Dealmaker)", 27: "The Nurturer (The Guardian)", 28: "The Risk Taker (The Daredevil)", 29: "The Devoted (The Commitment)", 30: "The Passion (The Fire)", 31: "The Voice (The Elected)", 32: "The Conservative (The Root)", 33: "The Reteller (The Historian)", 34: "The Power (The Giant)", 35: "The Progress (The Hunger)", 36: "The Crisis (The Survivor)", 37: "The Family (The Glue)", 38: "The Fighter (The Warrior)", 39: "The Provocateur (The Poker)", 40: "The Aloneness (The Deliverer)", 41: "The Fantasy (The Seed)", 42: "The Finisher (The Closer)", 43: "The Insight (The Breakthrough)", 44: "The Alert (The Instinct)", 45: "The Gatherer (The Monarch)", 46: "The Determination (The Vessel)", 47: "The Realization (The Epiphany)", 48: "The Depth (The Well)", 49: "The Catalyst (The Revolutionary)", 50: "The Values (The Custodian)", 51: "The Shock (The Thunder)", 52: "The Stillness (The Mountain)", 53: "The Starter (The Pressure)", 54: "The Ambition (The Climber)", 55: "The Spirit (The Cup)", 56: "The Storyteller (The Wanderer)", 57: "The Intuitive (The Ear)", 58: "The Joy (The Vital)", 59: "The Sexual (The Breaker)", 60: "The Limitation (The Acceptance)", 61: "The Mystery (The Knower)", 62: "The Detail (The Name)", 63: "The Doubter (The Question)", 64: "The Confusion (The Resolver)"
}

def safe_get_date(d):
    if not d: return None
    s = str(d).strip()
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
        g = Nominatim(user_agent="ia_final_v100")
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
    c2 = f"But a warrior is nothing without a reason to fight. Beneath the armor lies a secret engine: your **Moon in {moon['Sign']}**. While the world sees your actions, only you feel the pull of **{m_lore}**. This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. It governs your emotional tides and your deepest needs. Ignoring this voice is what leads to burnout and exhaustion; honoring it is the secret to your endless regeneration and emotional power."
    c3 = f"Every hero needs a road to walk. Yours is the **Path of the {lp}**. This is not a random wander; it is a destiny defined as: **{LIFE_PATH_LORE.get(lp, '')}** The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, and at times it will feel lonely, but the view from the top is the purpose you have been searching for. You are here to master this specific lesson."
    c4 = f"To aid you on this path, you were gifted a specific weapon—a superpower woven into your DNA. In the language of the Archetypes, you carry the energy of **Archetype {sun['Gate']}: {gate_name}**. This is not a skill you learned in school; it is a frequency you emit naturally. When you trust this power, doors open without force. It is the sword in your hand. When you try to be someone else, you dull this blade. Your task is to wield it with precision."
    c5 = f"But power without control is dangerous. Your operating manual is defined by your Orientation: **{orient}**. You are not designed to move like everyone else. Your specific strategy requires you to honor your nature—whether that is to wait in your hermitage, to experiment fearlessly, or to network with your tribe. Deviation from this strategy is the root of your frustration. You must trust your unique style of engagement."
    c6 = f"Every story has an antagonist. Yours takes the form of **{dragon}**. {d_desc} This struggle you feel—whether in wealth, love, or purpose—is not a punishment from the universe. It is the friction necessary to sharpen your blade. The dragon guards the treasure. By facing your Shadow and applying your Archetype, you do not just slay the dragon; you integrate it, turning your greatest weakness into your greatest wisdom."

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
    name, dob, tob = d.get("name", "Traveler"), safe_get_date(d.get("dob") or d.get("date")), clean_time(d.get("tob") or d.get("time"))
    if not dob: dob = datetime.date.today().strftime("%Y-%m-%d")
    city, struggle = d.get("city", "London"), d.get("struggle", "general")

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
