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

# --- 2. DATA: THE CORRECTED MAP ---
# CRITICAL FIX: This list MUST start with 25 (Aries Start) to match the math engine.
# If this starts with 41, the calculations will be wrong.
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12,  # Aries/Taurus/Gemini
    15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6,  # Cancer/Leo/Virgo
    46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11,  # Libra/Scorpio/Sag
    10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36 # Cap/Aqua/Pisces
]

# --- 3. DATA: THE TRANSLATION LAYER ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness. You are the spark that initiates new cycles when the old ways go stale."},
    2: {"name": "The Receptive", "story": "The Divine Feminine. You are the architectural blueprint that guides raw energy into form."},
    3: {"name": "The Innovator", "story": "Chaos into Order. You are the mutant who changes the rules to push evolution forward."},
    4: {"name": "The Logic Master", "story": "The Answer. You resolve doubt by finding the perfect pattern and explaining it to the world."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness. You wait for the right rhythm to align the world's habits."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace. You use diplomacy and emotional intelligence to dissolve friction."},
    7: {"name": "The Leader", "story": "Guidance. You do not force; you lead by representing the collective will of the people."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style. You are the individualist who inspires others just by being yourself."},
    9: {"name": "The Focuser", "story": "The Power of the Small. You tame the chaotic mind by focusing on one critical detail at a time."},
    10: {"name": "The Self", "story": "Being. You are here to master the art of simply being yourself without apology."},
    11: {"name": "The Idealist", "story": "Ideas into Light. You catch the images from the darkness and bring them to the world."},
    12: {"name": "The Articulate", "story": "The Channel. You master your mood to speak words that touch the soul."},
    13: {"name": "The Listener", "story": "The Confidant. You hold the secrets of the past to guide the future."},
    14: {"name": "The Power House", "story": "The Generator. You possess the unflagging energy to fuel the dreams of the collective."},
    15: {"name": "The Humanist", "story": "Extremes into Flow. You accept all rhythms of humanity, from the dull to the wild."},
    16: {"name": "The Master", "story": "The Virtuoso. You practice with enthusiasm until your skill becomes magical versatility."},
    17: {"name": "The Opinion", "story": "The Eye. You see the pattern of the future and organize it into a logical view."},
    18: {"name": "The Improver", "story": "Correction. You spot the flaw in the system so that it can be healed and perfected."},
    19: {"name": "The Sensitive", "story": "Attunement. You feel the needs of the tribe before they are even spoken."},
    20: {"name": "The Now", "story": "Presence. You bypass the thinking mind to act with pure, spontaneous clarity."},
    21: {"name": "The Controller", "story": "Authority. You take control of the resources to ensure the tribe survives and thrives."},
    22: {"name": "The Grace", "story": "Emotional Grace. You allow others to feel deeply by listening with an open heart."},
    23: {"name": "The Assimilator", "story": "Simplicity. You strip away the noise to reveal the essential truth."},
    24: {"name": "The Rationalizer", "story": "Invention. You revisit the past over and over until you find a new way forward."},
    25: {"name": "The Spirit", "story": "Universal Love. You retain the innocence of the spirit despite the wounds of the world."},
    26: {"name": "The Egoist", "story": "The Dealmaker. You use your willpower and charisma to direct resources where they are needed."},
    27: {"name": "The Nurturer", "story": "Altruism. You care for the weak and ensure the heritage is passed down."},
    28: {"name": "The Risk Taker", "story": "Immortality. You confront the fear of death to find a life worth living."},
    29: {"name": "The Yes Man", "story": "Commitment. You say 'Yes' to the experience and persevere through the abyss."},
    30: {"name": "The Passion", "story": "The Fire. You burn with a desire that cannot be quenched, teaching the world to feel."},
    31: {"name": "The Voice", "story": "Influence. You speak the vision that the collective is waiting to hear."},
    32: {"name": "The Conservative", "story": "Veneration. You assess what is valuable from the past to preserve it for the future."},
    33: {"name": "The Reteller", "story": "Retreat. You withdraw to process the memory and return with wisdom."},
    34: {"name": "The Power", "story": "Majesty. You are the pure, independent force of life expressing itself."},
    35: {"name": "The Progress", "story": "Adventure. You are driven to taste every experience, knowing that change is the only constant."},
    36: {"name": "The Crisis", "story": "Compassion. You survive the emotional storm to bring light to the darkness."},
    37: {"name": "The Family", "story": "Equality. You build the community through friendship, bargains, and affection."},
    38: {"name": "The Fighter", "story": "Honor. You fight the battles that give life meaning and purpose."},
    39: {"name": "The Provocateur", "story": "Liberation. You poke the spirit of others to wake them up from their slumber."},
    40: {"name": "The Aloneness", "story": "Resolve. You separate yourself from the group to regenerate your power."},
    41: {"name": "The Fantasy", "story": "The Origin. You hold the seed of the dream that starts the entire cycle."},
    42: {"name": "The Finisher", "story": "Growth. You maximize the cycle and bring it to a satisfying conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough. You hear the unique voice inside that changes the world's knowing."},
    44: {"name": "The Alert", "story": "Teamwork. You smell the potential in people and align them for success."},
    45: {"name": "The Gatherer", "story": "Synergy. You are the King/Queen who holds the resources together for the kingdom."},
    46: {"name": "The Determination", "story": "Serendipity. You succeed by being in the right place at the right time with your body."},
    47: {"name": "The Realization", "story": "Transmutation. You sort through the confusion of the past to find the epiphany."},
    48: {"name": "The Depth", "story": "Wisdom. You look into the deep well of talent to bring fresh solutions."},
    49: {"name": "The Catalyst", "story": "Revolution. You reject the old principles to establish a higher order."},
    50: {"name": "The Values", "story": "Harmony. You act as the guardian of the tribe's laws and values."},
    51: {"name": "The Shock", "story": "Initiation. You wake people up with thunder, forcing them to grow."},
    52: {"name": "The Stillness", "story": "The Mountain. You hold your energy still until the perfect moment to act."},
    53: {"name": "The Starter", "story": "Abundance. You are the pressure to begin something new and evolve."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward, seeking spiritual and material success."},
    55: {"name": "The Spirit", "story": "Freedom. You accept the highs and lows of emotion to find the spirit within."},
    56: {"name": "The Storyteller", "story": "Wandering. You travel through ideas and places to weave the collective myth."},
    57: {"name": "The Intuitive", "story": "Clarity. You hear the truth in the acoustic vibration of the now."},
    58: {"name": "The Joy", "story": "Vitality. You challenge authority with the joy of making life better."},
    59: {"name": "The Sexual", "story": "Intimacy. You break down barriers to create a union that produces life."},
    60: {"name": "The Limitation", "story": "Realism. You accept the boundaries of form to let the magic transcend them."},
    61: {"name": "The Mystery", "story": "Sanctity. You dive into the unknowable to bring back universal truth."},
    62: {"name": "The Detail", "story": "Precision. You name the details to build a bridge of understanding."},
    63: {"name": "The Doubter", "story": "Truth. You use critical logic to test the validity of the future."},
    64: {"name": "The Confusion", "story": "Illumination. You process the images of the mind until they resolve into light."}
}

# --- 4. LOGIC ENGINES ---
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
        geolocator = Nominatim(user_agent="ia_v99_final")
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
    """Translates Degree -> Corrected Gate -> Drop In Language"""
    if degree is None: return {"name": "Unknown", "story": "Mystery"}
    # Math: (Degree / 360) * 64 gives index in RAVE_ORDER
    # RAVE_ORDER now starts at 25 (Aries 0), matching Flatlib's Tropical Zodiac
    index = int(degree / 5.625) 
    if index >= 64: index = 0
    gate = RAVE_ORDER[index]
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

# --- 5. API ENDPOINT ---
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
        
        # Design Date
        p_dt = datetime.datetime.strptime(dob, "%Y-%m-%d")
        d_dt = p_dt - datetime.timedelta(days=88)
        d_obj = Datetime(d_dt.strftime("%Y/%m/%d"), tob, tz_offset)
        d_chart = Chart(d_obj, geo_obj, IDs=[const.SUN, const.MOON], hsys=const.HOUSES_PLACIDUS)
        
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
