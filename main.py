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

# ------------------------------------------------------------------------------
# 2. APP CONFIGURATION & LOGGING
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
# 3. DATA DICTIONARIES
# ------------------------------------------------------------------------------
CITY_DB = {
    "minneapolis": (44.9778, -93.2650),
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "sao paulo": (-23.5558, -46.6396),
    "tokyo": (35.6762, 139.6503),
    "los angeles": (34.0522, -118.2437)
}

RAVE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# ------------------------------------------------------------------------------
# 4. LOGIC FUNCTIONS
# ------------------------------------------------------------------------------

def safe_get_date(date_input):
    """Parses date from any weird format the frontend sends."""
    if not date_input:
        return datetime.date.today().strftime("%Y-%m-%d")
    s = str(date_input).strip()
    # Handle ISO format 1990-01-01T00:00:00.000Z
    if "T" in s:
        s = s.split("T")[0]
    return s

def calculate_life_path(dob_str: str) -> int:
    try:
        clean_date = safe_get_date(dob_str)
        # Ensure we have YYYY-MM-DD
        if clean_date.count("-") != 2:
            return 0
        parts = clean_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        def reduce_sum(n):
            while n > 9 and n not in [11, 22, 33]:
                n = sum(int(digit) for digit in str(n))
            return n

        total = reduce_sum(year) + reduce_sum(month) + reduce_sum(day)
        return reduce_sum(total)
    except Exception as e:
        logger.error(f"Numerology Error: {e}")
        return 0

def resolve_location(city_name: str):
    city_lower = str(city_name).lower().strip()
    lat, lon = 0.0, 0.0
    
    # 1. Try DB
    if city_lower in CITY_DB:
        lat, lon = CITY_DB[city_lower]
    else:
        # 2. Try Geopy
        try:
            geolocator = Nominatim(user_agent="astro_app_render")
            location = geolocator.geocode(city_name)
            if location:
                lat, lon = location.latitude, location.longitude
        except Exception as e:
            logger.error(f"Geopy Error: {e}")
            pass

    # 3. Get Timezone
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=lon, lat=lat) or "UTC"
    except:
        tz_str = "UTC"
    
    return lat, lon, tz_str

def get_hd_gate(sign, degree):
    """Maps Zodiac Sign + Degree -> Human Design Gate"""
    sign_list = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    total_deg = 0
    if sign in sign_list:
        idx = sign_list.index(sign)
        total_deg = (idx * 30) + degree
    
    # 360 degrees / 64 gates
    gate_idx = int((total_deg / 360) * 64) % 64
    return RAVE_ORDER[gate_idx]

def get_strategic_advice(struggle, chart_objects):
    struggle = str(struggle).lower()
    advice = ""
    
    if "money" in struggle or "career" in struggle:
        sign = chart_objects.get("Jupiter", {}).get("Sign", "Unknown")
        advice += f"<b>Wealth Strategy:</b> Your Jupiter is in {sign}. Expand here.<br>"
    elif "love" in struggle or "relationship" in struggle:
        sign = chart_objects.get("Venus", {}).get("Sign", "Unknown")
        advice += f"<b>Love Strategy:</b> Your Venus is in {sign}. Value this energy.<br>"
    else:
        sign = chart_objects.get("Sun", {}).get("Sign", "Unknown")
        advice += f"<b>Core Strategy:</b> Your Sun in {sign} is your guide.<br>"
        
    return advice

def create_pdf_b64(name, life_path, hd_profile, advice_text, chart_data):
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Cosmic Blueprint', 0, 1, 'C')
            self.ln(10)

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(0, 10, f"Name: {name}", 0, 1)
        pdf.cell(0, 10, f"Life Path: {life_path} | Profile: {hd_profile}", 0, 1)
        pdf.ln(5)
        
        clean_adv = advice_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, f"Advice:\n{clean_adv}")
        pdf.ln(5)
        
        for k, v in chart_data.items():
            pdf.cell(0, 7, f"{k}: {v['Sign']} (Gate {v['Gate']})", 0, 1)

        # Output bytes safely
        return base64.b64encode(pdf.output()).decode('utf-8')
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        return ""

# ------------------------------------------------------------------------------
# 5. MAIN ENDPOINT
# ------------------------------------------------------------------------------

@app.post("/calculate")
async def calculate_chart(request: Request):
    """
    Robust Endpoint: Accepts ANY input format, applies defaults, NEVER crashes (422).
    Returns JSON {"report": html} to satisfy Wix Frontend.
    """
    # 1. Parse Input Safely
    data = {}
    content_type = request.headers.get("content-type", "")
    
    try:
        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
    except Exception as e:
        logger.error(f"Parsing Error: {e}")

    # 2. Extract Data (With Defaults)
    name = data.get("name") or "Traveler"
    dob = data.get("dob") or "1990-01-01"
    tob = data.get("tob") or "12:00"
    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"
    
    logger.info(f"Processing for: {name}, City: {city}, DOB: {dob}")

    # 3. Calculations
    clean_dob = safe_get_date(dob)
    life_path = calculate_life_path(clean_dob)
    lat, lon, tz_str = resolve_location(city)
    
    # Astrology Chart
    try:
        date_obj = Datetime(clean_dob, tob, tz_str)
        pos_obj = GeoPos(lat, lon)
        chart = Chart(date_obj, pos_obj)
        
        chart_data = {}
        hd_sun, hd_earth = 1, 2
        
        for p_id in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]:
            obj = chart.get(p_id)
            gate = get_hd_gate(obj.sign, obj.lon % 30)
            chart_data[p_id] = {"Sign": obj.sign, "Gate": gate}
            
            if p_id == const.SUN: hd_sun = gate
            if p_id == const.EARTH: hd_earth = gate
            
        hd_profile = f"{(hd_sun % 6) + 1}/{(hd_earth % 6) + 1}"
    except Exception as e:
        logger.error(f"Chart Calc Error: {e}")
        hd_profile = "unknown"
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1}}

    # 4. Generate Outputs
    advice_html = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, life_path, hd_profile, advice_html, chart_data)

    # 5. Return JSON containing HTML (For Wix Compatibility)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cosmic Blueprint</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: transparent; color: #fff; padding: 20px; }}
            .card {{ background: rgba(0,0,0,0.8); padding: 20px; border: 1px solid #555; margin-bottom: 20px; border-radius: 8px; }}
            h2 {{ color: #d4af37; border-bottom: 1px solid #555; padding-bottom: 5px; margin-top: 0; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 5px; }}
            .btn {{ 
                background: #d4af37; color: #000; padding: 12px 24px; 
                text-decoration: none; font-weight: bold; border:none; 
                cursor:pointer; font-size:16px; display: inline-block;
                border-radius: 4px;
            }}
            .footer-guard {{ height: 500px; width: 100%; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Report for {name}</h2>
            <p><strong>Life Path:</strong> {life_path}</p>
            <p><strong>HD Profile:</strong> {hd_profile}</p>
        </div>
        
        <div class="card">
            <h2>Strategic Guidance</h2>
            <p>{advice_html}</p>
        </div>

        <div class="card">
            <h2>Planetary Data</h2>
            <ul>
                {"".join([f"<li><strong>{k}:</strong> {v['Sign']} (Gate {v['Gate']})</li>" for k,v in chart_data.items()])}
            </ul>
        </div>

        <div class="card">
            <button onclick="dlPDF()" class="btn">Download PDF</button>
        </div>

        <input type="hidden" id="pdfData" value="{pdf_b64}">
        <script>
            function dlPDF() {{
                const b64 = document.getElementById('pdfData').value;
                if(!b64) {{ alert('PDF generation failed.'); return; }}
                const link = document.createElement('a');
                link.href = 'data:application/pdf;base64,' + b64;
                link.download = 'Cosmic_Report_{name}.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}
        </script>
        
        <div class="footer-guard"></div>
    </body>
    </html>
    """
    
    return {"report": html_content}
