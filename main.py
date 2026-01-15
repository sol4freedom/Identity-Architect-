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
    "Aries": {"Mercury": "Direct, rapid-fire communication.", "Saturn": "Self-reliant discipline.", "Jupiter": "Wealth via bold risks.", "Moon": "Safety in independence.", "Venus": "Passionate, spontaneous love.", "Neptune": "Dreams of heroism.", "Mars": "Explosive, head-first drive.", "Uranus": "Individualistic rebellion.", "Pluto": "Destroying barriers.", "Rising": "Undeniable courage."},
    "Taurus": {"Mercury": "Deliberate, methodical thinking.", "Saturn": "Building legacy through patience.", "Jupiter": "Compounding assets.", "Moon": "Safety in comfort.", "Venus": "Sensory love and touch.", "Neptune": "Dreams of abundance.", "Mars": "Unstoppable momentum.", "Uranus": "Revolutionizing values.", "Pluto": "Transformation of worth.", "Rising": "Calm reliability."},
    "Gemini": {"Mercury": "Brilliant, agile processing.", "Saturn": "Structuring the intellect.", "Jupiter": "Luck via networking.", "Moon": "Safety in conversation.", "Venus": "Mental love and wit.", "Neptune": "Telepathic connection.", "Mars": "Versatile, scattered drive.", "Uranus": "Disrupting narratives.", "Pluto": "Psychological reprogramming.", "Rising": "Youthful curiosity."},
    "Cancer": {"Mercury": "Intuitive, memory-based speech.", "Saturn": "Responsibility to the clan.", "Jupiter": "Wealth via real estate.", "Moon": "Safety in a shell.", "Venus": "Caretaking love.", "Neptune": "Dreams of the perfect home.", "Mars": "Defensive protection.", "Uranus": "Revolutionizing family.", "Pluto": "Ancestral healing.", "Rising": "Gentle, receptive aura."},
    "Leo": {"Mercury": "Dramatic storytelling.", "Saturn": "Disciplined creativity.", "Jupiter": "Luck via visibility.", "Moon": "Safety in appreciation.", "Venus": "Grand, performative romance.", "Neptune": "Dreams of fame.", "Mars": "Drive fueled by honor.", "Uranus": "Disrupting the ego.", "Pluto": "Rebirth of identity.", "Rising": "Warm charisma."},
    "Virgo": {"Mercury": "Precise, analytical logic.", "Saturn": "Mastery of craft.", "Jupiter": "Expansion via details.", "Moon": "Safety in routine.", "Venus": "Devoted, practical love.", "Neptune": "Perfect healing.", "Mars": "Efficient action.", "Uranus": "Revolutionizing work.", "Pluto": "Deep purification.", "Rising": "Modest and sharp."},
    "Libra": {"Mercury": "Diplomatic negotiation.", "Saturn": "Structuring contracts.", "Jupiter": "Wealth via partnerships.", "Moon": "Safety in harmony.", "Venus": "Aesthetic love.", "Neptune": "Dreams of the soulmate.", "Mars": "Strategic alliances.", "Uranus": "Disrupting norms.", "Pluto": "Transformation via mirroring.", "Rising": "Graceful intelligence."},
    "Scorpio": {"Mercury": "Detective mind.", "Saturn": "Mastery of self-control.", "Jupiter": "Power via research.", "Moon": "Safety in deep trust.", "Venus": "Soul-merging fusion.", "Neptune": "Dreams of mysteries.", "Mars": "Relentless will.", "Uranus": "Disrupting taboos.", "Pluto": "Total metamorphosis.", "Rising": "Magnetic intensity."},
    "Sagittarius": {"Mercury": "Broad-minded philosophy.", "Saturn": "Structuring belief.", "Jupiter": "Luck via travel.", "Moon": "Safety in freedom.", "Venus": "Adventurous love.", "Neptune": "Dreams of nirvana.", "Mars": "Crusading for a cause.", "Uranus": "Disrupting dogma.", "Pluto": "Death of old beliefs.", "Rising": "Jovial optimism."},
    "Capricorn": {"Mercury": "Pragmatic thinking.", "Saturn": "Building institutions.", "Jupiter": "Success via career.", "Moon": "Safety in control.", "Venus": "Serious commitment.", "Neptune": "Spiritual authority.", "Mars": "Disciplined drive.", "Uranus": "Disrupting government.", "Pluto": "Exposing corruption.", "Rising": "Authoritative capability."},
    "Aquarius": {"Mercury": "Genius innovation.", "Saturn": "Structuring the future.", "Jupiter": "Luck via networks.", "Moon": "Safety in detachment.", "Venus": "Unconventional love.", "Neptune": "Dreams of utopia.", "Mars": "Rebellious drive.", "Uranus": "Awakening the collective.", "Pluto": "Power to the people.", "Rising": "Unique brilliance."},
    "Pisces": {"Mercury": "Poetic thinking.", "Saturn": "Form to chaos.", "Jupiter": "Compassionate expansion.", "Moon": "Safety in solitude.", "Venus": "Spiritual love.", "Neptune": "Dissolving into oneness.", "Mars": "Fluid adaptability.", "Uranus": "Disrupting reality.", "Pluto": "Soul transformation.", "Rising": "Dreamy empathy."}
}

NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "Leading with independence."}, 2: {"name": "The Diplomat", "desc": "Thriving on partnership."},
    3: {"name": "The Creator", "desc": "Expressing joy and optimism."}, 4: {"name": "The Builder", "desc": "Building stability through work."},
    5: {"name": "The Adventurer", "desc": "Seeking freedom and change."}, 6: {"name": "The Nurturer", "desc": "Focusing on home and responsibility."},
    7: {"name": "The Seeker", "desc": "Searching for deep truth."}, 8: {"name": "The Powerhouse", "desc": "Mastering abundance and success."},
    9: {"name": "The Humanist", "desc": "Serving humanity."}, 11: {"name": "The Illuminator", "desc": "Channeling intuition."},
    22: {"name": "The Master Builder", "desc": "Turning dreams into reality."}, 33: {"name": "The Master Teacher", "desc": "Uplifting via compassion."}
}
# --- LOGIC ---
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

class UserInput(BaseModel):
    name: str; date: str; time: str; city: str; struggle: str
    tz: Union[float, int, str, None] = None
    @validator('tz', pre=True)
    def parse_tz(cls, v): return float(v) if v else 0
    @validator('date', pre=True)
    def clean_date(cls, v): return v.split("T")[0] if "T" in v else v
    @validator('time', pre=True)
    def clean_time(cls, v): return v.split(".")[0] if "." in v else v
# --- APP EXECUTION ---
@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        lat, lon, tz = 51.48, 0.0, data.tz
        # LOCATION FIXES
        if "sao paulo" in data.city.lower() or "são paulo" in data.city.lower(): 
            lat, lon, tz = -23.55, -46.63, -3.0
        elif "fargo" in data.city.lower(): 
            lat, lon, tz = 46.87, -96.79, -6.0 
        else:
            try:
                geo = Nominatim(user_agent="ia_v20", timeout=5).geocode(data.city)
                if geo: lat, lon = geo.latitude, geo.longitude
            except: pass

        # ASTROLOGY
        dt = Datetime(data.date.replace("-", "/"), data.time, tz)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO], hsys=const.HOUSES_PLACIDUS)
        
        objs = {k: chart.get(getattr(const, k.upper())) for k in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
        rising = chart.get(const.HOUSE1)

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

        # REPORT GENERATION
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');
            body {{ font-family: 'Lato', sans-serif; background: #fff; color: #2D2D2D; padding: 20px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .box {{ max-width: 700px; margin: 0 auto; background: #F9F9F9; padding: 40px; border-radius: 12px; border: 1px solid #ddd; }}
            h2, h3 {{ font-family: 'Cinzel', serif; color: #D4AF37; text-transform: uppercase; margin: 0 0 10px 0; }}
            .section {{ border-left: 3px solid #D4AF37; padding: 15px; margin-bottom: 25px; background: #fff; }}
            .vib {{ background: #E6E6FA; text-align: center; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #D8BFD8; }}
            .item {{ margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
            .item:last-child {{ border: none; }}
            .label {{ font-weight: bold; color: #333; display: block; }}
            .desc {{ font-size: 0.9em; color: #555; font-style: italic; }}
            .highlight {{ color: #C71585; font-weight: bold; }}
            
            /* VAULT FIX */
            .vault-section {{ background-color: #222 !important; color: #fff !important; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #D4AF37; }}
            .vault-section h3 {{ color: #FF4500 !important; margin-top: 0; }}
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
                    <h3 style="color:#483D8B;">{lp['number']}: {lp['name']}</h3>
                    <p style="font-size:14px; color:#555;">"{lp['desc']}"</p>
                </div>

                <div class="section">
                    <h3 style="color:#4A4A4A;">🗝️ The Core ID</h3>
                    <div class="item"><span class="label">🎭 Profile: <span style="color:#4A4A4A;">{hd['name']}</span></span></div>
                    <div class="item"><span class="label">🧬 Calling: <span class="highlight">{keys['lw']['name']}</span></span><span class="desc">"{keys['lw']['story']}"</span></div>
                    <div class="item"><span class="label">🌍 Growth: <span class="highlight">{keys['evo']['name']}</span></span><span class="desc">"{keys['evo']['story']}"</span></div>
                    <div class="item"><span class="label">🏹 Rising: {rising.sign}</span><span class="desc">"{generate_desc('Rising', rising.sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #4682B4;">
                    <h3 style="color:#4682B4;">The Boardroom</h3>
                    <div class="item"><span class="label">🤝 Broker: {objs['Mercury'].sign}</span><span class="desc">"{generate_desc('Mercury', objs['Mercury'].sign)}"</span></div>
                    <div class="item"><span class="label">👔 CEO: {objs['Saturn'].sign}</span><span class="desc">"{generate_desc('Saturn', objs['Saturn'].sign)}"</span></div>
                    <div class="item"><span class="label">💰 Mogul: {objs['Jupiter'].sign}</span><span class="desc">"{generate_desc('Jupiter', objs['Jupiter'].sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #2E8B57;">
                    <h3 style="color:#2E8B57;">The Sanctuary</h3>
                    <div class="item"><span class="label">❤️ Heart: {objs['Moon'].sign}</span><span class="desc">"{generate_desc('Moon', objs['Moon'].sign)}"</span></div>
                    <div class="item"><span class="label">🎨 Muse: {objs['Venus'].sign}</span><span class="desc">"{generate_desc('Venus', objs['Venus'].sign)}"</span></div>
                    <div class="item"><span class="label">🌫️ Dreamer: {objs['Neptune'].sign}</span><span class="desc">"{generate_desc('Neptune', objs['Neptune'].sign)}"</span></div>
                </div>

                <div class="section" style="border-color: #CD5C5C;">
                    <h3 style="color:#CD5C5C;">The Streets</h3>
                    <div class="item"><span class="label">🔥 Hustle: {objs['Mars'].sign}</span><span class="desc">"{generate_desc('Mars', objs['Mars'].sign)}"</span></div>
                    <div class="item"><span class="label">⚡ Disruptor: {objs['Uranus'].sign}</span><span class="desc">"{generate_desc('Uranus', objs['Uranus'].sign)}"</span></div>
                    <div class="item"><span class="label">🕵️ Kingpin: {objs['Pluto'].sign}</span><span class="desc">"{generate_desc('Pluto', objs['Pluto'].sign)}"</span></div>
                </div>

                <div class="vault-section">
                    <h3>🔒 The Vault</h3>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚡ Aura: <span class="vault-highlight">{keys['rad']['name']}</span></span><span class="vault-desc">"{keys['rad']['story']}"</span></div>
                    <div class="item" style="border-bottom: 1px solid #444;"><span class="vault-label">⚓ Root: <span class="vault-highlight">{keys['pur']['name']}</span></span><span class="vault-desc">"{keys['pur']['story']}"</span></div>
                    <div class="item" style="border-bottom: none;"><span class="vault-label">🧲 Magnet: <span class="vault-highlight">{keys['att']['name']}</span></span><span class="vault-desc">"{keys['att']['story']}"</span></div>
                </div>

                <div style="background-color: #F0F4F8; padding: 15px; border-radius: 8px; text-align: center; color: #555;">
                    <p><strong>Current Struggle:</strong> {data.struggle}</p>
                    <p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</em></p>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button onclick="window.print()" style="background-color: #D4AF37; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: bold; font-family: 'Cinzel', serif;">
                        📥 SAVE MY CODE
                    </button>
                </div>
            </div>
        </body>
        </html>
        """
        return {"report": html}
    except Exception as e:
        return {"report": f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"}
