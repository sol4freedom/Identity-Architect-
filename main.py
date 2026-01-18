from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime
import traceback
import base64

# --- IMPORTS ---
from geopy.geocoders import Nominatim
# Lazy loading applied later for heavy libs to prevent timeouts
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- 1. BACKUP CITY DATABASE ---
CITY_DB = {
    "sao paulo": {"lat": -23.55, "lon": -46.63, "tz_std": -3.0, "hemisphere": "S"},
    "são paulo": {"lat": -23.55, "lon": -46.63, "tz_std": -3.0, "hemisphere": "S"},
    "fargo":     {"lat": 46.87,  "lon": -96.79, "tz_std": -6.0, "hemisphere": "N"},
    "minneapolis": {"lat": 44.97, "lon": -93.26, "tz_std": -6.0, "hemisphere": "N"},
    "ashland":   {"lat": 42.19,  "lon": -122.70, "tz_std": -8.0, "hemisphere": "N"},
    "new york":  {"lat": 40.71,  "lon": -74.00, "tz_std": -5.0, "hemisphere": "N"},
    "london":    {"lat": 51.50,  "lon": -0.12,  "tz_std": 0.0,  "hemisphere": "N"}
}

RAVE_ORDER = [25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36]

# --- ARCHETYPES ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness."}, 2: {"name": "The Receptive", "story": "The Divine Feminine blueprint."},
    3: {"name": "The Innovator", "story": "Chaos into Order."}, 4: {"name": "The Logic Master", "story": "The Answer to doubt."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness."}, 6: {"name": "The Peacemaker", "story": "Conflict into Peace."},
    7: {"name": "The Leader", "story": "Guidance by will."}, 8: {"name": "The Stylist", "story": "Mediocrity into Style."},
    9: {"name": "The Focuser", "story": "Power of the Small."}, 10: {"name": "The Self", "story": "The art of Being."},
    11: {"name": "The Idealist", "story": "Ideas into Light."}, 12: {"name": "The Articulate", "story": "Channeling the soul."},
    13: {"name": "The Listener", "story": "The Confidant of secrets."}, 14: {"name": "The Power House", "story": "Fueling dreams."},
    15: {"name": "The Humanist", "story": "Extremes into Flow."}, 16: {"name": "The Master", "story": "Skill into Magic."},
    17: {"name": "The Opinion", "story": "The logical Eye."}, 18: {"name": "The Improver", "story": "Healing the flaw."},
    19: {"name": "The Sensitive", "story": "Attunement to needs."}, 20: {"name": "The Now", "story": "Spontaneous clarity."},
    21: {"name": "The Controller", "story": "Authority and resources."}, 22: {"name": "The Grace", "story": "Emotional openness."},
    23: {"name": "The Assimilator", "story": "Simplicity from noise."}, 24: {"name": "The Rationalizer", "story": "Invention from the past."},
    25: {"name": "The Spirit", "story": "Universal Love."}, 26: {"name": "The Egoist", "story": "The Dealmaker."},
    27: {"name": "The Nurturer", "story": "Altruism and care."}, 28: {"name": "The Risk Taker", "story": "Immortality through purpose."},
    29: {"name": "The Yes Man", "story": "Commitment to experience."}, 30: {"name": "The Passion", "story": "The Fire of desire."},
    31: {"name": "The Voice", "story": "Influential leadership."}, 32: {"name": "The Conservative", "story": "Preserving value."},
    33: {"name": "The Reteller", "story": "Wisdom from retreat."}, 34: {"name": "The Power", "story": "Majesty of life."},
    35: {"name": "The Progress", "story": "Adventure and change."}, 36: {"name": "The Crisis", "story": "Compassion in the storm."},
    37: {"name": "The Family", "story": "Equality and friendship."}, 38: {"name": "The Fighter", "story": "Honor in the battle."},
    39: {"name": "The Provocateur", "story": "Liberation through friction."}, 40: {"name": "The Aloneness", "story": "Resolve and regeneration."},
    41: {"name": "The Fantasy", "story": "The Origin of the dream."}, 42: {"name": "The Finisher", "story": "Growth and conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough knowing."}, 44: {"name": "The Alert", "story": "Teamwork and smell."},
    45: {"name": "The Gatherer", "story": "Synergy of the Kingdom."}, 46: {"name": "The Determination", "story": "Serendipity in the body."},
    47: {"name": "The Realization", "story": "Transmutation of confusion."}, 48: {"name": "The Depth", "story": "Wisdom from the well."},
    49: {"name": "The Catalyst", "story": "Revolution of principles."}, 50: {"name": "The Values", "story": "Harmony and tribal law."},
    51: {"name": "The Shock", "story": "Initiation by thunder."}, 52: {"name": "The Stillness", "story": "The Mountain waiting."},
    53: {"name": "The Starter", "story": "Abundance. You are the pressure to begin something new."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward seeking success."},
    55: {"name": "The Spirit", "story": "Freedom in emotion."}, 56: {"name": "The Storyteller", "story": "Wandering through myths."},
    57: {"name": "The Intuitive", "story": "Clarity in the now."}, 58: {"name": "The Joy", "story": "Vitality. You challenge authority with the joy of improvement."},
    59: {"name": "The Sexual", "story": "Intimacy breaking barriers."}, 60: {"name": "The Limitation", "story": "Realism grounding magic."},
    61: {"name": "The Mystery", "story": "Sanctity of the unknown."}, 62: {"name": "The Detail", "story": "Precision of language."},
    63: {"name": "The Doubter", "story": "Truth through logic."}, 64: {"name": "The Confusion", "story": "Illumination of the mind."}
}
# --- END OF PART 1 (SAFETY BUMPER) ---
# --- PART 3 START (SAFE BUMPER) ---
# --- TIMEZONE ENGINE ---
def resolve_location(city_input, date_str, time_str):
    city_clean = city_input.lower().strip()
    found_backup = None
    for key in CITY_DB:
        if key in city_clean:
            found_backup = CITY_DB[key]
            break
    if found_backup:
        lat, lon, tz_std, hemi = found_backup['lat'], found_backup['lon'], found_backup['tz_std'], found_backup['hemisphere']
        if "T" in date_str: date_str = date_str.split("T")[0]
        month = int(date_str.split("-")[1])
        is_dst = False
        if hemi == "S":
            if month >= 10 or month <= 2: is_dst = True
        else:
            if 3 <= month <= 10: is_dst = True
        return lat, lon, tz_std + 1.0 if is_dst else tz_std, "Backup Table"

    try:
        from timezonefinder import TimezoneFinder
        geolocator = Nominatim(user_agent="ia_v46_fix", timeout=10)
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

        # Astrology
        dt = Datetime(safe_date.replace("-", "/"), data.time, tz)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO], hsys=const.HOUSES_PLACIDUS)
        
        objs = {k: chart.get(getattr(const, k.upper())) for k in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
        rising = chart.get(const.HOUSE1)

        # Design
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

        # PDF GENERATION
        pdf_b64 = create_pdf_b64(data, lp, hd, keys, objs, rising)

        # HTML REPORT
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
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
            .item:last-child {{ border-bottom: none; padding-bottom: 0; }}
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
            .end-marker {{ text-align: center; margin-top: 40px; color: #aaa; font-size: 11px; letter-spacing: 2px; }}
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

                <div class="card" style="text-align:center; font-style:italic;">
                    <p style="margin:0;"><strong>Current Struggle:</strong> {data.struggle}</p>
                    <p style="margin:10px 0 0 0;">To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</p>
                </div>
                
                <a href="data:application/pdf;base64,{pdf_b64}" download="Integrated_Self.pdf" class="btn">⬇️ DOWNLOAD PDF REPORT</a>
                
                <div class="end-marker">--- END OF GENERATED REPORT ---</div>
                <div style="text-align:center; font-size:10px; color:#ccc; margin-top:10px;">{data.city} | {safe_date} | TZ: {tz}</div>
            </div>
        </body>
        </html>
        """
        return {"report": html}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"report": f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"}
