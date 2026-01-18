import sys
import base64
import datetime
import json
from fastapi import FastAPI, Request
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

# Backup coordinates
CITY_DB = {
    "minneapolis": (44.9778, -93.2650),
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "sao paulo": (-23.5558, -46.6396),
    "tokyo": (35.6762, 139.6503),
    "los angeles": (34.0522, -118.2437)
}

# Human Design Gate Order
RAVE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# The 64 Keys / Hexagram Meanings
KEY_LORE = {i: f"Gate {i}: Archetypal Energy" for i in range(1, 65)}
KEY_LORE.update({
    1: "The Creative - Self Expression",
    2: "The Receptive - Direction of Self",
    41: "Contraction - The Fuel of Imagination",
    60: "Limitation - Acceptance of Bounds"
})

# Astrology Keywords
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

def validate_date(date_str):
    """Safely extracts YYYY-MM-DD from various formats."""
    if not date_str:
        return datetime.date.today().strftime("%Y-%m-%d")
    s = str(date_str)
    if "T" in s:
        return s.split("T")[0]
    return s

def calculate_life_path(dob_str: str) -> int:
    try:
        clean_date = validate_date(dob_str)
        parts = clean_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        def reduce_sum(n):
            while n > 9 and n not in [11, 22, 33]:
                n = sum(int(digit) for digit in str(n))
            return n

        r_year = reduce_sum(year)
        r_month = reduce_sum(month)
        r_day = reduce_sum(day)
        
        total = r_year + r_month + r_day
        return reduce_sum(total)
    except:
        return 0

def resolve_location(city_name: str):
    """Lazily loads TimezoneFinder to avoid timeout."""
    city_lower = str(city_name).lower().strip()
    lat, lon = 0.0, 0.0
    
    # 1. Check Dictionary
    if city_lower in CITY_DB:
        lat, lon = CITY_DB[city_lower]
    else:
        # 2. Try Geopy
        try:
            geolocator = Nominatim(user_agent="astro_app_render")
            location = geolocator.geocode(city_name)
            if location:
                lat, lon = location.latitude, location.longitude
        except:
            pass 

    # 3. Get Timezone
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=lon, lat=lat) or "UTC"
    except:
        tz_str = "UTC"
    
    return lat, lon, tz_str

def get_key_data(planet_name, sign, degree):
    """Maps Zodiac position to Human Design Gate."""
    total_deg = 0
    sign_list = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    if sign in sign_list:
        idx = sign_list.index(sign)
        total_deg = (idx * 30) + degree
    
    gate_idx = int((total_deg / 360) * 64) % 64
    gate = RAVE_ORDER[gate_idx]
    return gate, KEY_LORE.get(gate, "Unknown Energy")

def get_hd_profile(sun_gate, earth_gate):
    line_sun = (sun_gate % 6) + 1
    line_earth = (earth_gate % 6) + 1
    return f"{line_sun}/{line_earth}"

def get_strategic_advice(struggle, chart_objects):
    struggle = str(struggle).lower()
    advice = ""
    
    # Logic: specific advice based on struggle keywords + planetary signs
    if "money" in struggle or "career" in struggle:
        jup = chart_objects.get("Jupiter", {}).get("Sign", "?")
        advice += f"<b>Financial Strategy:</b> Leverage your Jupiter in {jup}. Expand through this archetype.<br>"
    
    if "love" in struggle or "relationship" in struggle:
        ven = chart_objects.get("Venus", {}).get("Sign", "?")
        advice += f"<b>Relational Strategy:</b> Your Venus in {ven} indicates your values in connection.<br>"
        
    if not advice:
        sun = chart_objects.get("Sun", {}).get("Sign", "?")
        advice += f"<b>Core Strategy:</b> When in doubt, shine your light through your Sun in {sun}."
        
    return advice

def create_pdf_b64(name, life_path, hd_profile, advice_text, chart_data):
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Cosmic Blueprint', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(0, 10, f"Report for: {name}", 0, 1)
    pdf.cell(0, 10, f"Life Path: {life_path} | Profile: {hd_profile}", 0, 1)
    pdf.ln(5)
    
    clean_advice = advice_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
    pdf.multi_cell(0, 7, f"Advice:\n{clean_advice}")
    pdf.ln(5)
    
    for p, d in chart_data.items():
        pdf.cell(0, 7, f"{p}: {d['Sign']} (Gate {d['Gate']})", 0, 1)

    # STRICT: return base64 encoded bytes
    return base64.b64encode(pdf.output()).decode('utf-8')

# ==============================================================================
# 4. MAIN ROUTE (UNIVERSAL ADAPTER)
# ==============================================================================

@app.post("/calculate", response_class=HTMLResponse)
async def calculate_chart(request: Request):
    """
    Universal Adapter: Accepts BOTH JSON and Form data to prevent 422 Errors.
    """
    # 1. Parse Input (Universal)
    content_type = request.headers.get("content-type", "")
    data = {}
    
    try:
        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
    except Exception:
        data = {}

    # 2. Extract Fields with Defaults
    name = data.get("name", "Traveler")
    dob = data.get("dob", "")
    tob = data.get("tob", "12:00")
    city = data.get("city", "")
    struggle = data.get("struggle", "General")

    # 3. Validation
    if not dob or not city:
        return HTMLResponse(content=f"""
        <html><body style="background:#222; color:#fff; padding:20px;">
            <h3>Data Missing</h3>
            <p>We received the request but 'Date of Birth' or 'City' was empty.</p>
            <p>Debug: {json.dumps(data, default=str)}</p>
        </body></html>
        """)

    # 4. Execute Logic
    clean_dob = validate_date(dob)
    life_path = calculate_life_path(clean_dob)
    lat, lon, tz_str = resolve_location(city)
    
    date_obj = Datetime(clean_dob, tob, tz_str)
    pos_obj = GeoPos(lat, lon)
    chart = Chart(date_obj, pos_obj)
    
    chart_data = {}
    hd_sun, hd_earth = 1, 2
    
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
               const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    
    for p_id in planets:
        obj = chart.get(p_id)
        gate, _ = get_key_data(p_id, obj.sign, obj.lon % 30)
        chart_data[p_id] = {"Sign": obj.sign, "Gate": gate}
        if p_id == const.SUN: hd_sun = gate
        if p_id == const.EARTH: hd_earth = gate

    hd_profile = get_hd_profile(hd_sun, hd_earth)
    advice_html = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, life_path, hd_profile, advice_html, chart_data)

    # 5. Return HTML Response
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Result</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: transparent; color: #fff; padding: 20px; }}
            .card {{ background: rgba(0,0,0,0.8); padding: 20px; border: 1px solid #555; margin-bottom: 20px; border-radius: 8px; }}
            h2 {{ color: #d4af37; border-bottom: 1px solid #555; padding-bottom: 5px; }}
            .btn {{ background: #d4af37; color: #000; padding: 10px 20px; text-decoration: none; font-weight: bold; border:none; cursor:pointer; font-size:16px; }}
            .footer-guard {{ height: 600px; width: 100%; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Cosmic Report for {name}</h2>
            <p><strong>Life Path:</strong> {life_path} ({NUMEROLOGY_LORE.get(life_path, '')})</p>
            <p><strong>HD Profile:</strong> {hd_profile}</p>
        </div>
        
        <div class="card">
            <h2>Guidance on "{struggle}"</h2>
            <p>{advice_html}</p>
        </div>

        <div class="card">
            <h2>Planetary Alignments</h2>
            <ul>
                {"".join([f"<li>{k}: {v['Sign']} (Gate {v['Gate']})</li>" for k,v in chart_data.items()])}
            </ul>
        </div>

        <div class="card">
            <button onclick="dlPDF()" class="btn">Download PDF Report</button>
        </div>

        <input type="hidden" id="pdfData" value="{pdf_b64}">
        <script>
            function dlPDF() {{
                const b64 = document.getElementById('pdfData').value;
                const link = document.createElement('a');
                link.href = 'data:application/pdf;base64,' + b64;
                link.download = 'Report_{name}.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}
        </script>
        
        <div class="footer-guard"></div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
