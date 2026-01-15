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

# --- APP SETUP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GENE KEYS MAPPING ---
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

# --- THE 64 ARCHETYPES (KEY LORE) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Entropy into Freshness. You are the spark that initiates new cycles when the old ways go stale."},
    2: {"name": "The Receptive", "story": "The Divine Feminine. You are the architectural blueprint that guides raw energy into form."},
    3: {"name": "The Innovator", "story": "Chaos into Order. You are the mutant who changes the rules to push evolution forward."},
    4: {"name": "The Logic Master", "story": "The Answer. You resolve doubt by finding the perfect pattern and explaining it to the world."},
    5: {"name": "The Fixer", "story": "Patience into Timelessness. You wait for the right rhythm to align the world's habits."},
    6: {"name": "The Peacemaker", "story": "Conflict into Peace. You use diplomacy and emotional intelligence to dissolve friction."},
    7: {"name": "The Leader", "story": "Guidance. You do not force; you lead by representing the collective will of the people."},
    8: {"name": "The Stylist", "story": "Mediocrity into Style. You are the individualist who inspires others just by being yourself."},
    9: {"name": "The Focuser", "story": "The Power of the Small. You tame the chaotic mind by focusing on one critical detail at a time."},
    10: {"name": "The Self", "story": "Being. You are here to master the art of simply being yourself without apology."},
    11: {"name": "The Idealist", "story": "Ideas into Light. You catch the images from the darkness and bring them to the world."},
    12: {"name": "The Articulate", "story": "The Channel. You master your mood to speak words that touch the soul."},
    13: {"name": "The Listener", "story": "The Confidant. You hold the secrets of the past to guide the future."},
    14: {"name": "The Power House", "story": "The Generator. You possess the unflagging energy to fuel the dreams of the collective."},
    15: {"name": "The Humanist", "story": "Extremes into Flow. You accept all rhythms of humanity, from the dull to the wild."},
    16: {"name": "The Master", "story": "The Virtuoso. You practice with enthusiasm until your skill becomes magical versatility."},
    17: {"name": "The Opinion", "story": "The Eye. You see the pattern of the future and organize it into a logical view."},
    18: {"name": "The Improver", "story": "Correction. You spot the flaw in the system so that it can be healed and perfected."},
    19: {"name": "The Sensitive", "story": "Attunement. You feel the needs of the tribe before they are even spoken."},
    20: {"name": "The Now", "story": "Presence. You bypass the thinking mind to act with pure, spontaneous clarity."},
    21: {"name": "The Controller", "story": "Authority. You take control of the resources to ensure the tribe survives and thrives."},
    22: {"name": "The Grace", "story": "Emotional Grace. You allow others to feel deeply by listening with an open heart."},
    23: {"name": "The Assimilator", "story": "Simplicity. You strip away the noise to reveal the essential truth."},
    24: {"name": "The Rationalizer", "story": "Invention. You revisit the past over and over until you find a new way forward."},
    25: {"name": "The Spirit", "story": "Universal Love. You retain the innocence of the spirit despite the wounds of the world."},
    26: {"name": "The Egoist", "story": "The Dealmaker. You use your willpower and charisma to direct resources where they are needed."},
    27: {"name": "The Nurturer", "story": "Altruism. You care for the weak and ensure the heritage is passed down."},
    28: {"name": "The Risk Taker", "story": "Immortality. You confront the fear of death to find a life worth living."},
    29: {"name": "The Yes Man", "story": "Commitment. You say 'Yes' to the experience and persevere through the abyss."},
    30: {"name": "The Passion", "story": "The Fire. You burn with a desire that cannot be quenched, teaching the world to feel."},
    31: {"name": "The Voice", "story": "Influence. You speak the vision that the collective is waiting to hear."},
    32: {"name": "The Conservative", "story": "Veneration. You assess what is valuable from the past to preserve it for the future."},
    33: {"name": "The Reteller", "story": "Retreat. You withdraw to process the memory and return with wisdom."},
    34: {"name": "The Power", "story": "Majesty. You are the pure, independent force of life expressing itself."},
    35: {"name": "The Progress", "story": "Adventure. You are driven to taste every experience, knowing that change is the only constant."},
    36: {"name": "The Crisis", "story": "Compassion. You survive the emotional storm to bring light to the darkness."},
    37: {"name": "The Family", "story": "Equality. You build the community through friendship, bargains, and affection."},
    38: {"name": "The Fighter", "story": "Honor. You fight the battles that give life meaning and purpose."},
    39: {"name": "The Provocateur", "story": "Liberation. You poke the spirit of others to wake them up from their slumber."},
    40: {"name": "The Aloneness", "story": "Resolve. You separate yourself from the group to regenerate your power."},
    41: {"name": "The Fantasy", "story": "The Origin. You hold the seed of the dream that starts the entire cycle."},
    42: {"name": "The Finisher", "story": "Growth. You maximize the cycle and bring it to a satisfying conclusion."},
    43: {"name": "The Insight", "story": "Breakthrough. You hear the unique voice inside that changes the world's knowing."},
    44: {"name": "The Alert", "story": "Teamwork. You smell the potential in people and align them for success."},
    45: {"name": "The Gatherer", "story": "Synergy. You are the King/Queen who holds the resources together for the kingdom."},
    46: {"name": "The Determination", "story": "Serendipity. You succeed by being in the right place at the right time with your body."},
    47: {"name": "The Realization", "story": "Transmutation. You sort through the confusion of the past to find the epiphany."},
    48: {"name": "The Depth", "story": "Wisdom. You look into the deep well of talent to bring fresh solutions."},
    49: {"name": "The Catalyst", "story": "Revolution. You reject the old principles to establish a higher order."},
    50: {"name": "The Values", "story": "Harmony. You act as the guardian of the tribe's laws and values."},
    51: {"name": "The Shock", "story": "Initiation. You wake people up with thunder, forcing them to grow."},
    52: {"name": "The Stillness", "story": "The Mountain. You hold your energy still until the perfect moment to act."},
    53: {"name": "The Starter", "story": "Abundance. You are the pressure to begin something new and evolve."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward, seeking spiritual and material success."},
    55: {"name": "The Spirit", "story": "Freedom. You accept the highs and lows of emotion to find the spirit within."},
    56: {"name": "The Storyteller", "story": "Wandering. You travel through ideas and places to weave the collective myth."},
    57: {"name": "The Intuitive", "story": "Clarity. You hear the truth in the acoustic vibration of the now."},
    58: {"name": "The Joy", "story": "Vitality. You challenge authority with the joy of making life better."},
    59: {"name": "The Sexual", "story": "Intimacy. You break down barriers to create a union that produces life."},
    60: {"name": "The Limitation", "story": "Realism. You accept the boundaries of form to let the magic transcend them."},
    61: {"name": "The Mystery", "story": "Sanctity. You dive into the unknowable to bring back universal truth."},
    62: {"name": "The Detail", "story": "Precision. You name the details to build a bridge of understanding."},
    63: {"name": "The Doubter", "story": "Truth. You use critical logic to test the validity of the future."},
    64: {"name": "The Confusion", "story": "Illumination. You process the images of the mind until they resolve into light."}
}

def get_key_data(degree):
    if degree is None: return {"name": "Unknown", "story": ""}
    index = int(degree / 5.625)
    if index >= 64: index = 0
    key_number = RAVE_ORDER[index]
    data = KEY_LORE.get(key_number, {"name": f"Key {key_number}", "story": ""})
    return {"number": key_number, "name": data["name"], "story": data["story"]}

# --- NUMEROLOGY ENGINE ---
NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "You are a self-starter here to lead with independence and originality."},
    2: {"name": "The Diplomat", "desc": "You are a peacemaker who thrives on partnership and balance."},
    3: {"name": "The Creator", "desc": "You are an artist here to express joy, optimism, and communication."},
    4: {"name": "The Builder", "desc": "You are the foundation, here to build lasting stability through hard work."},
    5: {"name": "The Adventurer", "desc": "You are a free spirit here to experience change, freedom, and variety."},
    6: {"name": "The Nurturer", "desc": "You are the caretaker, focusing on responsibility, home, and healing."},
    7: {"name": "The Seeker", "desc": "You are the analyst, searching for deep spiritual and intellectual truth."},
    8: {"name": "The Powerhouse", "desc": "You are the executive, mastering abundance, authority, and success."},
    9: {"name": "The Humanist", "desc": "You are the compassionate soul, here to serve humanity and let go."},
    11: {"name": "The Illuminator", "desc": "A Master Number. You channel intuition to inspire others."},
    22: {"name": "The Master Builder", "desc": "A Master Number. You turn massive dreams into concrete reality."},
    33: {"name": "The Master Teacher", "desc": "A Master Number. You uplift humanity through selfless compassion."}
}

def calculate_life_path(date_str):
    digits = [int(d) for d in date_str if d.isdigit()]
    total = sum(digits)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    data = NUMEROLOGY_LORE.get(total, {"name": "The Mystery", "desc": "A unique vibration."})
    return {"number": total, "name": data["name"], "desc": data["desc"]}

# --- THE 4-LENS GRAMMAR ENGINE (NO DUPLICATES) ---

# 1. PLANET ACTIONS (The "Verb")
PLANET_ACTIONS = {
    "Mercury": "Negotiates deals using",
    "Saturn": "Builds legacy through",
    "Jupiter": "Expands wealth via",
    "Moon": "Finds emotional safety in",
    "Venus": "Seduces and attracts with",
    "Neptune": "Dreams of",
    "Mars": "Conquers obstacles with",
    "Uranus": "Disrupts the system using",
    "Pluto": "Transforms power through",
    "Rising": "Navigates the world with"
}

# 2. SIGN LENSES (The "Adjective")
# Each sign now has 4 unique descriptions based on what kind of planet is asking.
# Mental: Mercury, Uranus
# Emotional: Moon, Venus, Neptune
# Action: Mars, Pluto, Rising
# Material: Saturn, Jupiter

SIGN_LENSES = {
    "Aries": {
        "mental": "sharp, instinctive decision-making",
        "emotional": "passionate, direct honesty",
        "action": "explosive, trailblazing speed",
        "material": "bold, entrepreneurial risk-taking"
    },
    "Taurus": {
        "mental": "practical, methodical thought",
        "emotional": "deep loyalty and sensual touch",
        "action": "unstoppable, rhythmic momentum",
        "material": "compounding assets and solid foundations"
    },
    "Gemini": {
        "mental": "brilliant logic and rapid networking",
        "emotional": "playful wit and curiosity",
        "action": "agile, multitasking adaptability",
        "material": "diverse income streams and trade"
    },
    "Cancer": {
        "mental": "intuitive memory and gut instinct",
        "emotional": "deep, protective nurturing",
        "action": "tenacious, defensive maneuvering",
        "material": "secure resource accumulation"
    },
    "Leo": {
        "mental": "creative self-expression",
        "emotional": "warm-hearted, generous loyalty",
        "action": "undeniable presence and dominance",
        "material": "building a personal empire"
    },
    "Virgo": {
        "mental": "precise analysis and optimization",
        "emotional": "devoted acts of service",
        "action": "efficient, calculated movement",
        "material": "perfecting the details of the system"
    },
    "Libra": {
        "mental": "strategic diplomacy and mediation",
        "emotional": "romantic harmony and aesthetics",
        "action": "collaborative, balanced tactics",
        "material": "profitable partnerships"
    },
    "Scorpio": {
        "mental": "investigative depth and research",
        "emotional": "intense, soul-merging intimacy",
        "action": "ruthless, regenerative power",
        "material": "controlling shared resources"
    },
    "Sagittarius": {
        "mental": "philosophical truth-seeking",
        "emotional": "free-spirited, adventurous optimism",
        "action": "wild, limitless exploration",
        "material": "international expansion"
    },
    "Capricorn": {
        "mental": "strategic, long-term planning",
        "emotional": "reliable, traditional commitment",
        "action": "disciplined, relentless grind",
        "material": "climbing the hierarchy"
    },
    "Aquarius": {
        "mental": "genius innovation and future-tech",
        "emotional": "accepting, platonic friendship",
        "action": "radical rebellion against the norm",
        "material": "systems for the collective good"
    },
    "Pisces": {
        "mental": "poetic imagination and symbols",
        "emotional": "boundless, mystical empathy",
        "action": "fluid, elusive adaptability",
        "material": "manifesting dreams into reality"
    }
}

def generate_desc(planet_name, sign_name):
    # Determine which lens to use
    lens = "action" # default
    if planet_name in ["Mercury", "Uranus"]: lens = "mental"
    if planet_name in ["Moon", "Venus", "Neptune"]: lens = "emotional"
    if planet_name in ["Saturn", "Jupiter"]: lens = "material"
    
    action = PLANET_ACTIONS.get(planet_name, "Expresses energy via")
    # Get the specific lens description for the sign
    style = SIGN_LENSES.get(sign_name, {}).get(lens, "cosmic energy")
    
    return f"{action} {style}."

# --- INPUT DATA ---
class UserInput(BaseModel):
    name: str
    date: str
    time: str
    city: str
    struggle: str
    tz: Union[float, int, str, None] = None

    @validator('tz', pre=True)
    def parse_timezone(cls, v):
        if v is None: return 0
        try: return float(v)
        except: return 0

    @validator('date', pre=True)
    def clean_date(cls, v):
        if "T" in v: return v.split("T")[0]
        return v

    @validator('time', pre=True)
    def clean_time(cls, v):
        if "." in v: v = v.split(".")[0]
        parts = v.split(":")
        if len(parts) >= 2: return f"{parts[0]}:{parts[1]}"
        return v

@app.post("/calculate")
def generate_reading(data: UserInput):
    try:
        # 1. SMART LOCATION
        city_lower = data.city.lower()
        lat, lon, tz_offset = 51.48, 0.00, data.tz

        if "sao paulo" in city_lower or "são paulo" in city_lower:
            lat, lon, tz_offset = -23.55, -46.63, -3
        elif "fargo" in city_lower:
            lat, lon, tz_offset = 46.87, -96.79, -5
        else:
            try:
                geolocator = Nominatim(user_agent="identity_architect_sol_v11", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat, lon = location.latitude, location.longitude
            except: pass

        # 2. CALCULATE ASTROLOGY (Personality/Black)
        date_obj = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        
        chart = Chart(date_obj, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

        # Get Objects
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        mercury = chart.get(const.MERCURY)
        venus = chart.get(const.VENUS)
        mars = chart.get(const.MARS)
        jupiter = chart.get(const.JUPITER)
        saturn = chart.get(const.SATURN)
        uranus = chart.get(const.URANUS)
        neptune = chart.get(const.NEPTUNE)
        pluto = chart.get(const.PLUTO)
        rising = chart.get(const.HOUSE1)
        
        # 3. CALCULATE DESIGN (Unconscious/Red)
        p_date = datetime.datetime.strptime(data.date, "%Y-%m-%d")
        d_date_obj = p_date - datetime.timedelta(days=88)
        d_date_str = d_date_obj.strftime("%Y/%m/%d")
        
        design_date_flatlib = Datetime(d_date_str, data.time, tz_offset)
        design_chart = Chart(design_date_flatlib, pos, IDs=[const.SUN, const.MOON], hsys=const.HOUSES_PLACIDUS)
        
        d_sun = design_chart.get(const.SUN)
        d_moon = design_chart.get(const.MOON)
        
        # 4. CALCULATE LIFE PATH (NUMEROLOGY)
        life_path = calculate_life_path(data.date)
        
        # 5. GET RICH ARCHETYPE DATA
        lifes_work = get_key_data(sun.lon)
        evolution = get_key_data((sun.lon + 180) % 360)
        radiance = get_key_data(d_sun.lon)
        purpose = get_key_data((d_sun.lon + 180) % 360)
        attraction = get_key_data(d_moon.lon)

        # 6. GENERATE REPORT (Integrated)
        report_html = f"""
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #2D2D2D;">
            
            <div style="text-align: center; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #D4AF37; margin: 0; letter-spacing: 2px;">THE INTEGRATED SELF</h2>
                <span style="font-size: 14px; color: #888;">PREPARED FOR {data.name.upper()}</span>
            </div>
            
            <div style="background-color: #E6E6FA; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <span style="font-size: 12px; color: #666; letter-spacing: 1px;">THE VIBRATION (LIFE PATH)</span>
                <h3 style="color: #483D8B; margin: 5px 0;">{life_path['number']}: {life_path['name']}</h3>
                <p style="font-size: 13px; font-style: italic; color: #555; margin-bottom: 0;">"{life_path['desc']}"</p>
            </div>
            
            <div style="background-color: #F9F9F9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #4A4A4A; margin-top: 0;">🗝️ THE CORE ID</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">CONSCIOUS INTENT</span>
                
                <p style="margin-top:10px;"><strong>🧬 The Calling:</strong> <span style="color: #C71585; font-weight: bold;">{lifes_work['name']}</span></p>
                <p style="font-size: 13px; font-style: italic; color: #555; margin-top: -10px; margin-bottom: 15px;">"{lifes_work['story']}"</p>
                
                <p><strong>🌍 The Growth Edge:</strong> <span style="color: #C71585; font-weight: bold;">{evolution['name']}</span></p>
                <p style="font-size: 13px; font-style: italic; color: #555; margin-top: -10px; margin-bottom: 15px;">"{evolution['story']}"</p>
                
                <p><strong>🏹 The Path (Rising):</strong> {rising.sign}</p>
                <p style="font-size: 13px; font-style: italic; color: #555; margin-top: -10px;">"{generate_desc('Rising', rising.sign)}"</p>
            </div>

            <div style="border-left: 5px solid #2C3E50; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #2C3E50; margin: 0;">THE BOARDROOM</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">STRATEGY & GROWTH</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li style="margin-bottom: 8px;">
                        🤝 <strong>The Broker:</strong> {mercury.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Mercury', mercury.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        👔 <strong>The CEO:</strong> {saturn.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Saturn', saturn.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        💰 <strong>The Mogul:</strong> {jupiter.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Jupiter', jupiter.sign)}</em></span>
                    </li>
                </ul>
            </div>

            <div style="border-left: 5px solid #27AE60; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #27AE60; margin: 0;">THE SANCTUARY</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">CONNECTION & CARE</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li style="margin-bottom: 8px;">
                        ❤️ <strong>The Heart:</strong> {moon.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Moon', moon.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        🎨 <strong>The Muse:</strong> {venus.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Venus', venus.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        🌫️ <strong>The Dreamer:</strong> {neptune.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Neptune', neptune.sign)}</em></span>
                    </li>
                </ul>
            </div>

            <div style="border-left: 5px solid #C0392B; padding-left: 15px; margin-bottom: 20px;">
                <h3 style="color: #C0392B; margin: 0;">THE STREETS</h3>
                <span style="font-size: 12px; color: #777; letter-spacing: 1px;">POWER & DRIVE</span>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    <li style="margin-bottom: 8px;">
                        🔥 <strong>The Hustle:</strong> {mars.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Mars', mars.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        ⚡ <strong>The Disruptor:</strong> {uranus.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Uranus', uranus.sign)}</em></span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        🕵️ <strong>The Kingpin:</strong> {pluto.sign}<br>
                        <span style="font-size:12px; color:#666;"><em>{generate_desc('Pluto', pluto.sign)}</em></span>
                    </li>
                </ul>
            </div>
            
            <div style="background-color: #222; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #FF4500; margin-top: 0;">🔒 THE VAULT</h3>
                <span style="font-size: 12px; color: #aaa; letter-spacing: 1px;">UNCONSCIOUS BLUEPRINT</span>
                
                <p style="margin-top:10px;"><strong>⚡ The Aura:</strong> <span style="color: #FFD700; font-weight: bold;">{radiance['name']}</span></p>
                <p style="font-size: 13px; font-style: italic; color: #ccc; margin-top: -10px; margin-bottom: 15px;">"{radiance['story']}"</p>
                
                <p><strong>⚓ The Root:</strong> <span style="color: #FFD700; font-weight: bold;">{purpose['name']}</span></p>
                <p style="font-size: 13px; font-style: italic; color: #ccc; margin-top: -10px; margin-bottom: 15px;">"{purpose['story']}"</p>
                
                <p><strong>🧲 The Magnet:</strong> <span style="color: #FFD700; font-weight: bold;">{attraction['name']}</span></p>
                <p style="font-size: 13px; font-style: italic; color: #ccc; margin-top: -10px;">"{attraction['story']}"</p>
            </div>

            <div style="background-color: #F0F4F8; padding: 15px; border-radius: 8px; font-size: 14px; text-align: center; color: #555;">
                <p><strong>Current Struggle:</strong> {data.struggle}</p>
                <p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</em></p>
            </div>
        </div>
        """

        return {"report": report_html}

    except Exception as e:
        return {"report": f"<p style='color:red'>Calculation Error: {str(e)}</p>"}
