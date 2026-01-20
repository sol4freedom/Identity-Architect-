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

# --- 1. DATA: LOCATIONS ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- 2. DATA: THE LORE (EXPANDED) ---

# A. ASTROLOGY (The Container)
SIGN_LORE = {
    "Aries": "The Initiator. You are the spark of life, driven by instinct, courage, and a need for direct action.",
    "Taurus": "The Builder. You are the anchor of stability, valuing sensory pleasure, endurance, and material security.",
    "Gemini": "The Messenger. You are the weaver of connections, driven by curiosity, duality, and the exchange of information.",
    "Cancer": "The Protector. You are the emotional harbor, ruled by the tides of feeling, memory, and deep nurturing.",
    "Leo": "The Radiant. You are the center of the solar system, born to shine, express creative will, and lead with heart.",
    "Virgo": "The Alchemist. You are the seeker of perfection, driven to refine, analyze, and serve the higher order.",
    "Libra": "The Harmonizer. You are the bridge between forces, seeking balance, beauty, and the reflection of self in others.",
    "Scorpio": "The Transformer. You are the diver into the deep, unafraid of intensity, shadows, and the cycles of rebirth.",
    "Sagittarius": "The Explorer. You are the arrow of truth, seeking meaning, wisdom, and the vastness of the horizon.",
    "Capricorn": "The Architect. You are the climber of mountains, driven by ambition, structure, and the legacy you build.",
    "Aquarius": "The Visionary. You are the breaker of patterns, looking toward the future, the collective, and the unique.",
    "Pisces": "The Mystic. You are the dreamer of the zodiac, dissolving boundaries to touch the universal and the divine."
}

# B. HUMAN DESIGN (The Content)
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness. You are the primal spark of creativity. You do not follow the path; you create it from the void."},
    2: {"name": "The Receptive", "story": "Dislocation into Orientation. You are the divine feminine blueprint. You provide the direction for raw energy to flow."},
    3: {"name": "The Innovator", "story": "Chaos into Innovation. You are the mutant. You break the established rules to push evolution forward into something new."},
    4: {"name": "The Logic Master", "story": "Intolerance into Understanding. You are the answer. You resolve the anxiety of doubt by finding the perfect pattern."},
    5: {"name": "The Fixer", "story": "Impatience into Patience. You trust the natural rhythm of life. You wait for the storm to pass before acting."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace. You are the emotional diplomat. You dissolve friction by holding the space for resolution."},
    7: {"name": "The Leader", "story": "Division into Guidance. You lead not by force, but by representing the collective will of the people towards the future."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style. You are the rebel of expression. You inspire others simply by having the courage to be yourself."},
    9: {"name": "The Focuser", "story": "Inertia into Determination. You tame the chaos of the mind by focusing deeply on one critical detail at a time."},
    10: {"name": "The Self", "story": "Self-Obsession into Being. You are here to master the art of self-love and to empower others by simply being you."},
    11: {"name": "The Idealist", "story": "Obscurity into Light. You catch ideas from the ether. You are the vessel for the images that inspire humanity."},
    12: {"name": "The Articulate", "story": "Vanity into Discrimination. You master the timing of your voice. You speak words that can mutate the soul."},
    13: {"name": "The Listener", "story": "Discord into Empathy. You are the confidant. You hold the secrets of the past to guide the collective future."},
    14: {"name": "The Power House", "story": "Compromise into Competence. You possess the unflagging fuel to drive the dreams of the world into reality."},
    15: {"name": "The Humanist", "story": "Dullness into Magnetism. You accept all extremes of the human experience, from the lowest lows to the highest highs."},
    16: {"name": "The Master", "story": "Indifference into Versatility. You turn raw talent into mastery through the enthusiasm of repetition."},
    17: {"name": "The Opinion", "story": "Opinion into Far-Sightedness. You see the pattern of the future and organize it into a logical view for others."},
    18: {"name": "The Improver", "story": "Judgment into Integrity. You spot the flaw in the system not to criticize, but so that it can be perfected."},
    19: {"name": "The Sensitive", "story": "Co-Dependence into Sacrifice. You are the barometer of the tribe. You feel the emotional needs of those around you."},
    20: {"name": "The Now", "story": "Superficiality into Presence. You act with pure, spontaneous clarity. You are the voice of the present moment."},
    21: {"name": "The Controller", "story": "Control into Authority. You manage the resources. You take command to ensure the tribe survives and thrives."},
    22: {"name": "The Grace", "story": "Dishonor into Grace. You are the artist of the emotions. You listen with an open heart that allows others to feel."},
    23: {"name": "The Assimilator", "story": "Complexity into Simplicity. You are the remover of obstacles. You strip away the noise to reveal the essential truth."},
    24: {"name": "The Rationalizer", "story": "Addiction into Invention. You revisit the past over and over until you find the new way forward."},
    25: {"name": "The Spirit", "story": "Constriction into Acceptance. You are the Shaman. You retain the innocence of spirit despite the wounds of the world."},
    26: {"name": "The Egoist", "story": "Pride into Artfulness. You are the great influencer. You use your willpower to direct resources where they are needed."},
    27: {"name": "The Nurturer", "story": "Selfishness into Altruism. You are the guardian. You care for the weak and ensure the heritage is preserved."},
    28: {"name": "The Risk Taker", "story": "Purposelessness into Totality. You confront the fear of death to find a life truly worth living."},
    29: {"name": "The Yes Man", "story": "Half-Heartedness into Devotion. You say 'Yes' to the experience and persevere through the abyss to wisdom."},
    30: {"name": "The Passion", "story": "Desire into Rapture. You burn with a fire that cannot be quenched, teaching the world how to feel deeply."},
    31: {"name": "The Voice", "story": "Arrogance into Leadership. You are the voice of the collective. You speak the vision that others are waiting to hear."},
    32: {"name": "The Conservative", "story": "Failure into Preservation. You assess what is valuable from the past to preserve it for the future success."},
    33: {"name": "The Reteller", "story": "Forgetting into Mindfulness. You withdraw to process the memory. You turn experience into wisdom."},
    34: {"name": "The Power", "story": "Force into Majesty. You are the pure, independent force of life expressing itself through activity."},
    35: {"name": "The Progress", "story": "Hunger into Adventure. You are driven to taste every experience, knowing that change is the only constant."},
    36: {"name": "The Crisis", "story": "Turbulence into Compassion. You survive the emotional storm to bring light to the darkness of others."},
    37: {"name": "The Family", "story": "Weakness into Equality. You build the community through friendship, bargains, and deep affection."},
    38: {"name": "The Fighter", "story": "Struggle into Honor. You fight the battles that give life meaning. You stand for your individual truth."},
    39: {"name": "The Provocateur", "story": "Provocation into Liberation. You poke the spirit of others to wake them up from their slumber."},
    40: {"name": "The Aloneness", "story": "Exhaustion into Resolve. You separate yourself from the group to regenerate your power and deliver deliverance."},
    41: {"name": "The Fantasy", "story": "Fantasy into Emanation. You hold the seed of the dream. You are the starting point of the new cycle."},
    42: {"name": "The Finisher", "story": "Expectation into Celebration. You maximize the cycle and bring it to a satisfying, fruitful conclusion."},
    43: {"name": "The Insight", "story": "Deafness into Breakthrough. You hear the unique voice inside. Your insight changes the world's knowing."},
    44: {"name": "The Alert", "story": "Interference into Teamwork. You smell potential. You align the right people to ensure success."},
    45: {"name": "The Gatherer", "story": "Dominance into Synergy. You are the King/Queen. You hold the resources together for the kingdom."},
    46: {"name": "The Determination", "story": "Seriousness into Delight. You succeed by being in the right place at the right time with your physical body."},
    47: {"name": "The Realization", "story": "Oppression into Transmutation. You sort through the confusion of the past to find the sudden epiphany."},
    48: {"name": "The Depth", "story": "Inadequacy into Wisdom. You look into the deep well of talent to bring fresh solutions to the surface."},
    49: {"name": "The Catalyst", "story": "Reaction into Revolution. You reject the old principles to establish a higher order for the tribe."},
    50: {"name": "The Values", "story": "Corruption into Harmony. You act as the guardian of the tribe's laws and values. You maintain the pot."},
    51: {"name": "The Shock", "story": "Agitation into Initiation. You wake people up with thunder. You force them to jump into the new."},
    52: {"name": "The Stillness", "story": "Stress into Restraint. You hold your energy still, like a mountain, until the perfect moment to act."},
    53: {"name": "The Starter", "story": "Immaturity into Expansion. You are the pressure to begin. You initiate the cycle of evolution."},
    54: {"name": "The Ambition", "story": "Greed into Ascension. You drive the tribe upward. You seek spiritual and material mastery."},
    55: {"name": "The Spirit", "story": "Victimization into Freedom. You accept the highs and lows of emotion to find the spirit within."},
    56: {"name": "The Storyteller", "story": "Distraction into Enrichment. You travel through ideas and places to weave the collective myth."},
    57: {"name": "The Intuitive", "story": "Unease into Clarity. You hear the truth in the acoustic vibration of the now. You trust your instinct."},
    58: {"name": "The Joy", "story": "Dissatisfaction into Vitality. You challenge authority with the joy of making life better and more efficient."},
    59: {"name": "The Sexual", "story": "Dishonesty into Intimacy. You break down barriers to create a union that produces life and transparency."},
    60: {"name": "The Limitation", "story": "Limitation into Realism. You accept the boundaries of form to let the magic transcend them."},
    61: {"name": "The Mystery", "story": "Psychosis into Sanctity. You dive into the unknowable to bring back universal truth and inspiration."},
    62: {"name": "The Detail", "story": "Intellect into Precision. You name the details. You build a bridge of understanding through facts."},
    63: {"name": "The Doubter", "story": "Doubt into Truth. You use critical logic to test the validity of the future. You question to find clarity."},
    64: {"name": "The Confusion", "story": "Confusion into Illumination. You process the images of the mind until they resolve into light."}
}

# --- 3. LOGIC ENGINES ---

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
        geolocator = Nominatim(user_agent="ia_final_fix_v8")
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

def create_pdf_b64(name, lp, hd, advice, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # Header
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
        pdf.ln(5)

        # Profile
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        pdf.cell(0, 10, f"Life Path: {lp} | Profile: {hd}", 0, 1)
        pdf.ln(5)
        
        # Advice
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Strategic Guidance", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        clean_advice = advice[1].replace("**", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, clean_advice)
        pdf.ln(5)
        
        # Blueprint
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
        
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        chart = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        p_sun = chart.get(const.SUN)
        p_sun_data = get_hd_data(p_sun.lon)
        hd_sun_gate = p_sun_data['gate']
        
        for p in planets:
            obj = chart.get(getattr(const, p.upper()))
            info = get_hd_data(obj.lon)
            sign_lore = SIGN_LORE.get(obj.sign, "Energy") 
            chart_data[p] = {
                "Sign": obj.sign, 
                "SignLore": sign_lore,
                "Gate": info['gate'], 
                "Name": info['name'], 
                "Story": info['story']
            }
            
        asc = chart.get(const.ASC)
        asc_info = get_hd_data(asc.lon)
        asc_sign_lore = SIGN_LORE.get(asc.sign, "Energy")
        chart_data["Rising"] = {
            "Sign": asc.sign, 
            "SignLore": asc_sign_lore,
            "Gate": asc_info['gate'], 
            "Name": asc_info['name'], 
            "Story": asc_info['story']
        }
        
        line_sun = (hd_sun_gate % 6) + 1
        hd_profile = f"{line_sun}/?" 
        
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
        hd_profile = "Unknown"
        lp = 0

    topic, advice_text = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, lp, hd_profile, (topic, advice_text), chart_data)

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
            <p><strong>Life Path:</strong> {lp} | <strong>Profile:</strong> {hd_profile}</p>
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
