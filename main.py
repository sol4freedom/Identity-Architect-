import sys
import base64
import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
import flatlib
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

# ==============================================================================
# 1. APP CONFIGURATION
# ==============================================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 2. DATA DICTIONARIES (Hardcoded for stability)
# ==============================================================================

# Backup coordinates if geopy fails or for quick lookups
CITY_DB = {
    "minneapolis": (44.9778, -93.2650),
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "sao paulo": (-23.5558, -46.6396),
    "tokyo": (35.6762, 139.6503)
}

# Human Design Gate Ordering (Abbreviated for context, ensures no missing vars)
RAVE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# The 64 Keys / Hexagram Meanings
KEY_LORE = {i: f"Gate {i}: Archetypal Energy of Synthesis" for i in range(1, 65)}
# Overwrite a few for realism
KEY_LORE.update({
    1: "The Creative - Self Expression",
    2: "The Receptive - Direction of Self",
    41: "Contraction - The Fuel of Imagination",
    60: "Limitation - Acceptance of bounds"
})

# Astrology Keywords for Synthesis
MEGA_MATRIX = {
    "Sun": {"core": "Life Purpose", "action": "Radiating"},
    "Moon": {"core": "Emotional Needs", "action": "Feeling"},
    "Mars": {"core": "Drive & Conflict", "action": "Acting"},
    "Venus": {"core": "Values & Love", "action": "Attracting"},
    "Jupiter": {"core": "Expansion & Luck", "action": "Growing"},
    "Saturn": {"core": "Discipline & Karma", "action": "Structuring"},
    "Mercury": {"core": "Communication", "action": "Thinking"},
}

# Numerology Meanings
NUMEROLOGY_LORE = {
    1: "The Leader - Independent and ambitious.",
    2: "The Peacemaker - Diplomatic and intuitive.",
    3: "The Creative - Expressive and social.",
    4: "The Builder - Practical and grounded.",
    5: "The Adventurer - Freedom-loving and versatile.",
    6: "The Nurturer - Responsible and caring.",
    7: "The Seeker - Analytical and spiritual.",
    8: "The Powerhouse - Material success and authority.",
    9: "The Humanitarian - Compassionate and generous.",
    11: "Master Number - Spiritual Messenger.",
    22: "Master Builder - Manifesting dreams into reality.",
    33: "Master Teacher - Compassionate service."
}

# ==============================================================================
# 3. HELPER & LOGIC FUNCTIONS
# ==============================================================================

def validate_date(date_str: str):
    """Safely extracts YYYY-MM-DD from strings like '1992-11-06T08:00'."""
    try:
        if "T" in date_str:
            return date_str.split("T")[0]
        return date_str
    except Exception:
        return datetime.date.today().strftime("%Y-%m-%d")

def calculate_life_path(dob_str: str) -> int:
    """Calculates Life Path Number from YYYY-MM-DD string."""
    try:
        clean_date = validate_date(dob_str)
        parts = clean_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        def reduce_sum(n):
            while n > 9 and n not in [11, 22, 33]:
                n = sum(int(digit) for digit in str(n))
            return n

        # Reduce components individually first
        r_year = reduce_sum(year)
        r_month = reduce_sum(month)
        r_day = reduce_sum(day)
        
        total = r_year + r_month + r_day
        final_lp = reduce_sum(total)
        return final_lp
    except Exception:
        return 0

def resolve_location(city_name: str):
    """
    Lazy loads TimezoneFinder to prevent startup timeouts.
    Returns (lat, lon, timezone_str).
    """
    city_lower = city_name.lower().strip()
    lat, lon = 0.0, 0.0
    
    # Check cache first
    if city_lower in CITY_DB:
        lat, lon = CITY_DB[city_lower]
    else:
        try:
            geolocator = Nominatim(user_agent="astro_app_render")
            location = geolocator.geocode(city_name)
            if location:
                lat, lon = location.latitude, location.longitude
        except:
            lat, lon = 0.0, 0.0 # Fallback

    # Lazy Load TimezoneFinder
    from timezonefinder import TimezoneFinder
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=lon, lat=lat) or "UTC"
    
    return lat, lon, tz_str

def get_key_data(planet_name, sign, degree):
    """Mock Human Design Gate calculation based on Zodiac Degree."""
    # This is a simplified mapping logic for demonstration.
    # In a full system, you map 360 degrees to the 64 gates.
    total_deg = 0
    sign_list = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    if sign in sign_list:
        idx = sign_list.index(sign)
        total_deg = (idx * 30) + degree
    
    # Map 0-360 to 0-63 index of RAVE_ORDER
    gate_idx = int((total_deg / 360) * 64) % 64
    gate = RAVE_ORDER[gate_idx]
    return gate, KEY_LORE.get(gate, "Unknown Energy")

def get_hd_profile(sun_gate, earth_gate):
    """Returns a mock HD Profile (e.g., '4/6') based on gate lines."""
    # Simplified logic: use modulo to simulate line calculation
    line_sun = (sun_gate % 6) + 1
    line_earth = (earth_gate % 6) + 1
    return f"{line_sun}/{line_earth}"

def generate_desc(planet, sign, house):
    """Generates astrological description string."""
    core = MEGA_MATRIX.get(planet, {}).get("core", "Energy")
    return f"Your {planet} is in {sign}, placing focus on {core} in the realm of {house}."

def get_strategic_advice(struggle: str, chart_objects):
    """
    Scans user struggle and returns advice based on planetary placements.
    chart_objects is a dict of {PlanetName: {Sign: X, House: Y}}
    """
    struggle = struggle.lower()
    advice = ""
    
    # 1. Money/Career Advice (Jupiter/Saturn)
    if "money" in struggle or "career" in struggle or "work" in struggle:
        jup_sign = chart_objects.get("Jupiter", {}).get("Sign", "Unknown")
        sat_sign = chart_objects.get("Saturn", {}).get("Sign", "Unknown")
        advice += (
            f"<b>Financial Strategy:</b> With Jupiter in {jup_sign}, expand by taking calculated risks in this area. "
            f"However, Saturn in {sat_sign} demands you build structured discipline here first.<br>"
        )

    # 2. Love/Relationships (Venus/Moon)
    if "love" in struggle or "relationship" in struggle or "partner" in struggle:
        ven_sign = chart_objects.get("Venus", {}).get("Sign", "Unknown")
        moon_sign = chart_objects.get("Moon", {}).get("Sign", "Unknown")
        advice += (
            f"<b>Relational Strategy:</b> Your Venus in {ven_sign} seeks connection through this archetype, "
            f"but ensure your Moon in {moon_sign} feels emotionally safe before opening up.<br>"
        )

    # 3. Purpose/Direction (Sun/Mars)
    if "purpose" in struggle or "lost" in struggle or "life" in struggle:
        sun_sign = chart_objects.get("Sun", {}).get("Sign", "Unknown")
        mars_sign = chart_objects.get("Mars", {}).get("Sign", "Unknown")
        advice += (
            f"<b>Purpose Strategy:</b> Your core vitality (Sun in {sun_sign}) shines when you adopt the "
            f"drive and action style of Mars in {mars_sign}. Just do it.<br>"
        )

    if not advice:
        advice = "Focus on your Solar Strategy (Sun placement) to gain clarity on this issue."
        
    return advice

def create_pdf_b64(name, life_path, hd_profile, advice_text, chart_data):
    """
    Generates a PDF using FPDF (Lazy Loaded) and returns base64 string.
    """
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Cosmic Blueprint Report', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title Section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
    pdf.ln(5)
    
    # Life Path & Profile
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Life Path Number: {life_path}", 0, 1)
    pdf.cell(0, 10, f"Human Design Profile: {hd_profile}", 0, 1)
    pdf.ln(10)
    
    # Advice Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Strategic Advice:", 0, 1)
    pdf.set_font("Arial", size=11)
    # Strip HTML tags for PDF text
    clean_advice = advice_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
    pdf.multi_cell(0, 7, clean_advice)
    pdf.ln(10)
    
    # Chart Data
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Planetary Positions:", 0, 1)
    pdf.set_font("Arial", size=10)
    
    for planet, data in chart_data.items():
        line = f"{planet}: {data['Sign']} (Gate {data['Gate']})"
        pdf.cell(0, 7, line, 0, 1)

    # Output as base64
    # FPDF2 output() returns bytes by default if no name provided, or string in older versions.
    # We force byte output to be safe.
    try:
        pdf_bytes = pdf.output(dest='S').encode('latin-1') # Older FPDF2 method
    except:
        pdf_bytes = pdf.output() # Newer FPDF2 method returns bytes directly

    b64_str = base64.b64encode(pdf_bytes).decode('utf-8')
    return b64_str

# ==============================================================================
# 4. MAIN ROUTE
# ==============================================================================

@app.post("/calculate", response_class=HTMLResponse)
async def calculate_chart(
    name: str = Form(...),
    dob: str = Form(...),
    tob: str = Form("12:00"),
    city: str = Form(...),
    struggle: str = Form("General")
):
    # 1. Parsing & Validation
    clean_dob = validate_date(dob)
    life_path = calculate_life_path(clean_dob)
    lp_desc = NUMEROLOGY_LORE.get(life_path, "A path of mystery.")
    
    # 2. Location & Timezone
    lat, lon, tz_str = resolve_location(city)
    
    # 3. Flatlib Chart Calculation
    date_obj = Datetime(clean_dob, tob, tz_str)
    pos_obj = GeoPos(lat, lon)
    chart = Chart(date_obj, pos_obj)
    
    # 4. Data Extraction & Logic
    chart_data = {}
    hd_sun_gate = 1
    hd_earth_gate = 2
    
    # We iterate over standard planets defined in flatlib
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
               const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    
    for p_id in planets:
        obj = chart.get(p_id)
        sign = obj.sign
        # Extract degree (0-30 within sign)
        deg = obj.lon % 30 
        
        gate, gate_desc = get_key_data(p_id, sign, deg)
        
        chart_data[p_id] = {
            "Sign": sign,
            "House": "Unknown", # House calc requires specific system, omitted for brevity
            "Gate": gate,
            "Desc": generate_desc(p_id, sign, "your chart")
        }
        
        if p_id == const.SUN:
            hd_sun_gate = gate
        if p_id == const.EARTH: # Note: Flatlib might not have Earth explicitly, usually opposite Sun
            hd_earth_gate = gate

    # Calculate HD Profile
    hd_profile = get_hd_profile(hd_sun_gate, hd_earth_gate)
    
    # 5. Strategic Advice
    advice_html = get_strategic_advice(struggle, chart_data)
    
    # 6. PDF Generation
    pdf_b64 = create_pdf_b64(name, life_path, hd_profile, advice_html, chart_data)
    
    # 7. HTML Response Construction
    # Note the .footer-guard div at the bottom
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Cosmic Blueprint</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: transparent; color: #fff; padding: 20px; }}
            .card {{ background: rgba(0,0,0,0.8); padding: 20px; border-radius: 10px; border: 1px solid #444; margin-bottom: 20px; }}
            h1, h2 {{ color: #d4af37; }}
            .highlight {{ color: #00ffcc; font-weight: bold; }}
            .btn {{ 
                background: #d4af37; color: #000; padding: 10px 20px; 
                text-decoration: none; border-radius: 5px; font-weight: bold; 
                cursor: pointer; border: none; font-size: 16px;
            }}
            .footer-guard {{ height: 500px; width: 100%; clear: both; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Results for {name}</h1>
            <p><strong>Date:</strong> {clean_dob} | <strong>Location:</strong> {city}</p>
        </div>

        <div class="card">
            <h2>Numerology</h2>
            <p><strong>Life Path:</strong> <span class="highlight">{life_path}</span></p>
            <p>{lp_desc}</p>
        </div>

        <div class="card">
            <h2>Human Design</h2>
            <p><strong>Profile:</strong> <span class="highlight">{hd_profile}</span></p>
            <p><strong>Sun Gate:</strong> {hd_sun_gate} ({KEY_LORE.get(hd_sun_gate, '')})</p>
        </div>

        <div class="card">
            <h2>Strategic Guidance</h2>
            <p><em>Regarding "{struggle}"...</em></p>
            <p>{advice_html}</p>
        </div>
        
        <div class="card">
            <h2>Planetary Data</h2>
            <ul>
                {"".join([f"<li><strong>{k}:</strong> {v['Sign']} (Gate {v['Gate']})</li>" for k,v in chart_data.items()])}
            </ul>
        </div>

        <div class="card">
            <h3>Keep this Report</h3>
            <button onclick="downloadPDF()" class="btn">Download Full PDF</button>
        </div>

        <input type="hidden" id="pdfData" value="{pdf_b64}">

        <script>
            function downloadPDF() {{
                const b64 = document.getElementById('pdfData').value;
                const link = document.createElement('a');
                link.href = 'data:application/pdf;base64,' + b64;
                link.download = 'Cosmic_Blueprint_{name}.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}
        </script>

        <div class="footer-guard"></div>
    </body>
    </html>
    """
    
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
