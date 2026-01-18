import sys
import base64
import datetime
import json
import logging
from typing import Optional, Dict, Any

# ------------------------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------------------------
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
import flatlib
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import pytz

# ------------------------------------------------------------------------------
# 2. APP CONFIGURATION
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 3. RICH DATA (The Brains)
# ------------------------------------------------------------------------------
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

RAVE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

MEGA_MATRIX = {
    "Aries": "The Pioneer (Courage)", "Taurus": "The Builder (Stability)",
    "Gemini": "The Messenger (Curiosity)", "Cancer": "The Nurturer (Protection)",
    "Leo": "The Star (Expression)", "Virgo": "The Healer (Precision)",
    "Libra": "The Diplomat (Harmony)", "Scorpio": "The Mystic (Transformation)",
    "Sagittarius": "The Explorer (Freedom)", "Capricorn": "The Boss (Ambition)",
    "Aquarius": "The Visionary (Innovation)", "Pisces": "The Dreamer (Empathy)"
}

KEY_LORE = {i: f"Gate {i}" for i in range(1, 65)}
# (You can expand this later, keeping it light for safety)

# ------------------------------------------------------------------------------
# 4. LOGIC FUNCTIONS
# ------------------------------------------------------------------------------

def safe_get_date(date_input):
    if not date_input: return datetime.date.today().strftime("%Y-%m-%d")
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def calculate_life_path(dob_str):
    try:
        clean = safe_get_date(dob_str)
        parts = clean.split("-")
        if len(parts) != 3: return 0
        total = sum(int(p) for p in parts)
        
        while total > 9 and total not in [11, 22, 33]:
            total = sum(int(d) for d in str(total))
        return total
    except: return 0

def resolve_location(city_name):
    city_lower = str(city_name).lower().strip()
    
    # 1. Check Backup DB
    for key in CITY_DB:
        if key in city_lower:
            return CITY_DB[key]
            
    # 2. Geopy Lookup
    try:
        geolocator = Nominatim(user_agent="ia_v60_full")
        loc = geolocator.geocode(city_name)
        if loc:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=loc.longitude, lat=loc.latitude) or "UTC"
            return loc.latitude, loc.longitude, tz
    except: pass
    
    return 51.50, -0.12, "Europe/London" # Default

def get_hd_gate(sign, degree):
    sign_list = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    if sign not in sign_list: return 1
    
    idx = sign_list.index(sign)
    abs_deg = (idx * 30) + degree
    gate_idx = int((abs_deg / 360) * 64) % 64
    return RAVE_ORDER[gate_idx]

def get_strategic_advice(struggle, chart):
    s = str(struggle).lower()
    sun_sign = chart.get("Sun", {}).get("Sign", "Unknown")
    
    if any(x in s for x in ['money', 'career', 'job', 'wealth']):
        jup = chart.get("Jupiter", {}).get("Sign", "Unknown")
        sat = chart.get("Saturn", {}).get("Sign", "Unknown")
        return "Wealth Architecture", f"Your path to abundance combines the expansion of **Jupiter in {jup}** with the structure of **Saturn in {sat}**."
        
    elif any(x in s for x in ['love', 'relationship', 'partner']):
        ven = chart.get("Venus", {}).get("Sign", "Unknown")
        moon = chart.get("Moon", {}).get("Sign", "Unknown")
        return "Relational Design", f"Your heart speaks the language of **Venus in {ven}**, while your soul needs the safety of **Moon in {moon}**."
        
    else:
        ris = chart.get("Rising", {}).get("Sign", "Unknown")
        return "Core Alignment", f"When in doubt, return to your **{ris} Rising**. This is your hull and your strategy for navigating life."

def create_pdf_b64(name, lp, hd, advice, chart):
    from fpdf import FPDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
            self.ln(5)
            
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        pdf.cell(0, 10, f"Life Path: {lp} | Profile: {hd}", 0, 1)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Strategic Guidance", 0, 1)
        pdf.set_font("Arial", '', 12)
        clean_advice = advice[1].replace("**", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, clean_advice)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Planetary Blueprint", 0, 1)
        pdf.set_font("Arial", '', 12)
        
        for k, v in chart.items():
            sign = v.get("Sign", "?")
            gate = v.get("Gate", "?")
            pdf.cell(0, 8, f"{k}: {sign} (Gate {gate})", 0, 1)
            
        return base64.b64encode(pdf.output().encode('latin-1', 'ignore')).decode('utf-8')
    except:
        return ""

# ------------------------------------------------------------------------------
# 5. MAIN ENDPOINT
# ------------------------------------------------------------------------------

@app.post("/calculate")
async def calculate_chart(request: Request):
    # 1. Parse Data (Safe Mode)
    data = {}
    try:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct: data = await request.json()
        else: data = dict(await request.form())
    except: pass

    # 2. Defaults to prevent crash
    name = data.get("name") or "Traveler"
    dob = safe_get_date(data.get("dob"))
    tob = data.get("tob") or "12:00"
    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"

    # 3. Calculations (The Real Engine)
    try:
        lat, lon, tz_str = resolve_location(city)
        dt_obj = Datetime(dob, tob, tz_str)
        geo_obj = GeoPos(lat, lon)
        chart = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        hd_sun_gate = 1
        hd_earth_gate = 2
        
        for p in planets:
            obj = chart.get(getattr(const, p.upper()))
            gate = get_hd_gate(obj.sign, obj.lon % 30)
            chart_data[p] = {"Sign": obj.sign, "Gate": gate}
            if p == "Sun": hd_sun_gate = gate
            if p == "Earth": hd_earth_gate = gate # Note: Flatlib doesn't calc Earth by default, using Sun-180 logic later if needed
            
        # Rising Sign
        asc = chart.get(const.ASC)
        chart_data["Rising"] = {"Sign": asc.sign, "Gate": get_hd_gate(asc.sign, asc.lon % 30)}
        
        # Profile (Simplified)
        line_sun = (hd_sun_gate % 6) + 1
        hd_profile = f"{line_sun}/?" 
        
        lp = calculate_life_path(dob)
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": "?"}}
        hd_profile = "Unknown"
        lp = 0

    # 4. Generate Advice & PDF
    topic, advice_text = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, lp, hd_profile, (topic, advice_text), chart_data)

    # 5. Return JSON with Rich HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
        body {{ font-family: 'Source Sans Pro', sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
        .card {{ background: #fff; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h2 {{ font-family: 'Playfair Display', serif; color: #D4AF37; margin-top: 0; }}
        .highlight {{ color: #C71585; font-weight: bold; }}
        .btn {{ 
            background-color: #D4AF37; color: white; border: none; padding: 15px 30px; 
            font-size: 16px; border-radius: 50px; cursor: pointer; display: block; 
            width: 100%; max-width: 300px; margin: 20px auto; text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
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
            <p><strong>☀️ Sun in {chart_data.get('Sun',{}).get('Sign','?')}</strong>: {MEGA_MATRIX.get(chart_data.get('Sun',{}).get('Sign','?'), '')}</p>
            <p><strong>🌙 Moon in {chart_data.get('Moon',{}).get('Sign','?')}</strong>: {MEGA_MATRIX.get(chart_data.get('Moon',{}).get('Sign','?'), '')}</p>
            <p><strong>🏹 Rising in {chart_data.get('Rising',{}).get('Sign','?')}</strong>: {MEGA_MATRIX.get(chart_data.get('Rising',{}).get('Sign','?'), '')}</p>
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
