import sys, base64, datetime, json, logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
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

# --- 2. DATA: THE TRANSLATION LAYER (Descriptions) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness. You are the spark that initiates new cycles."},
    2: {"name": "The Receptive", "story": "The Divine Feminine. You are the blueprint that guides raw energy."},
    3: {"name": "The Innovator", "story": "Chaos into Order. You change the rules to push evolution."},
    4: {"name": "The Logic Master", "story": "The Answer. You resolve doubt by finding the pattern."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness. You wait for the right rhythm."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace. You use emotional intelligence to dissolve friction."},
    7: {"name": "The Leader", "story": "Guidance. You lead by representing the collective will."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style. You inspire others by being yourself."},
    9: {"name": "The Focuser", "story": "Power of the Small. You tame chaos by focusing on details."},
    10: {"name": "The Self", "story": "Being. You master the art of being yourself."},
    11: {"name": "The Idealist", "story": "Ideas into Light. You catch images from the darkness."},
    12: {"name": "The Articulate", "story": "The Channel. You speak words that touch the soul."},
    13: {"name": "The Listener", "story": "The Confidant. You hold the secrets of the past."},
    14: {"name": "The Power House", "story": "The Generator. You fuel the dreams of the collective."},
    15: {"name": "The Humanist", "story": "Extremes into Flow. You accept all rhythms of humanity."},
    16: {"name": "The Master", "story": "The Virtuoso. Skill becomes magical versatility."},
    17: {"name": "The Opinion", "story": "The Eye. You see the pattern of the future."},
    18: {"name": "The Improver", "story": "Correction. You spot the flaw so it can be healed."},
    19: {"name": "The Sensitive", "story": "Attunement. You feel the needs of the tribe."},
    20: {"name": "The Now", "story": "Presence. You act with pure, spontaneous clarity."},
    21: {"name": "The Controller", "story": "Authority. You direct resources for the tribe."},
    22: {"name": "The Grace", "story": "Emotional Grace. You listen with an open heart."},
    23: {"name": "The Assimilator", "story": "Simplicity. You strip noise to reveal truth."},
    24: {"name": "The Rationalizer", "story": "Invention. You revisit the past to find a new way."},
    25: {"name": "The Spirit", "story": "Universal Love. You retain innocence despite wounds."},
    26: {"name": "The Egoist", "story": "The Dealmaker. You direct resources where needed."},
    27: {"name": "The Nurturer", "story": "Altruism. You care for the weak."},
    28: {"name": "The Risk Taker", "story": "Immortality. You find a life worth living."},
    29: {"name": "The Yes Man", "story": "Commitment. You persevere through the abyss."},
    30: {"name": "The Passion", "story": "The Fire. You burn with a desire that teaches feeling."},
    31: {"name": "The Voice", "story": "Influence. You speak the vision."},
    32: {"name": "The Conservative", "story": "Veneration. You preserve what is valuable."},
    33: {"name": "The Reteller", "story": "Retreat. You withdraw to process wisdom."},
    34: {"name": "The Power", "story": "Majesty. You are the force of life expressing itself."},
    35: {"name": "The Progress", "story": "Adventure. You are driven to taste every experience."},
    36: {"name": "The Crisis", "story": "Compassion. You bring light to darkness."},
    37: {"name": "The Family", "story": "Equality. You build community through friendship."},
    38: {"name": "The Fighter", "story": "Honor. You fight battles that give life purpose."},
    39: {"name": "The Provocateur", "story": "Liberation. You poke spirits to wake them up."},
    40: {"name": "The Aloneness", "story": "Resolve. You separate to regenerate power."},
    41: {"name": "The Fantasy", "story": "The Origin. You hold the seed of the dream."},
    42: {"name": "The Finisher", "story": "Growth. You bring cycles to a conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough. Your voice changes the world's knowing."},
    44: {"name": "The Alert", "story": "Teamwork. You smell potential and align success."},
    45: {"name": "The Gatherer", "story": "Synergy. You hold resources together."},
    46: {"name": "The Determination", "story": "Serendipity. You are in the right place at the right time."},
    47: {"name": "The Realization", "story": "Transmutation. You find the epiphany in confusion."},
    48: {"name": "The Depth", "story": "Wisdom. You bring fresh solutions from deep wells."},
    49: {"name": "The Catalyst", "story": "Revolution. You reject old principles for higher order."},
    50: {"name": "The Values", "story": "Harmony. You guard the tribe's laws."},
    51: {"name": "The Shock", "story": "Initiation. You wake people up with thunder."},
    52: {"name": "The Stillness", "story": "The Mountain. You wait for the perfect moment."},
    53: {"name": "The Starter", "story": "Abundance. You pressure beginnings."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward."},
    55: {"name": "The Spirit", "story": "Freedom. You accept emotional highs and lows."},
    56: {"name": "The Storyteller", "story": "Wandering. You weave the collective myth."},
    57: {"name": "The Intuitive", "story": "Clarity. You hear truth in the now."},
    58: {"name": "The Joy", "story": "Vitality. You challenge authority to make life better."},
    59: {"name": "The Sexual", "story": "Intimacy. You break barriers to create union."},
    60: {"name": "The Limitation", "story": "Realism. You accept boundaries to transcend them."},
    61: {"name": "The Mystery", "story": "Sanctity. You dive into the unknowable."},
    62: {"name": "The Detail", "story": "Precision. You build bridges of understanding."},
    63: {"name": "The Doubter", "story": "Truth. You use logic to test the future."},
    64: {"name": "The Confusion", "story": "Illumination. You resolve images into light."}
}

# --- 3. LOGIC ENGINES ---

def get_gate_from_degree(degree):
    """
    CORRELATION ENGINE:
    Maps 0-360 degrees directly to Gates.
    0° Aries = Gate 25.
    5.625° Aries = Gate 17.
    This prevents 'List Rotation' errors.
    """
    if degree < 0 or degree >= 360: degree = degree % 360
    
    # Calculate "Step" (0-63) where 0 is start of Aries
    step = int(degree / 5.625)
    
    # HARD CODED MAP (Aries 0 -> Pisces End)
    # This correlates degree directly to gate. No sliding list.
    gate_map = {
        0: 25, 1: 17, 2: 21, 3: 51, 4: 42, 5: 3, 6: 27, 7: 24,   # Aries / Taurus
        8: 2, 9: 23, 10: 8, 11: 20, 12: 16, 13: 35, 14: 45, 15: 12, # Taurus / Gemini
        16: 15, 17: 52, 18: 39, 19: 53, 20: 62, 21: 56, 22: 31, 23: 33, # Cancer / Leo
        24: 7, 25: 4, 26: 29, 27: 59, 28: 40, 29: 64, 30: 47, 31: 6, # Leo / Virgo
        32: 46, 33: 18, 34: 48, 35: 57, 36: 32, 37: 50, 38: 28, 39: 44, # Libra / Scorpio
        40: 1, 41: 43, 42: 14, 43: 34, 44: 9, 45: 5, 46: 26, 47: 11, # Sag
        48: 10, 49: 58, 50: 38, 51: 54, 52: 61, 53: 60, 54: 41, 55: 19, # Cap / Aqua
        56: 13, 57: 49, 58: 30, 59: 55, 60: 37, 61: 63, 62: 22, 63: 36  # Pisces
    }
    
    return gate_map.get(step, 1)

def safe_get_date(date_input):
    if not date_input: return datetime.date.today().strftime("%Y-%m-%d")
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def calculate_life_path(dob_str):
    try:
        digits = [int(d) for d in dob_str if d.isdigit()]
        if not digits: return 0
        total = sum(digits)
        while total > 9 and total not in [11, 22, 33]:
            total = sum(int(d) for d in str(total))
        return total
    except: return 0

def resolve_location(city_name):
    city_lower = str(city_name).lower().strip()
    for key in CITY_DB:
        if key in city_lower: return CITY_DB[key]
    try:
        geolocator = Nominatim(user_agent="ia_v101_fixed")
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
    """Uses the new Correlation Engine."""
    if degree is None: return {"name": "Unknown", "story": "Mystery"}
    
    # Use the new explicit mapper
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
    from fpdf import FPDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
            self.ln(5)
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        pdf.cell(0, 10, f"Life Path: {lp} | Profile: {hd}", 0, 1)
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
            pdf.cell(0, 8, f"{k}: {sign} - {name_txt}", 0, 1)
        return base64.b64encode(pdf.output().encode('latin-1', 'ignore')).decode('utf-8')
    except: return ""

# --- 4. API ENDPOINT ---
@app.post("/calculate")
async def calculate_chart(request: Request):
    data = {}
    try:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct: data = await request.json()
        else: data = dict(await request.form())
    except: pass
    
    name = data.get("name") or "Traveler"
    dob = safe_get_date(data.get("dob"))
    tob = data.get("tob") or "12:00"
    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"

    try:
        # Calculate
        lat, lon, tz_name = resolve_location(city)
        tz_offset = get_tz_offset(dob, tob, tz_name)
        
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        chart = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        # Personality Sun Gate
        p_sun = chart.get(const.SUN)
        p_sun_data = get_hd_data(p_sun.lon)
        hd_sun_gate = p_sun_data['gate']
        
        # Build Data
        for p in planets:
            obj = chart.get(getattr(const, p.upper()))
            info = get_hd_data(obj.lon)
            chart_data[p] = {"Sign": obj.sign, "Gate": info['gate'], "Name": info['name'], "Story": info['story']}
            
        asc = chart.get(const.ASC)
        asc_info = get_hd_data(asc.lon)
        chart_data["Rising"] = {"Sign": asc.sign, "Gate": asc_info['gate'], "Name": asc_info['name'], "Story": asc_info['story']}
        
        line_sun = (hd_sun_gate % 6) + 1
        hd_profile = f"{line_sun}/?" 
        lp = calculate_life_path(dob)
        
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
        .gate-title {{ color: #C71585; font-weight: bold; }}
        .gate-desc {{ font-size: 0.9em; font-style: italic; color: #666; display: block; margin-top: 4px; }}
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
            <span class="gate-title">{chart_data.get('Sun',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Sun',{}).get('Story','')}"</span></p>
            
            <p><strong>🌙 Moon in {chart_data.get('Moon',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Moon',{}).get('Gate',0)})<br>
            <span class="gate-title">{chart_data.get('Moon',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Moon',{}).get('Story','')}"</span></p>
            
            <p><strong>🏹 Rising in {chart_data.get('Rising',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Rising',{}).get('Gate',0)})<br>
            <span class="gate-title">{chart_data.get('Rising',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Rising',{}).get('Story','')}"</span></p>
        </div>

        <button onclick="downloadPDF()" class="btn">⬇️ DOWNLOAD PDF REPORT</button>

        <script>
            function downloadPDF() {{
                const link = document.createElement('a');
                link.href = 'data:application/pdf;base64,{pdf_b64}';
                link.download = 'Integrated_Self_Report.pdf';
                link.click();
            }}
        </script>

        <div class="spacer"></div>
    </body>
    </html>
    """
    return {"report": html}
