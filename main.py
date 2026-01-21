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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATA: LINE ARCHETYPES (ORIENTATION) ---
# We map the 6 Lines to "Integrated" names
LINE_NAMES = {
    1: "Investigator",
    2: "Natural",
    3: "Experimenter",
    4: "Networker",
    5: "Fixer",
    6: "Role Model"
}

# --- 2. DATA: LOCATIONS ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- 3. DATA: THE LORE ---
SIGN_LORE = {
    "Aries": "The Initiator. You are the spark of life, driven by instinct and courage.",
    "Taurus": "The Builder. You are the anchor of stability and sensory endurance.",
    "Gemini": "The Messenger. You are the weaver of connections and curiosity.",
    "Cancer": "The Protector. You are the emotional harbor and nurturer.",
    "Leo": "The Radiant. You are the center of the solar system, born to shine.",
    "Virgo": "The Alchemist. You are the seeker of perfection and service.",
    "Libra": "The Harmonizer. You are the bridge seeking balance and beauty.",
    "Scorpio": "The Transformer. You are the diver into the deep and the cycles of rebirth.",
    "Sagittarius": "The Explorer. You are the arrow of truth and vast wisdom.",
    "Capricorn": "The Architect. You are the climber of mountains and legacy.",
    "Aquarius": "The Visionary. You are the breaker of patterns and the futurist.",
    "Pisces": "The Mystic. You are the dreamer dissolving boundaries."
}

KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness."},
    2: {"name": "The Receptive", "story": "The Divine Feminine Blueprint."},
    3: {"name": "The Innovator", "story": "Chaos into Innovation."},
    4: {"name": "The Logic Master", "story": "The Answer to Doubt."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace."},
    7: {"name": "The Leader", "story": "Guidance by Collective Will."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style."},
    9: {"name": "The Focuser", "story": "Power of the Small."},
    10: {"name": "The Self", "story": "The Art of Being."},
    11: {"name": "The Idealist", "story": "Ideas into Light."},
    12: {"name": "The Articulate", "story": "The Channel of Voice."},
    13: {"name": "The Listener", "story": "The Confidant of the Past."},
    14: {"name": "The Power House", "story": "Fuel for Dreams."},
    15: {"name": "The Humanist", "story": "Extremes into Flow."},
    16: {"name": "The Master", "story": "Skill into Versatility."},
    17: {"name": "The Opinion", "story": "The Eye of the Future."},
    18: {"name": "The Improver", "story": "Correction for Perfection."},
    19: {"name": "The Sensitive", "story": "Attunement to Needs."},
    20: {"name": "The Now", "story": "Spontaneous Clarity."},
    21: {"name": "The Controller", "story": "Authority over Resources."},
    22: {"name": "The Grace", "story": "Emotional Openness."},
    23: {"name": "The Assimilator", "story": "Complexity into Simplicity."},
    24: {"name": "The Rationalizer", "story": "Invention from the Past."},
    25: {"name": "The Spirit", "story": "Innocence despite Wounds."},
    26: {"name": "The Egoist", "story": "The Great Influencer."},
    27: {"name": "The Nurturer", "story": "Altruism and Care."},
    28: {"name": "The Risk Taker", "story": "Purpose through Totality."},
    29: {"name": "The Yes Man", "story": "Commitment through the Abyss."},
    30: {"name": "The Passion", "story": "The Burning Fire."},
    31: {"name": "The Voice", "story": "Leadership through Influence."},
    32: {"name": "The Conservative", "story": "Preservation of Value."},
    33: {"name": "The Reteller", "story": "Retreat into Wisdom."},
    34: {"name": "The Power", "story": "Majesty of Force."},
    35: {"name": "The Progress", "story": "Hunger for Experience."},
    36: {"name": "The Crisis", "story": "Compassion through Turbulence."},
    37: {"name": "The Family", "story": "Community and Friendship."},
    38: {"name": "The Fighter", "story": "Struggle for Honor."},
    39: {"name": "The Provocateur", "story": "Liberation through Provocation."},
    40: {"name": "The Aloneness", "story": "Resolve in Separation."},
    41: {"name": "The Fantasy", "story": "The Origin of the Dream."},
    42: {"name": "The Finisher", "story": "Growth through Conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough of Knowing."},
    44: {"name": "The Alert", "story": "Teamwork through Instinct."},
    45: {"name": "The Gatherer", "story": "Synergy of the Kingdom."},
    46: {"name": "The Determination", "story": "Serendipity of the Body."},
    47: {"name": "The Realization", "story": "Epiphany from Confusion."},
    48: {"name": "The Depth", "story": "Wisdom from the Well."},
    49: {"name": "The Catalyst", "story": "Revolution of Principles."},
    50: {"name": "The Values", "story": "Guardian of Harmony."},
    51: {"name": "The Shock", "story": "Initiation by Thunder."},
    52: {"name": "The Stillness", "story": "The Mountain."},
    53: {"name": "The Starter", "story": "Pressure to Begin."},
    54: {"name": "The Ambition", "story": "Ascension of the Tribe."},
    55: {"name": "The Spirit", "story": "Freedom in Emotion."},
    56: {"name": "The Storyteller", "story": "The Wandering Myth."},
    57: {"name": "The Intuitive", "story": "Clarity in the Now."},
    58: {"name": "The Joy", "story": "Vitality to Challenge."},
    59: {"name": "The Sexual", "story": "Intimacy breaking Barriers."},
    60: {"name": "The Limitation", "story": "Realism into Transcendence."},
    61: {"name": "The Mystery", "story": "Inner Truth."},
    62: {"name": "The Detail", "story": "Precision of Intellect."},
    63: {"name": "The Doubter", "story": "Logic for Truth."},
    64: {"name": "The Confusion", "story": "Illumination of Images."}
}

# --- 4. LOGIC ENGINES ---

def clean_time(time_input):
    if not time_input: return "12:00"
    s = str(time_input).upper().strip()
    match = re.search(r'(\d{1,2}):(\d{2})', s)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        if "PM" in s and h < 12: h += 12
        if "AM" in s and h == 12: h = 0
        return f"{h:02d}:{m:02d}"
    return "12:00"

def get_gate_from_degree(degree):
    if degree is None: return 1
    if degree < 0 or degree >= 360: degree = degree % 360
    step = int(degree / 5.625)
    # Standard Human Design Mandala Mapping
    gate_map = {
        0: 25, 1: 17, 2: 21, 3: 51, 4: 42, 5: 3, 6: 27, 7: 24,
        8: 2, 9: 23, 10: 8, 11: 20, 12: 16, 13: 35, 14: 45, 15: 12,
        16: 15, 17: 52, 18: 39, 19: 53, 20: 62, 21: 56, 22: 31, 23: 33,
        24: 7, 25: 4, 26: 29, 27: 59, 28: 40, 29: 64, 30: 47, 31: 6,
        32: 46, 33: 18, 34: 48, 35: 57, 36: 32, 37: 50, 38: 28, 39: 44,
        40: 1, 41: 43, 42: 14, 43: 34, 44: 9, 45: 5, 46: 26, 47: 11,
        48: 10, 49: 58, 50: 38, 51: 54, 52: 61, 53: 60, 54: 41, 55: 19,
        56: 13, 57: 49, 58: 30, 59: 55, 60: 37, 61: 63, 62: 22, 63: 36
    }
    return gate_map.get(step, 1)

def safe_get_date(date_input):
    if not date_input: return None
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def resolve_location(city_name):
    city_lower = str(city_name).lower().strip()
    for key in CITY_DB:
        if key in city_lower: return CITY_DB[key]
    try:
        geolocator = Nominatim(user_agent="ia_final_fix_v9")
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

def get_hd_data(degree):
    gate = get_gate_from_degree(degree)
    info = KEY_LORE.get(gate, {"name": f"Gate {gate}", "story": "Energy"})
    return {"gate": gate, "name": info["name"], "story": info["story"]}

def get_strategic_advice(struggle, chart):
    s = str(struggle).lower()
    if any(x in s for x in ['money', 'career', 'job']):
        jup = chart.get("Jupiter", {}).get("Sign", "?")
        return "Wealth Architecture", f"Your path to abundance involves the expansion of **Jupiter in {jup}**."
    elif any(x in s for x in ['love', 'relationship']):
        ven = chart.get("Venus", {}).get("Sign", "?")
        return "Relational Design", f"Your heart speaks the language of **Venus in {ven}**."
    else:
        ris = chart.get("Rising", {}).get("Sign", "?")
        return "Core Alignment", f"Return to your **{ris} Rising**. This is your anchor."

def create_pdf_b64(name, lp, orientation, advice, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
        pdf.ln(5)

        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        # CHANGED: Profile -> Orientation
        pdf.cell(0, 10, f"Life Path: {lp} | Orientation: {orientation}", 0, 1)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Strategic Guidance", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        clean_advice = advice[1].replace("**", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, clean_advice)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Planetary Blueprint", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        for k, v in chart.items():
            sign = v.get("Sign", "?")
            gate = v.get("Gate", "?")
            name_txt = v.get("Name", "")
            sign_txt = v.get("SignLore", "")
            pdf.cell(0, 8, f"{k}: {sign} - {name_txt}", 0, 1)
            pdf.set_font("Helvetica", 'I', 10)
            pdf.multi_cell(0, 5, f"   (Sign) {sign_txt}")
            pdf.ln(2)
            pdf.set_font("Helvetica", '', 12)
            
        pdf_bytes = pdf.output()
        return base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"PDF Error: {str(e)}")
        return ""

# --- 5. API ROUTES ---

@app.get("/")
def root():
    return {"status": "online", "message": "Identity Architect is Running."}

@app.post("/calculate")
async def calculate_chart(request: Request):
    data = {}
    try:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct: data = await request.json()
        else: data = dict(await request.form())
    except: pass
    
    name = data.get("name") or "Traveler"
    
    # 1. Personality Date (Conscious)
    raw_date = data.get("dob") or data.get("date")
    dob = safe_get_date(raw_date)
    if not dob: dob = datetime.date.today().strftime("%Y-%m-%d")

    raw_time = data.get("tob") or data.get("time") or data.get("birth_time") or "12:00"
    tob = clean_time(raw_time)

    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"

    try:
        lat, lon, tz_name = resolve_location(city)
        tz_offset = get_tz_offset(dob, tob, tz_name)
        
        # 2. Calculate Personality Chart (The Mind)
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        chart_p = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        # 3. Calculate Design Chart (The Body - approx 88 days prior)
        # Note: We subtract 88 days. For higher precision, solar arc is needed, but this is standard for MVP.
        design_date_obj = datetime.datetime.strptime(dob, "%Y-%m-%d") - datetime.timedelta(days=88)
        design_dob = design_date_obj.strftime("%Y/%m/%d")
        dt_design = Datetime(design_dob, tob, tz_offset) # Same time/loc is close enough for lines
        chart_d = Chart(dt_design, geo_obj, IDs=[const.SUN], hsys=const.HOUSES_PLACIDUS)

        # 4. Extract Data
        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        # Personality Sun Gate & Line
        p_sun = chart_p.get(const.SUN)
        p_sun_data = get_hd_data(p_sun.lon)
        p_sun_gate = p_sun_data['gate']
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1  # Calculate Line (1-6)

        # Design Sun Gate & Line
        d_sun = chart_d.get(const.SUN)
        d_line = (int(d_sun.lon / 0.9375) % 6) + 1

        # ORIENTATION (Replaces Profile)
        # Map numbers to text (e.g., 2 -> Natural, 4 -> Networker)
        p_name = LINE_NAMES.get(p_line, str(p_line))
        d_name = LINE_NAMES.get(d_line, str(d_line))
        orientation_text = f"{p_name} / {d_name}" # e.g. "Natural / Networker"

        for p in planets:
            obj = chart_p.get(getattr(const, p.upper()))
            info = get_hd_data(obj.lon)
            sign_lore = SIGN_LORE.get(obj.sign, "Energy")
            chart_data[p] = {
                "Sign": obj.sign, 
                "SignLore": sign_lore,
                "Gate": info['gate'], 
                "Name": info['name'], 
                "Story": info['story']
            }
            
        asc = chart_p.get(const.ASC)
        asc_info = get_hd_data(asc.lon)
        asc_sign_lore = SIGN_LORE.get(asc.sign, "Energy")
        chart_data["Rising"] = {
            "Sign": asc.sign, 
            "SignLore": asc_sign_lore,
            "Gate": asc_info['gate'], 
            "Name": asc_info['name'], 
            "Story": asc_info['story']
        }
        
        # Life Path Calc
        try:
            digits = [int(d) for d in dob if d.isdigit()]
            total = sum(digits)
            while total > 9 and total not in [11, 22, 33]:
                total = sum(int(d) for d in str(total))
            lp = total
        except: lp = 0
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1, "Name": "Error", "Story": ""}}
        orientation_text = "Unknown"
        lp = 0

    topic, advice_text = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, lp, orientation_text, (topic, advice_text), chart_data)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
        body {{ font-family: 'Source Sans Pro', sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
        .card {{ background: #fff; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h2 {{ font-family: 'Playfair Display', serif; color: #D4AF37; margin-top: 0; }}
        .gate-title {{ color: #C71585; font-weight: bold; font-size: 1.1em; }}
        .gate-desc {{ font-size: 0.95em; color: #444; display: block; margin-top: 4px; font-style: italic; }}
        .sign-desc {{ font-size: 0.9em; color: #666; display: block; margin-bottom: 10px; border-left: 3px solid #eee; padding-left: 10px; }}
        .orientation-tag {{ 
            background: #eee; padding: 5px 10px; border-radius: 4px; font-weight: bold; color: #555; font-size: 0.9em;
            display: inline-block; margin-top: 5px;
        }}
        .btn {{ 
            background-color: #D4AF37; color: white; border: none; padding: 15px 30px; 
            font-size: 16px; border-radius: 50px; cursor: pointer; display: block; 
            width: 100%; max-width: 300px; margin: 20px auto; text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-decoration: none;
        }}
        .spacer {{ height: 500px; }}
    </style>
    </head>
    <body>
        <div class="card" style="text-align:center;">
            <h2>The Integrated Self</h2>
            <p>Prepared for {name}</p>
            <p>
                <strong>Life Path:</strong> {lp}<br>
                <span class="orientation-tag">Orientation: {orientation_text}</span>
            </p>
        </div>

        <div class="card" style="border-left: 5px solid #D4AF37;">
            <h2>⚡ Strategic Insight: {topic}</h2>
            <p>{advice_text}</p>
        </div>

        <div class="card">
            <h2>The Blueprint</h2>
            
            <p><strong>☀️ Sun in {chart_data.get('Sun',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Sun',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Sun',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Sun',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Sun',{}).get('Story','')}"</span></p>
            
            <p><strong>🌙 Moon in {chart_data.get('Moon',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Moon',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Moon',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Moon',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Moon',{}).get('Story','')}"</span></p>
            
            <p><strong>🏹 Rising in {chart_data.get('Rising',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Rising',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Rising',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Rising',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Rising',{}).get('Story','')}"</span></p>
        </div>

        <a href="data:application/pdf;base64,{pdf_b64}" download="Integrated_Self.pdf" target="_blank" class="btn">
            ⬇️ DOWNLOAD PDF REPORT
        </a>

        <div class="spacer"></div>
    </body>
    </html>
    """
    return {"report": html}
