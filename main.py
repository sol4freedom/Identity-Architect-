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

# --- GENE KEYS MAPPING ---
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

# --- ARCHETYPE LIBRARY ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness. You are the spark that initiates new cycles."},
    2: {"name": "The Receptive", "story": "The Divine Feminine. You are the architectural blueprint that guides raw energy."},
    3: {"name": "The Innovator", "story": "Chaos into Order. You are the mutant who changes the rules."},
    4: {"name": "The Logic Master", "story": "The Answer. You resolve doubt by finding the perfect pattern."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness. You wait for the right rhythm to align habits."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace. You use emotional intelligence to dissolve friction."},
    7: {"name": "The Leader", "story": "Guidance. You lead by representing the collective will."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style. You inspire others just by being yourself."},
    9: {"name": "The Focuser", "story": "The Power of the Small. You tame chaos by focusing on one detail at a time."},
    10: {"name": "The Self", "story": "Being. You master the art of simply being yourself without apology."},
    11: {"name": "The Idealist", "story": "Ideas into Light. You catch images from the darkness and bring them to the world."},
    12: {"name": "The Articulate", "story": "The Channel. You master your mood to speak words that touch the soul."},
    13: {"name": "The Listener", "story": "The Confidant. You hold the secrets of the past to guide the future."},
    14: {"name": "The Power House", "story": "The Generator. You possess the unflagging energy to fuel dreams."},
    15: {"name": "The Humanist", "story": "Extremes into Flow. You accept all rhythms of humanity."},
    16: {"name": "The Master", "story": "The Virtuoso. You practice with enthusiasm until skill becomes magic."},
    17: {"name": "The Opinion", "story": "The Eye. You see the pattern of the future and organize it logically."},
    18: {"name": "The Improver", "story": "Correction. You spot the flaw so it can be healed."},
    19: {"name": "The Sensitive", "story": "Attunement. You feel the needs of the tribe before they are spoken."},
    20: {"name": "The Now", "story": "Presence. You bypass the thinking mind to act with spontaneous clarity."},
    21: {"name": "The Controller", "story": "Authority. You control resources to ensure the tribe thrives."},
    22: {"name": "The Grace", "story": "Emotional Grace. You listen with an open heart."},
    23: {"name": "The Assimilator", "story": "Simplicity. You strip away the noise to reveal the essential truth."},
    24: {"name": "The Rationalizer", "story": "Invention. You revisit the past to find a new way forward."},
    25: {"name": "The Spirit", "story": "Universal Love. You retain innocence despite the wounds of the world."},
    26: {"name": "The Egoist", "story": "The Dealmaker. You use charisma to direct resources where needed."},
    27: {"name": "The Nurturer", "story": "Altruism. You care for the weak and ensure heritage is passed down."},
    28: {"name": "The Risk Taker", "story": "Immortality. You confront the fear of death to find a life worth living."},
    29: {"name": "The Yes Man", "story": "Commitment. You say 'Yes' to the experience and persevere."},
    30: {"name": "The Passion", "story": "The Fire. You burn with desire, teaching the world to feel."},
    31: {"name": "The Voice", "story": "Influence. You speak the vision the collective is waiting to hear."},
    32: {"name": "The Conservative", "story": "Veneration. You assess what is valuable from the past to preserve it."},
    33: {"name": "The Reteller", "story": "Retreat. You withdraw to process memory and return with wisdom."},
    34: {"name": "The Power", "story": "Majesty. You are the independent force of life expressing itself."},
    35: {"name": "The Progress", "story": "Adventure. You are driven to taste every experience."},
    36: {"name": "The Crisis", "story": "Compassion. You survive the emotional storm to bring light."},
    37: {"name": "The Family", "story": "Equality. You build community through friendship and affection."},
    38: {"name": "The Fighter", "story": "Honor. You fight the battles that give life meaning."},
    39: {"name": "The Provocateur", "story": "Liberation. You poke the spirit of others to wake them up."},
    40: {"name": "The Aloneness", "story": "Resolve. You separate yourself to regenerate your power."},
    41: {"name": "The Fantasy", "story": "The Origin. You hold the seed of the dream that starts the cycle."},
    42: {"name": "The Finisher", "story": "Growth. You maximize the cycle and bring it to a conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough. You hear the unique voice that changes knowing."},
    44: {"name": "The Alert", "story": "Teamwork. You smell potential and align people for success."},
    45: {"name": "The Gatherer", "story": "Synergy. You hold the resources together for the kingdom."},
    46: {"name": "The Determination", "story": "Serendipity. You succeed by being in the right place at the right time."},
    47: {"name": "The Realization", "story": "Transmutation. You sort through confusion to find the epiphany."},
    48: {"name": "The Depth", "story": "Wisdom. You look into the deep well to bring fresh solutions."},
    49: {"name": "The Catalyst", "story": "Revolution. You reject old principles to establish a higher order."},
    50: {"name": "The Values", "story": "Harmony. You act as the guardian of the tribe's values."},
    51: {"name": "The Shock", "story": "Initiation. You wake people up with thunder."},
    52: {"name": "The Stillness", "story": "The Mountain. You hold energy still until the perfect moment."},
    53: {"name": "The Starter", "story": "Abundance. You are the pressure to begin something new."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward seeking success."},
    55: {"name": "The Spirit", "story": "Freedom. You accept high and low emotions to find the spirit."},
    56: {"name": "The Storyteller", "story": "Wandering. You travel through ideas to weave the collective myth."},
    57: {"name": "The Intuitive", "story": "Clarity. You hear the truth in the vibration of the now."},
    58: {"name": "The Joy", "story": "Vitality. You challenge authority with the joy of improvement."},
    59: {"name": "The Sexual", "story": "Intimacy. You break down barriers to create union."},
    60: {"name": "The Limitation", "story": "Realism. You accept boundaries to let magic transcend them."},
    61: {"name": "The Mystery", "story": "Sanctity. You dive into the unknowable to bring back truth."},
    62: {"name": "The Detail", "story": "Precision. You name the details to build understanding."},
    63: {"name": "The Doubter", "story": "Truth. You use logic to test the validity of the future."},
    64: {"name": "The Confusion", "story": "Illumination. You process images until they resolve into light."}
}

# --- THE MEGA MATRIX ---
MEGA_MATRIX = {
    "Aries": {
        "Mercury": "Direct, rapid-fire communication.", 
        "Saturn": "Self-reliant discipline and initiative.", 
        "Jupiter": "Wealth via bold risks and pioneering.", 
        "Moon": "Safety in independence and action.", 
        "Venus": "Passionate, spontaneous love.", 
        "Neptune": "Dreams of being the hero.", 
        "Mars": "Explosive, head-first drive.", 
        "Uranus": "Disrupts via individualistic rebellion.", 
        "Pluto": "Asserting self to destroy barriers.", 
        "Rising": "Undeniable courage and energy."
    },
    "Taurus": {
        "Mercury": "Deliberate, methodical thinking.", 
        "Saturn": "Building legacy through patience.", 
        "Jupiter": "Compounding assets and steady growth.", 
        "Moon": "Safety in comfort and stability.", 
        "Venus": "Sensory love, touch, and loyalty.", 
        "Neptune": "Dreams of material abundance.", 
        "Mars": "Unstoppable, rhythmic momentum.", 
        "Uranus": "Revolutionizing values and resources.", 
        "Pluto": "Transformation of self-worth.", 
        "Rising": "Calm, grounded reliability."
    },
    "Gemini": {
        "Mercury": "Brilliant, agile processing.", 
        "Saturn": "Structuring the intellect.", 
        "Jupiter": "Luck via networking and curiosity.", 
        "Moon": "Safety in conversation.", 
        "Venus": "Mental love, wit, and banter.", 
        "Neptune": "Dreams of telepathic connection.", 
        "Mars": "Versatile, scattered drive.", 
        "Uranus": "Disrupts the narrative.", 
        "Pluto": "Psychological reprogramming.", 
        "Rising": "Youthful, curious engagement."
    },
    "Cancer": {
        "Mercury": "Intuitive, memory-based speech.", 
        "Saturn": "Responsibility to the clan.", 
        "Jupiter": "Wealth via real estate or care.", 
        "Moon": "Safety in a protective shell.", 
        "Venus": "Caretaking and emotional safety.", 
        "Neptune": "Dreams of the perfect home.", 
        "Mars": "Defensive, fierce protection.", 
        "Uranus": "Revolutionizing the family unit.", 
        "Pluto": "Ancestral healing.", 
        "Rising": "Gentle, receptive aura."
    },
    "Leo": {
        "Mercury": "Dramatic, expressive storytelling.", 
        "Saturn": "Disciplined creativity.", 
        "Jupiter": "Luck via visibility and confidence.", 
        "Moon": "Safety in being appreciated.", 
        "Venus": "Grand, performative romance.", 
        "Neptune": "Dreams of artistic fame.", 
        "Mars": "Drive fueled by honor and pride.", 
        "Uranus": "Disrupts the ego.", 
        "Pluto": "Death and rebirth of the identity.", 
        "Rising": "Warm, charismatic presence."
    },
    "Virgo": {
        "Mercury": "Precise, analytical logic.", 
        "Saturn": "Mastery of craft and service.", 
        "Jupiter": "Expansion via refining details.", 
        "Moon": "Safety in routine and order.", 
        "Venus": "Devoted, practical love.", 
        "Neptune": "Dreams of perfect healing.", 
        "Mars": "Efficient, calculated action.", 
        "Uranus": "Revolutionizing work and health.", 
        "Pluto": "Deep purification.", 
        "Rising": "Modest, sharp, put-together."
    },
    "Libra": {
        "Mercury": "Diplomatic, balanced negotiation.", 
        "Saturn": "Structuring fair contracts.", 
        "Jupiter": "Wealth via partnerships.", 
        "Moon": "Safety in harmony and pairing.", 
        "Venus": "Aesthetic, harmonious love.", 
        "Neptune": "Dreams of the soulmate.", 
        "Mars": "Strategic, social alliances.", 
        "Uranus": "Disrupts relationship norms.", 
        "Pluto": "Transformation via mirroring.", 
        "Rising": "Graceful, social intelligence."
    },
    "Scorpio": {
        "Mercury": "Detective mind, seeking secrets.", 
        "Saturn": "Mastery of self-control.", 
        "Jupiter": "Expansion via research or hidden power.", 
        "Moon": "Safety in deep, absolute trust.", 
        "Venus": "Intense, soul-merging fusion.", 
        "Neptune": "Dreams of the mysteries.", 
        "Mars": "Relentless, sheer will.", 
        "Uranus": "Disrupts taboos.", 
        "Pluto": "Total metamorphosis.", 
        "Rising": "Magnetic, intense mystery."
    },
    "Sagittarius": {
        "Mercury": "Broad-minded philosophy.", 
        "Saturn": "Structuring a belief system.", 
        "Jupiter": "Luck via travel and truth.", 
        "Moon": "Safety in freedom and movement.", 
        "Venus": "Adventurous, honest love.", 
        "Neptune": "Dreams of nirvana.", 
        "Mars": "Crusading for a cause.", 
        "Uranus": "Disrupts dogma.", 
        "Pluto": "Death of old beliefs.", 
        "Rising": "Jovial, optimistic adventure."
    },
    "Capricorn": {
        "Mercury": "Pragmatic, executive thinking.", 
        "Saturn": "Building enduring institutions.", 
        "Jupiter": "Success via hierarchy and career.", 
        "Moon": "Safety in control and achievement.", 
        "Venus": "Committed, serious status.", 
        "Neptune": "Dissolving structures for spirit.", 
        "Mars": "Disciplined, long-game drive.", 
        "Uranus": "Disrupts the government.", 
        "Pluto": "Exposing systemic corruption.", 
        "Rising": "Authoritative, capable maturity."
    },
    "Aquarius": {
        "Mercury": "Genius, non-linear innovation.", 
        "Saturn": "Structuring the future.", 
        "Jupiter": "Luck via networks and tech.", 
        "Moon": "Safety in detachment.", 
        "Venus": "Unconventional, free love.", 
        "Neptune": "Dreams of utopia.", 
        "Mars": "Rebellious, humanitarian drive.", 
        "Uranus": "Awakening the collective.", 
        "Pluto": "Power to the people.", 
        "Rising": "Unique, aloof brilliance."
    },
    "Pisces": {
        "Mercury": "Poetic, symbolic thinking.", 
        "Saturn": "Giving form to chaos.", 
        "Jupiter": "Expansion via compassion.", 
        "Moon": "Safety in solitude.", 
        "Venus": "Unconditional, spiritual love.", 
        "Neptune": "Dissolving into oneness.", 
        "Mars": "Fluid, elusive adaptability.", 
        "Uranus": "Disrupts reality itself.", 
        "Pluto": "Transformation of the soul.", 
        "Rising": "Dreamy, empathetic softness."
    }
}

NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "A self-starter leading with independence."},
    2: {"name": "The Diplomat", "desc": "A peacemaker thriving on partnership."},
    3: {"name": "The Creator", "desc": "An artist expressing joy and optimism."},
    4: {"name": "The Builder", "desc": "A foundation building stability through work."},
    5: {"name": "The Adventurer", "desc": "A free spirit seeking freedom and change."},
    6: {"name": "The Nurturer", "desc": "A caretaker focused on home and responsibility."},
    7: {"name": "The Seeker", "desc": "An analyst searching for deep spiritual truth."},
    8: {"name": "The Powerhouse", "desc": "An executive mastering abundance and success."},
    9: {"name": "The Humanist", "desc": "A compassionate soul serving humanity."},
    11: {"name": "The Illuminator", "desc": "A Master Number channeling intuition."},
    22: {"name": "The Master Builder", "desc": "Turning massive dreams into reality."},
    33: {"name": "The Master Teacher", "desc": "Uplifting humanity through compassion."}
}

Step 2: The Body (Logic & Report)
Paste this DIRECTLY BELOW Step 1.
# --- HELPER FUNCTIONS ---
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

# --- API ENDPOINT ---
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
        # --- BRAZIL SUMMER TIME FIX ---
        lat, lon, tz = 51.48, 0.0, data.tz
        
        if "sao paulo" in data.city.lower() or "são paulo" in data.city.lower(): 
            lat, lon = -23.55, -46.63
            # Check month for DST (Roughly Oct-Feb in Brazil 90s)
            month = int(data.date.split("-")[1])
            if month >= 10 or month <= 2:
                tz = -2.0 # Summer Time
            else:
                tz = -3.0 # Standard Time
        elif "fargo" in data.city.lower(): 
            lat, lon, tz = 46.87, -96.79, -6.0 
        else:
            try:
                geo = Nominatim(user_agent="ia_v18", timeout=5).geocode(data.city)
                if geo: lat, lon = geo.latitude, geo.longitude
            except: pass

        # CALCULATIONS
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
            'lw': get_key_data(objs['Sun'].lon),
            'evo': get_key_data((objs['Sun'].lon + 180) % 360),
            'rad': get_key_data(d_sun.lon),
            'pur': get_key_data((d_sun.lon + 180) % 360),
            'att': get_key_data(d_moon.lon)
        }

        # --- THE REPORT (WITH CSS FIXES) ---
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');
            :root {{ --gold: #D4AF37; --bg: #fff; --card: #F9F9F9; --text: #2D2D2D; }}
            body {{ 
                font-family: 'Lato', sans-serif; 
                background: var(--bg); 
                color: var(--text); 
                padding: 20px; 
                -webkit-print-color-adjust: exact; 
                print-color-adjust: exact;
            }}
            .box {{ max-width: 700px; margin: 0 auto; background: var(--card); padding: 40px; border-radius: 12px; border: 1px solid #ddd; }}
            h2, h3 {{ font-family: 'Cinzel', serif; color: var(--gold); text-transform: uppercase; margin: 0 0 10px 0; }}
            .section {{ border-left: 3px solid var(--gold); padding: 15px; margin-bottom: 25px; background: #fff; }}
            .vib {{ background: #E6E6FA; text-align: center; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #D8BFD8; }}
            .item {{ margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
            .item:last-child {{ border: none; }}
            .label {{ font-weight: bold; color: #333; display: block; }}
            .desc {{ font-size: 0.9em; color: #555; font-style: italic; }}
            .highlight {{ color: #C71585; font-weight: bold; }}
            
            /* THE VAULT VISIBILITY FIX */
            .vault-section {{
                background-color: #222 !important; 
                color: #fff !important; 
                padding: 20px; 
                border-radius: 8px; 
                margin-bottom: 20px;
                border-left: 4px solid var(--gold);
            }}
            .vault-section h3 {{ color: #FF4500 !important; margin-top: 0; }}
            .vault-label {{ color: #fff !important; font-weight: bold; display: block; }}
            .vault-desc {{ color: #ccc !important; font-size: 0.9em; font-style: italic; }}
            .vault-highlight {{ color: #FFD700 !important; }}

            @media print {{
                button {{ display: none; }}
                body {{ padding: 0; }}
                .box {{ border: none; }}
            }}
        </style>
        </head>
        <body>
            <div class="box">
                <div style="text-align:center; margin-bottom:30px; border-bottom:1px solid var(--gold); padding-bottom:20px;">
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
                    <div class="item">
                        <span class="label">🧬 Calling: <span class="highlight">{keys['lw']['name']}</span></span>
                        <span class="desc">"{keys['lw']['story']}"</span>
                    </div>
                    <div class="item">
                        <span class="label">🌍 Growth: <span class="highlight">{keys['evo']['name']}</span></span>
                        <span class="desc">"{keys['evo']['story']}"</span>
                    </div>
                    <div class="item">
                        <span class="label">🏹 Rising: {rising.sign}</span>
                        <span class="desc">"{generate_desc('Rising', rising.sign)}"</span>
                    </div>
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
                    <div class="item" style="border-bottom: 1px solid #444;">
                        <span class="vault-label">⚡ Aura: <span class="vault-highlight">{keys['rad']['name']}</span></span>
                        <span class="vault-desc">"{keys['rad']['story']}"</span>
                    </div>
                    <div class="item" style="border-bottom: 1px solid #444;">
                        <span class="vault-label">⚓ Root: <span class="vault-highlight">{keys['pur']['name']}</span></span>
                        <span class="vault-desc">"{keys['pur']['story']}"</span>
                    </div>
                    <div class="item" style="border-bottom: none;">
                        <span class="vault-label">🧲 Magnet: <span class="vault-highlight">{keys['att']['name']}</span></span>
                        <span class="vault-desc">"{keys['att']['story']}"</span>
                    </div>
                </div>

                <div style="background-color: #F0F4F8; padding: 15px; border-radius: 8px; font-size: 14px; text-align: center; color: #555;">
                    <p><strong>Current Struggle:</strong> {data.struggle}</p>
                    <p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</em></p>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button onclick="window.print()" style="background-color: #D4AF37; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: bold; font-family: 'Cinzel', serif;">
                        📥 SAVE MY CODE
                    </button>
                </div>

                <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px; font-size: 10px; color: #999; text-align: center;">
                    Debug: {data.city} | {data.date} {data.time} | TZ: {tz} (Sao Paulo DST Fix Applied)
                </div>
            </div>
        </body>
        </html>
        """
        return {"report": html}
    except Exception as e:
        return {"report": f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"}

