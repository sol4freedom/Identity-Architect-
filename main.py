from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime
import traceback
import base64

# --- IMPORTS ---
from geopy.geocoders import Nominatim
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- DATA LIBRARIES ---
CITY_DB = {
    "sao paulo": {"lat": -23.55, "lon": -46.63, "tz_std": -3.0, "hemisphere": "S"},
    "minneapolis": {"lat": 44.97, "lon": -93.26, "tz_std": -6.0, "hemisphere": "N"},
    "london": {"lat": 51.50,  "lon": -0.12,  "tz_std": 0.0,  "hemisphere": "N"}
}

RAVE_ORDER = [25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36]

KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness."}, 
    2: {"name": "The Receptive", "story": "The Divine Feminine blueprint."},
    # (Simplified for length safety - system works with this)
}

MEGA_MATRIX = {
    "Aries": {"Sun": "Pioneer", "Moon": "Independent", "Rising": "Courage"},
    "Taurus": {"Sun": "Builder", "Moon": "Comfort", "Rising": "Reliable"},
    "Gemini": {"Sun": "Messenger", "Moon": "Conversation", "Rising": "Curious"},
    "Cancer": {"Sun": "Nurturer", "Moon": "Safety", "Rising": "Gentle"},
    "Leo": {"Sun": "Star", "Moon": "Appreciation", "Rising": "Charisma"},
    "Virgo": {"Sun": "Healer", "Moon": "Routine", "Rising": "Modest"},
    "Libra": {"Sun": "Diplomat", "Moon": "Harmony", "Rising": "Grace"},
    "Scorpio": {"Sun": "Mystic", "Moon": "Trust", "Rising": "Intensity"},
    "Sagittarius": {"Sun": "Explorer", "Moon": "Freedom", "Rising": "Optimism"},
    "Capricorn": {"Sun": "Boss", "Moon": "Control", "Rising": "Authority"},
    "Aquarius": {"Sun": "Visionary", "Moon": "Detachment", "Rising": "Unique"},
    "Pisces": {"Sun": "Dreamer", "Moon": "Solitude", "Rising": "Empathy"}
}

NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "Leading with independence."}, 
    11: {"name": "The Illuminator", "desc": "Channeling intuition."}
}


# --- LOGIC FUNCTIONS ---
def get_key_data(degree):
    if degree is None: return {"name": "Unknown", "story": ""}
    index = int(degree / 5.625)
    if index >= 64: index = 0
    key_number = RAVE_ORDER[index]
    return KEY_LORE.get(key_number, {"name": f"Key {key_number}", "story": "Energy Code"})

def get_hd_profile(p_degree, d_degree):
    def get_line(deg): return int((deg % 5.625) / 0.9375) + 1
    key = f"{get_line(p_degree)}/{get_line(d_degree)}"
    return {"name": f"{key} Profile"}

def calculate_life_path(date_str):
    if "T" in date_str: date_str = date_str.split("T")[0]
    digits = [int(d) for d in date_str if d.isdigit()]
    total = sum(digits)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return NUMEROLOGY_LORE.get(total, {"number": total, "name": "The Seeker", "desc": "Walking the path."})

def generate_desc(planet, sign):
    return MEGA_MATRIX.get(sign, {}).get(planet, f"Energy of {sign}")

def resolve_location(city_input, date_str, time_str):
    city_clean = city_input.lower().strip()
    # Check backup list first
    for key in CITY_DB:
        if key in city_clean:
            return CITY_DB[key]["lat"], CITY_DB[key]["lon"], CITY_DB[key]["tz_std"], "Backup"
    
    # Try online lookup
    try:
        from timezonefinder import TimezoneFinder
        geolocator = Nominatim(user_agent="ia_v55_final", timeout=10)
        location = geolocator.geocode(city_input)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            if tz_str:
                local_tz = pytz.timezone(tz_str)
                clean_date = date_str.split("T")[0] if "T" in date_str else date_str
                naive_dt = datetime.datetime.strptime(f"{clean_date} {time_str}", "%Y-%m-%d %H:%M")
                localized_dt = local_tz.localize(naive_dt)
                return location.latitude, location.longitude, localized_dt.utcoffset().total_seconds() / 3600.0, "Automatic DB"
    except Exception as e:
        print(f"Auto-lookup failed: {e}")

    return 51.50, -0.12, 0.0, "Default"

def get_strategic_advice(struggle_text, objs, rising):
    s = struggle_text.lower()
    if any(x in s for x in ['money', 'wealth', 'finance', 'job', 'career', 'business']):
        return "Money & Career", f"Focus on Jupiter in {objs['Jupiter'].sign}."
    elif any(x in s for x in ['love', 'relationship', 'partner']):
        return "Relationships", f"Focus on Venus in {objs['Venus'].sign}."
    elif any(x in s for x in ['purpose', 'life', 'lost']):
        return "Life Purpose", f"Focus on Sun in {objs['Sun'].sign}."
    else:
        return "General", f"Lean into {rising.sign} Rising."

def create_pdf_b64(data, lp, hd, keys, objs, rising):
    from fpdf import FPDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 15)
            self.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
            self.ln(5)
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"Prepared for {data.name}", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, f"LIFE PATH: {lp['number']}", 0, 1)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 8, txt=f"Current Struggle: {data.struggle}\nAdvice: Lean into {rising.sign} Rising.")
    # FIX: Ensure clean byte output
    return base64.b64encode(bytes(pdf.output())).decode('utf-8')


# --- API ROUTES ---
class UserInput(BaseModel):
    name: str; date: str; time: str; city: str; struggle: str
    email: str = None 
    
    @validator('date', pre=True)
    def clean_date_format(cls, v):
        if isinstance(v, str) and "T" in v: return v.split("T")[0]
        return v
    @validator('time', pre=True)
    def clean_time(cls, v): return v.split(".")[0] if "." in v else v

@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        safe_date = data.date.split("T")[0] if "T" in data.date else data.date
        lat, lon, tz, source = resolve_location(data.city, safe_date, data.time)

        dt = Datetime(safe_date.replace("-", "/"), data.time, tz)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO], hsys=const.HOUSES_PLACIDUS)
        
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        objs = {k: chart.get(getattr(const, k.upper())) for k in planets}
        rising = chart.get(const.HOUSE1)

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

        topic, advice = get_strategic_advice(data.struggle, objs, rising)
        pdf_b64 = create_pdf_b64(data, lp, hd, keys, objs, rising)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <script>
        function downloadPDF(b64Data) {{
            const linkSource = `data:application/pdf;base64,${{b64Data}}`;
            const downloadLink = document.createElement("a");
            const fileName = "Integrated_Self_Code.pdf";
            downloadLink.href = linkSource;
            downloadLink.download = fileName;
            downloadLink.click();
        }}
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
            body {{ font-family: 'Source Sans Pro', sans-serif; background: #f5f5f5; color: #333; padding: 20px; line-height: 1.6; }}
            .main-container {{ max-width: 700px; margin: 0 auto; }}
            .card {{ 
                background: #fff; padding: 25px; border-radius: 12px; margin-bottom: 25px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 5px solid #ddd;
            }}
            h2 {{ font-family: 'Playfair Display', serif; color: #D4AF37; margin: 0 0 5px 0; font-size: 28px; text-align: center; }}
            h3 {{ font-family: 'Playfair Display', serif; font-size: 22px; margin: 0 0 15px 0; color: #222; }}
            .item {{ margin-bottom: 15px; border-bottom: 1px dashed #eee; padding-bottom: 10px; }}
            .item:last-child {{ border: none; padding-bottom: 0; }}
            .label {{ font-weight: 600; color: #444; font-size: 1.05em; display:block; margin-bottom: 4px; }}
            .desc {{ font-size: 0.95em; color: #666; display: block; }}
            .card.cosmic {{ border-left-color: #C71585; }}
            .card.blueprint {{ border-left-color: #D4AF37; }}
            .card.boardroom {{ border-left-color: #4682B4; }}
            .card.sanctuary {{ border-left-color: #2E8B57; }}
            .card.streets {{ border-left-color: #CD5C5C; }}
            .card.vault {{ border-left-color: #FFD700; background: #222; color: #fff; }}
            .card.vault .label {{ color: #fff; }}
            .card.vault .desc {{ color: #ccc; }}
            .card.vault h3 {{ color: #FFD700; }}
            .btn {{ 
                background-color: #D4AF37; color: white; border: none; padding: 18px 40px; font-size: 16px; 
                border-radius: 50px; font-weight: bold; cursor: pointer; display: block; margin: 30px auto; 
                width: 100%; max-width: 300px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                text-decoration: none;
            }}
            .end-marker {{ 
                text-align: center; margin-top: 60px; margin-bottom: 20px; 
                color: #aaa; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; border-top: 1px solid #ccc; padding-top: 15px;
            }}
            .footer-guard {{ height: 500px; }}
        </style>
        </head>
        <body>
            <div class="main-container">
                <div class="card" style="text-align:center; border:none;">
                    <h2>The Integrated Self</h2>
                    <div style="font-size:12px; color:#999; letter-spacing:1px;">PREPARED FOR {data.name.upper()}</div>
                </div>

                <div class="card" style="text-align:center; background:#F8F4FF; border-left:none;">
                    <div style="font-size:11px; letter-spacing:2px; margin-bottom:5px; color:#888;">LIFE PATH VIBRATION</div>
                    <h3 style="color:#6A5ACD; font-size:24px; margin:0;">{lp['number']}: {lp['name']}</h3>
                    <p style="font-style:italic; margin-top:10px;">"{lp['desc']}"</p>
                </div>

                <div class="card cosmic">
                    <h3 style="color:#C71585;">✨ The Cosmic Signature</h3>
                    <div class="item"><span class="label">☀️ Sun in {objs['Sun'].sign}:</span> <span class="desc">"{generate_desc('Sun', objs['Sun'].sign)}"</span></div>
                    <div class="item"><span class="label">🌙 Moon in {objs['Moon'].sign}:</span> <span class="desc">"{generate_desc('Moon', objs['Moon'].sign)}"</span></div>
                    <div class="item"><span class="label">🏹 Rising in {rising.sign}:</span> <span class="desc">"{generate_desc('Rising', rising.sign)}"</span></div>
                    <div class="item"><span class="label">🗣️ Mercury in {objs['Mercury'].sign}:</span> <span class="desc">"{generate_desc('Mercury', objs['Mercury'].sign)}"</span></div>
                    <div class="item"><span class="label">❤️ Venus in {objs['Venus'].sign}:</span> <span class="desc">"{generate_desc('Venus', objs['Venus'].sign)}"</span></div>
                </div>

                <div class="card blueprint">
                    <h3 style="color:#D4AF37;">🗝️ The Blueprint</h3>
                    <div class="item"><span class="label">🎭 Profile:</span> {hd['name']}</div>
                    <div class="item"><span class="label">🧬 Calling: <span class="highlight">{keys['lw']['name']}</span></span> <span class="desc">"{keys['lw']['story']}"</span></div>
                    <div class="item"><span class="label">🌍 Growth: <span class="highlight">{keys['evo']['name']}</span></span> <span class="desc">"{keys['evo']['story']}"</span></div>
                </div>

                <div class="card boardroom">
                    <h3 style="color:#4682B4;">The Boardroom</h3>
                    <div class="item"><span class="label">👔 CEO (Saturn in {objs['Saturn'].sign})</span> <span class="desc">"{generate_desc('Saturn', objs['Saturn'].sign)}"</span></div>
                    <div class="item"><span class="label">💰 Mogul (Jupiter in {objs['Jupiter'].sign})</span> <span class="desc">"{generate_desc('Jupiter', objs['Jupiter'].sign)}"</span></div>
                </div>

                <div class="card sanctuary">
                    <h3 style="color:#2E8B57;">The Sanctuary</h3>
                    <div class="item"><span class="label">🎨 Muse (Venus in {objs['Venus'].sign})</span> <span class="desc">"{generate_desc('Venus', objs['Venus'].sign)}"</span></div>
                    <div class="item"><span class="label">🌫️ Dreamer (Neptune in {objs['Neptune'].sign})</span> <span class="desc">"{generate_desc('Neptune', objs['Neptune'].sign)}"</span></div>
                </div>

                <div class="card streets">
                    <h3 style="color:#CD5C5C;">The Streets</h3>
                    <div class="item"><span class="label">🔥 Hustle (Mars in {objs['Mars'].sign})</span> <span class="desc">"{generate_desc('Mars', objs['Mars'].sign)}"</span></div>
                    <div class="item"><span class="label">⚡ Disruptor (Uranus in {objs['Uranus'].sign})</span> <span class="desc">"{generate_desc('Uranus', objs['Uranus'].sign)}"</span></div>
                    <div class="item"><span class="label">🕵️ Kingpin (Pluto in {objs['Pluto'].sign})</span> <span class="desc">"{generate_desc('Pluto', objs['Pluto'].sign)}"</span></div>
                </div>

                <div class="card vault">
                    <h3>🔒 The Vault</h3>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚡ Aura: <span class="highlight">{keys['rad']['name']}</span></span> <span class="vault-desc">"{keys['rad']['story']}"</span></div>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚓ Root: <span class="highlight">{keys['pur']['name']}</span></span> <span class="vault-desc">"{keys['pur']['story']}"</span></div>
                    <div class="item" style="border-bottom: none;"><span class="vault-label">🧲 Magnet: <span class="highlight">{keys['att']['name']}</span></span> <span class="vault-desc">"{keys['att']['story']}"</span></div>
                </div>

                <div class="card" style="background:#2c3e50; color:white; text-align:center; padding:30px;">
                    <h3 style="color:#f1c40f; margin-top:0;">⚡ Strategic Insight: {topic}</h3>
                    <p style="font-size:1.1em; line-height:1.8;">{advice}</p>
                </div>
                
                <button onclick="downloadPDF('{pdf_b64}')" class="btn">⬇️ DOWNLOAD PDF REPORT</button>
                
                <div class="end-marker">--- END OF GENERATED REPORT ---</div>
                <div style="text-align:center; font-size:10px; color:#ccc; margin-top:10px;">{data.city} | {safe_date} | TZ: {tz}</div>
                
                <div class="footer-guard"></div>
            </div>
        </body>
        </html>
        """
        return {"report": html}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"report": f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"}
