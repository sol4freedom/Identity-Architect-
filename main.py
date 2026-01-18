from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime
import traceback
import base64

# --- IMPORTS ---
from geopy.geocoders import Nominatim
# Lazy loading applied later for heavy libs (TimezoneFinder, FPDF)
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ==========================================
# 1. INPUTS & ROUTES (MOVED TO TOP)
# ==========================================

class UserInput(BaseModel):
    name: str; date: str; time: str; city: str; struggle: str
    email: str = None 
    
    @validator('date', pre=True)
    def clean_date_format(cls, v):
        if isinstance(v, str) and "T" in v: return v.split("T")[0]
        return v
    @validator('time', pre=True)
    def clean_time(cls, v): return v.split(".")[0] if "." in v else v

@app.get("/")
def home():
    return {"status": "System Status: Online", "message": "The server is running correctly."}

@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        # 1. PREPARE DATA
        safe_date = data.date.split("T")[0] if "T" in data.date else data.date
        lat, lon, tz, source = resolve_location(data.city, safe_date, data.time)

        # 2. CALCULATE ASTROLOGY
        dt = Datetime(safe_date.replace("-", "/"), data.time, tz)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO], hsys=const.HOUSES_PLACIDUS)
        
        objs = {k: chart.get(getattr(const, k.upper())) for k in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
        rising = chart.get(const.HOUSE1)

        # 3. CALCULATE DESIGN
        d_dt = datetime.datetime.strptime(safe_date, "%Y-%m-%d") - datetime.timedelta(days=88)
        d_chart = Chart(Datetime(d_dt.strftime("%Y/%m/%d"), data.time, tz), geo, IDs=[const.SUN, const.MOON])
        d_sun = d_chart.get(const.SUN); d_moon = d_chart.get(const.MOON)

        lp = calculate_life_path(safe_date)
        hd = get_hd_profile(objs['Sun'].lon, d_sun.lon)
        keys = {
            'lw': get_key_data(objs['Sun'].lon), 'evo': get_key_data((objs['Sun'].lon + 180) % 360),
            'rad': get_key_data(d_sun.lon), 'pur': get_key_data((d_sun.lon + 180) % 360),
            'att': get_key_data(d_moon.lon)
        }

        # 4. GET ADVICE & PDF
        topic, advice = get_strategic_advice(data.struggle, objs, rising)
        pdf_b64 = create_pdf_b64(data, lp, hd, keys, objs, rising)

        # 5. GENERATE HTML REPORT
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <script>
        function downloadPDF(b64Data) {{
            const linkSource = `data:
