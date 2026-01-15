from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime 
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- 1. CITY DATABASE (Add new cities here) ---
# Format: "city name": {"lat": latitude, "lon": longitude, "tz_std": standard_timezone, "hemisphere": "S" or "N"}
CITY_DB = {
    "sao paulo": {"lat": -23.55, "lon": -46.63, "tz_std": -3.0, "hemisphere": "S"},
    "são paulo": {"lat": -23.55, "lon": -46.63, "tz_std": -3.0, "hemisphere": "S"},
    "fargo":     {"lat": 46.87,  "lon": -96.79, "tz_std": -6.0, "hemisphere": "N"},
    "ashland":   {"lat": 42.19,  "lon": -122.70, "tz_std": -8.0, "hemisphere": "N"},
    "new york":  {"lat": 40.71,  "lon": -74.00, "tz_std": -5.0, "hemisphere": "N"},
    "london":    {"lat": 51.50,  "lon": -0.12,  "tz_std": 0.0,  "hemisphere": "N"}
}

# --- 2. DATA LIBRARIES ---
RAVE_ORDER = [25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36]

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
    53: {"name": "The Starter", "story": "Abundance of beginnings."}, 54: {"name": "The Ambition", "story": "Ascension and drive."},
    55: {"name": "The Spirit", "story": "Freedom in emotion."}, 56: {"name": "The Storyteller", "story": "Wandering through myths."},
    57: {"name": "The Intuitive", "story": "Clarity in the now."}, 58: {"name": "The Joy", "story": "Vitality against authority."},
    59: {"name": "The Sexual", "story": "Intimacy breaking barriers."}, 60: {"name": "The Limitation", "story": "Realism grounding magic."},
    61: {"name": "The Mystery", "story": "Sanctity of the unknown."}, 62: {"name": "The Detail", "story": "Precision of language."},
    63: {"name": "The Doubter", "story": "Truth through logic."}, 64: {"name": "The Confusion", "story": "Illumination of the mind."}
}

MEGA_MATRIX = {
    "Aries": {"Mercury": "Direct, rapid-fire communication.", "Saturn": "Self-reliant discipline and initiative.", "Jupiter": "Wealth via bold risks and pioneering.", "Moon": "Safety in independence and action.", "Venus": "Passionate, spontaneous love.", "Neptune": "Dreams of being the hero.", "Mars": "Explosive, head-first drive.", "Uranus": "Disrupts via individualistic rebellion.", "Pluto": "Asserting self to destroy barriers.", "Rising": "Undeniable courage and energy."},
    "Taurus": {"Mercury": "Deliberate, methodical thinking.", "Saturn": "Building legacy through patience.", "Jupiter": "Compounding assets and steady growth.", "Moon": "Safety in comfort and stability.", "Venus": "Sensory love, touch, and loyalty.", "Neptune": "Dreams of material abundance.", "Mars": "Unstoppable, rhythmic momentum.", "Uranus": "Revolutionizing values and resources.", "Pluto": "Transformation of self-worth.", "Rising": "Calm, grounded reliability."},
    "Gemini": {"Mercury": "Brilliant, agile processing.", "Saturn": "Structuring the intellect.", "Jupiter": "Luck via networking and curiosity.", "Moon": "Safety in conversation.", "Venus": "Mental love, wit, and banter.", "Neptune": "Dreams of telepathic connection.", "Mars": "Versatile, scattered drive.", "Uranus": "Disrupts the narrative.", "Pluto": "Psychological reprogramming.", "Rising": "Youthful, curious engagement."},
    "Cancer": {"Mercury": "Intuitive, memory-based speech.", "Saturn": "Responsibility to the clan.", "Jupiter": "Wealth via real estate or care.", "Moon": "Safety in a protective shell.", "Venus": "Caretaking and emotional safety.", "Neptune": "Dreams of the perfect home.", "Mars": "Defensive, fierce protection.", "Uranus": "Revolutionizing the family unit.", "Pluto": "Ancestral healing.", "Rising": "Gentle, receptive aura."},
    "Leo": {"Mercury": "Dramatic, expressive storytelling.", "Saturn": "Disciplined creativity.", "Jupiter": "Luck via visibility and confidence.", "Moon": "Safety in being appreciated.", "Venus": "Grand, performative romance.", "Neptune": "Dreams of artistic fame.", "Mars": "Drive fueled by honor and pride.", "Uranus": "Disrupts the ego.", "Pluto": "Death and rebirth of the identity.", "Rising": "Warm, charismatic presence."},
    "Virgo": {"Mercury": "Precise, analytical logic.", "Saturn": "Mastery of craft and service.", "Jupiter": "Expansion via refining details.", "Moon": "Safety in routine and order.", "Venus": "Devoted, practical love.", "Neptune": "Dreams of perfect healing.", "Mars": "Efficient, calculated action.", "Uranus": "Revolutionizing work and health.", "Pluto": "Deep purification.", "Rising": "Modest, sharp, put-together."},
    "Libra": {"Mercury": "Diplomatic, balanced negotiation.", "Saturn": "Structuring fair contracts.", "Jupiter": "Wealth via partnerships.", "Moon": "Safety in harmony and pairing.", "Venus": "Aesthetic, harmonious love.", "Neptune": "Dreams of the soulmate.", "Mars": "Strategic, social alliances.", "Uranus": "Disrupts relationship norms.", "Pluto": "Transformation via mirroring.", "Rising": "Graceful, social intelligence."},
    "Scorpio": {"Mercury": "Detective mind, seeking secrets.", "Saturn": "Mastery of self-control.", "Jupiter": "Expansion via research or hidden power.", "Moon": "Safety in deep, absolute trust.", "Venus": "Intense, soul-merging fusion.", "Neptune": "Dreams of the mysteries.", "Mars": "Relentless, sheer will.", "Uranus": "Disrupts taboos.", "Pluto": "Total metamorphosis.", "Rising": "Magnetic, intense mystery."},
    "Sagittarius": {"Mercury": "Broad-minded philosophy.", "Saturn": "Structuring a belief system.", "Jupiter": "Luck via travel and truth.", "Moon": "Safety in freedom and movement.", "Venus": "Adventurous, honest love.", "Neptune": "Dreams of nirvana.", "Mars": "Crusading for a cause.", "Uranus": "Disrupts dogma.", "Pluto": "Death of old beliefs.", "Rising": "Jovial, optimistic adventure."},
    "Capricorn": {"Mercury": "Pragmatic, executive thinking.", "Saturn": "Building enduring institutions.", "Jupiter": "Success via hierarchy and career.", "Moon": "Safety in control and achievement.", "Venus": "Committed, serious status.", "Neptune": "Dissolving structures for spirit.", "Mars": "Disciplined, long-game drive.", "Uranus": "Disrupts the government.", "Pluto": "Exposing systemic corruption.", "Rising": "Authoritative, capable maturity."},
    "Aquarius": {"Mercury": "Genius, non-linear innovation.", "Saturn": "Structuring the future.", "Jupiter": "Luck via networks and tech.", "Moon": "Safety in detachment.", "Venus": "Unconventional, free love.", "Neptune": "Dreams of utopia.", "Mars": "Rebellious, humanitarian drive.", "Uranus": "Awakening the collective.", "Pluto": "Power to the people.", "Rising": "Unique, aloof brilliance."},
    "Pisces": {"Mercury": "Poetic, symbolic thinking.", "Saturn": "Giving form to chaos.", "Jupiter": "Expansion via compassion.", "Moon": "Safety in solitude.", "Venus": "Unconditional, spiritual love.", "Neptune": "Dissolving into oneness.", "Mars": "Fluid, elusive adaptability.", "Uranus": "Disrupts reality itself.", "Pluto": "Transformation of the soul.", "Rising": "Dreamy, empathetic softness."}
}

NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "A self-starter leading with independence."}, 2: {"name": "The Diplomat", "desc": "A peacemaker thriving on partnership."},
    3: {"name": "The Creator", "desc": "Expressing joy and optimism."}, 4: {"name": "The Builder", "desc": "Building stability through work."},
    5: {"name": "The Adventurer", "desc": "Seeking freedom and change."}, 6: {"name": "The Nurturer", "desc": "Focusing on home and responsibility."},
    7: {"name": "The Seeker", "desc": "Searching for deep truth."}, 8: {"name": "The Powerhouse", "desc": "Mastering abundance and success."},
    9: {"name": "The Humanist", "desc": "Serving humanity."}, 11: {"name": "The Illuminator", "desc": "Channeling intuition."},
    22: {"name": "The Master Builder", "desc": "Turning dreams into reality."}, 33: {"name": "The Master Teacher", "desc": "Uplifting via compassion."}
}

# --- 3. LOGIC & HELPERS ---
def get_key_data(degree):
    if degree is None: return {"name": "Unknown", "story": ""}
    index = int(degree / 5.625)
    if index >= 64: index = 0
    key_number = RAVE_ORDER[index]
    return KEY_LORE.get(key_number, {"name": f"Key {key_number}", "story": ""})

def get_hd_profile(p_degree, d_degree):
    def get_line(deg): return int((deg % 5.625) / 0.9375) + 1
    key = f"{get_line(p_degree)}/{get_line(d_degree)}"
    return {"name": f"{key} Profile"}

def calculate_life_path(date_str):
    digits = [int(d) for d in date_str if d.isdigit()]
    total = sum(digits)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    data = NUMEROLOGY_LORE.get(total, {"name": "Mystery", "desc": ""})
    return {"number": total, "name": data["name"], "desc": data["desc"]}

def generate_desc(planet, sign):
    return MEGA_MATRIX.get(sign, {}).get(planet, f"Energy of {sign}")

def resolve_location(city_input, date_str):
    # Lookup city in DB
    city_clean = city_input.lower().strip()
    data = CITY_DB.get(city_clean)
    
    if not data:
        # Fallback to Geopy if not in DB
        try:
            geo = Nominatim(user_agent="ia_v22", timeout=5).geocode(city_input)
            if geo: return geo.latitude, geo.longitude, 0.0 # Default TZ 0 if unknown
        except: pass
        return 51.48, 0.0, 0.0 # Default London

    # Calculate DST Logic based on Month & Hemisphere
    lat, lon, tz_std, hemi = data['lat'], data['lon'], data['tz_std'], data['hemisphere']
    month = int(date_str.split("-")[1])
    
    is_dst = False
    if hemi == "S": # Southern Hemisphere (Summer is Oct-Feb)
        if month >= 10 or month <= 2: is_dst = True
    else: # Northern Hemisphere (Summer is Mar-Oct)
        if 3 <= month <= 10: is_dst = True
        
    final_tz = tz_std + 1.0 if is_dst else tz_std
    return lat, lon, final_tz

# --- 4. API ENDPOINT ---
class UserInput(BaseModel):
    name: str; date: str; time: str; city: str; struggle: str
    tz: Union[float, int, str, None] = None
    @validator('tz', pre=True)
    def parse_tz(cls, v): return float(v) if v else 0
    @validator('date', pre=True)
    def clean_date(cls, v): return v.split("T")[0] if "T" in v else v
    @validator('time', pre=True)
    def clean_time(cls, v): return v.split(".")[0] if "." in v else v

@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        # Resolve Location using new DB Logic
        lat, lon, tz = resolve_location(data.city, data.date)

        # Astrology Calc
        dt = Datetime(data.date.replace("-", "/"), data.time, tz)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO], hsys=const.HOUSES_PLACIDUS)
        
        objs = {k: chart.get(getattr(const, k.upper())) for k in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
        rising = chart.get(const.HOUSE1)

        # Design Calc
        d_dt = datetime.datetime.strptime(data.date, "%Y-%m-%d") - datetime.timedelta(days=88)
        d_chart = Chart(Datetime(d_dt.strftime("%Y/%m/%d"), data.time, tz), geo, IDs=[const.SUN, const.MOON])
        d_sun = d_chart.get(const.SUN); d_moon = d_chart.get(const.MOON)

        lp = calculate_life_path(data.date)
        hd = get_hd_profile(objs['Sun'].lon, d_sun.lon)
        keys = {
            'lw': get_key_data(objs['Sun'].lon), 'evo': get_key_data((objs['Sun'].lon + 180) % 360),
            'rad': get_key_data(d_sun.lon), 'pur': get_key_data((d_sun.lon + 180) % 360),
            'att': get_key_data(d_moon.lon)
        }

        # --- THE REPORT (WHITE/CLEAN THEME) ---
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
            body {{ font-family: 'Source Sans Pro', sans-serif; background: #fff; color: #2D2D2D; padding: 20px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .box {{ max-width: 700px; margin: 0 auto; background: #FFF; padding: 40px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }}
            h2 {{ font-family: 'Playfair Display', serif; color: #D4AF37; text-transform: uppercase; margin: 0 0 10px 0; font-size: 28px; }}
            h3 {{ font-family: 'Playfair Display', serif; font-size: 20px; margin: 0 0 10px 0; color: #333; }}
            .section {{ border-left: 4px solid #D4AF37; padding: 15px 0 15px 20px; margin-bottom: 30px; background: #fff; }}
            .vib {{ background: #F8F4FF; text-align: center; padding: 20px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #E6D8FF; }}
            .item {{ margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
            .item:last-child {{ border: none; }}
            .label {{ font-weight: bold; color: #333; display: block; }}
            .desc {{ font-size: 0.9em; color: #666; font-style: italic; }}
            .highlight {{ color: #C71585; font-weight: bold; }}
            
            /* VAULT FIX: Force White Text on Black Background */
            .vault-section {{ background-color: #111 !important; color: #fff !important; padding: 30px; border-radius: 12px; margin-bottom: 30px; border-left: 5px solid #D4AF37; }}
            .vault-section h3 {{ color: #FFD700 !important; margin-top: 0; }}
            .vault-label {{ color: #fff !important; font-weight: bold; display: block; }}
            .vault-desc {{ color: #ccc !important; font-size: 0.9em; font-style: italic; }}
            .vault-highlight {{ color: #FFD700 !important; }}

            @media print {{ button {{ display: none; }} }}
        </style>
        </head>
        <body>
            <div class="box">
                <div style="text-align:center; margin-bottom:30px; border-bottom:1px solid #D4AF37; padding-bottom:20px;">
                    <h2>The Integrated Self</h2>
                    <span style="font-size:12px; color:#888;">PREPARED FOR {data.name.upper()}</span>
                </div>

                <div class="vib">
                    <span style="font-size:10px; letter-spacing:2px; color:#666;">THE VIBRATION (LIFE PATH)</span>
                    <h3 style="color:#6A5ACD;">{lp['number']}: {lp['name']}</h3>
                    <p style="font-size:14px; color:#555;">"{lp['desc']}"</p>
                </div>

                <div class="section">
                    <h3>🗝️ The Core ID</h3>
                    <div class="item"><span class="label">🎭 Profile: <span style="color:#444;">{hd['name']}</span></span></div>
                    <div class="item"><span class="label">🧬 Calling: <span class="highlight">{keys['lw']['name']}</span></span><span class="desc">"{keys['lw']['story']}"</span></div>
                    <div class="item"><span class="label">🌍 Growth: <span class="highlight">{keys['evo']['name']}</span></span><span class="desc">"{keys['evo']['story']}"</span></div>
                    <div class="item"><span class="label">🏹 Rising: {rising.sign}</span><span class="desc">"{generate_desc('Rising', rising.sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #4682B4;">
                    <h3 style="color:#4682B4;">The Boardroom</h3>
                    <div class="item"><span class="label">🤝 Broker (Mercury in {objs['Mercury'].sign})</span><span class="desc">"{generate_desc('Mercury', objs['Mercury'].sign)}"</span></div>
                    <div class="item"><span class="label">👔 CEO (Saturn in {objs['Saturn'].sign})</span><span class="desc">"{generate_desc('Saturn', objs['Saturn'].sign)}"</span></div>
                    <div class="item"><span class="label">💰 Mogul (Jupiter in {objs['Jupiter'].sign})</span><span class="desc">"{generate_desc('Jupiter', objs['Jupiter'].sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #2E8B57;">
                    <h3 style="color:#2E8B57;">The Sanctuary</h3>
                    <div class="item"><span class="label">❤️ Heart (Moon in {objs['Moon'].sign})</span><span class="desc">"{generate_desc('Moon', objs['Moon'].sign)}"</span></div>
                    <div class="item"><span class="label">🎨 Muse (Venus in {objs['Venus'].sign})</span><span class="desc">"{generate_desc('Venus', objs['Venus'].sign)}"</span></div>
                    <div class="item"><span class="label">🌫️ Dreamer (Neptune in {objs['Neptune'].sign})</span><span class="desc">"{generate_desc('Neptune', objs['Neptune'].sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #CD5C5C;">
                    <h3 style="color:#CD5C5C;">The Streets</h3>
                    <div class="item"><span class="label">🔥 Hustle (Mars in {objs['Mars'].sign})</span><span class="desc">"{generate_desc('Mars', objs['Mars'].sign)}"</span></div>
                    <div class="item"><span class="label">⚡ Disruptor (Uranus in {objs['Uranus'].sign})</span><span class="desc">"{generate_desc('Uranus', objs['Uranus'].sign)}"</span></div>
                    <div class="item"><span class="label">🕵️ Kingpin (Pluto in {objs['Pluto'].sign})</span><span class="desc">"{generate_desc('Pluto', objs['Pluto'].sign)}"</span></div>
                </div>

                <div class="vault-section">
                    <h3>🔒 The Vault</h3>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚡ Aura: <span class="vault-highlight">{keys['rad']['name']}</span></span><span class="vault-desc">"{keys['rad']['story']}"</span></div>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚓ Root: <span class="vault-highlight">{keys['pur']['name']}</span></span><span class="vault-desc">"{keys['pur']['story']}"</span></div>
                    <div class="item" style="border-bottom: none;"><span class="vault-label">🧲 Magnet: <span class="vault-highlight">{keys['att']['name']}</span></span><span class="vault-desc">"{keys['att']['story']}"</span></div>
                </div>

                <div style="background-color: #F8F8F8; padding: 20px; border-radius: 8px; text-align: center; color: #666; margin-top: 30px;">
                    <p style="margin:0;"><strong>Current Struggle:</strong> {data.struggle}</p>
                    <p style="margin:5px 0 0 0; font-style:italic;">To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <button onclick="window.print()" style="background-color: #D4AF37; color: white; border: none; padding: 12px 24px; font-size: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; letter-spacing: 1px;">
                        📥 SAVE MY CODE
                    </button>
                </div>

                <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px; font-size: 10px; color: #999; text-align: center;">
                    Debug: {data.city} | {data.date} {data.time} | TZ: {tz} (Using Dictionary DB)
                </div>
            </div>
        </body>
        </html>
        """
        return {"report": html}
    except Exception as e:
        return {"report": f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"}
