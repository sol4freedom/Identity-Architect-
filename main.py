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

# --- HUMAN DESIGN PROFILE ENGINE ---
def get_hd_profile(p_degree, d_degree):
    def get_line(deg):
        gate_progress = deg % 5.625
        line_num = int(gate_progress / 0.9375) + 1
        return line_num

    p_line = get_line(p_degree)
    d_line = get_line(d_degree)
    
    profiles = {
        "1/3": "Investigator/Martyr", "1/4": "Investigator/Opportunist",
        "2/4": "Hermit/Opportunist", "2/5": "Hermit/Heretic",
        "3/5": "Martyr/Heretic", "3/6": "Martyr/Role Model",
        "4/6": "Opportunist/Role Model", "4/1": "Opportunist/Investigator",
        "5/1": "Heretic/Investigator", "5/2": "Heretic/Hermit",
        "6/2": "Role Model/Hermit", "6/3": "Role Model/Martyr"
    }
    
    key = f"{p_line}/{d_line}"
    name = profiles.get(key, f"{key} Profile")
    return {"key": key, "name": name}

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

# --- THE MEGA-MATRIX (ZERO DUPLICATES) ---
PLANET_ACTIONS = {
    "Mercury": "Negotiates deals using",
    "Saturn": "Builds legacy through",
    "Jupiter": "Expands wealth via",
    "Moon": "Finds safety in",
    "Venus": "Seduces and attracts with",
    "Neptune": "Dreams of",
    "Mars": "Conquers obstacles with",
    "Uranus": "Disrupts the system using",
    "Pluto": "Transforms power through",
    "Rising": "Navigates the world with"
}

MEGA_MATRIX = {
    "Aries": {
        "Mercury": "Direct, rapid-fire communication that gets straight to the point.",
        "Saturn": "Self-reliant discipline; you build structures by taking solo initiative.",
        "Jupiter": "Wealth comes through bold risks and pioneering new markets.",
        "Moon": "Emotional safety is found in independence and quick action.",
        "Venus": "Love is a chase; you value passion, courage, and spontaneity.",
        "Neptune": "Dreams of being the hero; spirituality is found in the spark of life.",
        "Mars": "Explosive drive; you conquer obstacles with raw, head-first speed.",
        "Uranus": "Disrupts through sudden, individualistic rebellion.",
        "Pluto": "Transformation happens through asserting the self and destroying barriers.",
        "Rising": "You enter the room with undeniable courage and energy."
    },
    "Taurus": {
        "Mercury": "Deliberate, methodical thinking that focuses on practical value.",
        "Saturn": "Building legacy through unshakeable patience and resource management.",
        "Jupiter": "Expansion comes from compounding assets and slow, steady growth.",
        "Moon": "Emotional safety is found in comfort, food, and stability.",
        "Venus": "Love is sensory; you value loyalty, touch, and beauty.",
        "Neptune": "Dreams of material abundance and earthly paradise.",
        "Mars": "Drive is like a steamroller; slow to start, but unstoppable once moving.",
        "Uranus": "Disrupts the economy and values; revolutionizing how we view resources.",
        "Pluto": "Deep transformation of self-worth and attachment to the material.",
        "Rising": "You project an aura of calm, grounded reliability."
    },
    "Gemini": {
        "Mercury": "Brilliant, agile processing; you connect dots faster than anyone else.",
        "Saturn": "Structuring the intellect; mastering the details of communication.",
        "Jupiter": "Luck comes from networking, teaching, and endless curiosity.",
        "Moon": "Emotional safety is found in conversation and understanding.",
        "Venus": "Love is mental; you value wit, banter, and variety.",
        "Neptune": "Dreams of a world connected by ideas and telepathy.",
        "Mars": "Drive is scattered but versatile; you fight with words.",
        "Uranus": "Disrupts the narrative; revolutionizing information flow.",
        "Pluto": "Transformation of the mind; deep psychological reprogramming.",
        "Rising": "You appear youthful, curious, and ready to engage."
    },
    "Cancer": {
        "Mercury": "Intuitive communication; you speak from memory and feeling.",
        "Saturn": "Building emotional resilience; responsibility to the family/clan.",
        "Jupiter": "Wealth comes through real estate, hospitality, or nurturing others.",
        "Moon": "Emotional safety is the priority; you need a shell to retreat into.",
        "Venus": "Love is caretaking; you value emotional safety and history.",
        "Neptune": "Dreams of the perfect home and universal mothering.",
        "Mars": "Drive is defensive; you fight fiercely to protect what is yours.",
        "Uranus": "Disrupts the home life; revolutionizing the definition of family.",
        "Pluto": "Deep ancestral healing and transformation of the emotional roots.",
        "Rising": "You project a gentle, protective, and receptive aura."
    },
    "Leo": {
        "Mercury": "Expressive, dramatic storytelling; you speak to entertain and lead.",
        "Saturn": "Disciplined creativity; you build a personal brand or empire.",
        "Jupiter": "Luck comes from confidence, visibility, and generosity.",
        "Moon": "Emotional safety is found in appreciation and being seen.",
        "Venus": "Love is a performance; you value romance, loyalty, and grand gestures.",
        "Neptune": "Dreams of glamour, artistic fame, and shining light.",
        "Mars": "Drive is fueled by pride; you fight for honor and recognition.",
        "Uranus": "Disrupts the ego; revolutionizing creative expression.",
        "Pluto": "Transformation of the heart; death and rebirth of the ego.",
        "Rising": "You enter the room with warmth, charisma, and presence."
    },
    "Virgo": {
        "Mercury": "Precise, analytical logic; you see the flaw in every system.",
        "Saturn": "Mastery of craft; you build through service and perfectionism.",
        "Jupiter": "Expansion comes from refining details and improving health.",
        "Moon": "Emotional safety is found in routine, order, and usefulness.",
        "Venus": "Love is helpful; you value cleanliness, devotion, and practical support.",
        "Neptune": "Dreams of healing and perfect order.",
        "Mars": "Drive is efficient; you achieve goals through calculated steps.",
        "Uranus": "Disrupts the workflow; revolutionizing work and health.",
        "Pluto": "Deep purification; transformation through service and analysis.",
        "Rising": "You appear modest, sharp, and put-together."
    },
    "Libra": {
        "Mercury": "Diplomatic negotiation; you weigh every side before speaking.",
        "Saturn": "Structuring relationships; building lasting, fair contracts.",
        "Jupiter": "Wealth comes through partnerships, law, or design.",
        "Moon": "Emotional safety is found in harmony and having a partner.",
        "Venus": "Love is an art form; you value aesthetics, balance, and peace.",
        "Neptune": "Dreams of the perfect soulmate and universal harmony.",
        "Mars": "Drive is strategic; you fight using social alliances and charm.",
        "Uranus": "Disrupts relationships; revolutionizing how we relate.",
        "Pluto": "Transformation through intense mirroring in relationships.",
        "Rising": "You project grace, charm, and social intelligence."
    },
    "Scorpio": {
        "Mercury": "Detective mind; you investigate the secrets others hide.",
        "Saturn": "Disciplined self-control; mastery over shared resources/debt.",
        "Jupiter": "Expansion comes from research, psychology, or investments.",
        "Moon": "Emotional safety requires deep, absolute trust and privacy.",
        "Venus": "Love is distinct fusion; you value loyalty and intensity.",
        "Neptune": "Dreams of merging souls and uncovering mysteries.",
        "Mars": "Drive is relentless; you conquer through sheer will and strategy.",
        "Uranus": "Disrupts the taboo; revolutionizing sex, death, and power.",
        "Pluto": "Total metamorphosis; burning down the old to birth the new.",
        "Rising": "You possess a magnetic, mysterious, and intense presence."
    },
    "Sagittarius": {
        "Mercury": "Broad-minded philosophy; you preach the big picture.",
        "Saturn": "Structuring the belief system; hard-won wisdom.",
        "Jupiter": "Luck comes from travel, publishing, and spiritual seeking.",
        "Moon": "Emotional safety is found in freedom and movement.",
        "Venus": "Love is an adventure; you value honesty and space.",
        "Neptune": "Dreams of nirvana and expanding consciousness.",
        "Mars": "Drive is crusading; you fight for a cause or belief.",
        "Uranus": "Disrupts dogma; revolutionizing education and religion.",
        "Pluto": "Transformation of truth; the death of old beliefs.",
        "Rising": "You appear jovial, optimistic, and ready for adventure."
    },
    "Capricorn": {
        "Mercury": "Pragmatic, executive thinking; focusing on the bottom line.",
        "Saturn": "The Master Builder; constructing enduring institutions.",
        "Jupiter": "Expansion comes from career success and hierarchy.",
        "Moon": "Emotional safety is found in control and achievement.",
        "Venus": "Love is serious; you value status, commitment, and longevity.",
        "Neptune": "Dreams of dissolving structures to find spiritual authority.",
        "Mars": "Drive is disciplined; you play the long game to win.",
        "Uranus": "Disrupts the government; revolutionizing corporate structures.",
        "Pluto": "Transformation of the system; exposure of corruption.",
        "Rising": "You project authority, maturity, and capability."
    },
    "Aquarius": {
        "Mercury": "Genius, non-linear logic; thinking generations ahead.",
        "Saturn": "Structuring the future; discipline in scientific pursuit.",
        "Jupiter": "Luck comes from networks, technology, and humanitarianism.",
        "Moon": "Emotional safety is found in detachment and friendship.",
        "Venus": "Love is unconventional; you value freedom and intellect.",
        "Neptune": "Dreams of utopia and the collective consciousness.",
        "Mars": "Drive is rebellious; you fight for the underdog.",
        "Uranus": "Disrupts everything; the awakener of the collective.",
        "Pluto": "Transformation of society; power to the people.",
        "Rising": "You appear unique, aloof, and intellectually brilliant."
    },
    "Pisces": {
        "Mercury": "Poetic, symbolic thinking; communicating via images.",
        "Saturn": "Structuring the spiritual; bringing form to chaos.",
        "Jupiter": "Expansion comes from compassion, art, and spirituality.",
        "Moon": "Emotional safety is found in solitude and merging with the divine.",
        "Venus": "Love is unconditional; you value soul connections.",
        "Neptune": "Dreams of dissolving into the ocean of oneness.",
        "Mars": "Drive is fluid; you move like water to get what you need.",
        "Uranus": "Disrupts reality; revolutionizing spirituality.",
        "Pluto": "Transformation of the soul; letting go of everything.",
        "Rising": "You project a dreamy, empathetic, and soft aura."
    }
}

def generate_desc(planet_name, sign_name):
    sign_data = MEGA_MATRIX.get(sign_name, {})
    return sign_data.get(planet_name, f"Expresses {sign_name} energy.")

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
                geolocator = Nominatim(user_agent="identity_architect_sol_v13", timeout=10)
                location = geolocator.geocode(data.city)
                if location:
                    lat, lon = location.latitude, location.longitude
            except: pass

        # 2. CALCULATE ASTROLOGY
        date_obj = Datetime(data.date.replace("-", "/"), data.time, tz_offset)
        pos = GeoPos(lat, lon)
        safe_objects = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
        chart = Chart(date_obj, pos, IDs=safe_objects, hsys=const.HOUSES_PLACIDUS)

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
        
        # 3. CALCULATE DESIGN
        p_date = datetime.datetime.strptime(data.date, "%Y-%m-%d")
        d_date_obj = p_date - datetime.timedelta(days=88)
        d_date_str = d_date_obj.strftime("%Y/%m/%d")
        design_date_flatlib = Datetime(d_date_str, data.time, tz_offset)
        design_chart = Chart(design_date_flatlib, pos, IDs=[const.SUN, const.MOON], hsys=const.HOUSES_PLACIDUS)
        d_sun = design_chart.get(const.SUN)
        d_moon = design_chart.get(const.MOON)
        
        # 4. CALCULATE LIFE PATH
        life_path = calculate_life_path(data.date)
        
        # 5. CALCULATE HD PROFILE
        hd_profile = get_hd_profile(sun.lon, d_sun.lon)
        
        # 6. GET ARCHETYPES
        lifes_work = get_key_data(sun.lon)
        evolution = get_key_data((sun.lon + 180) % 360)
        radiance = get_key_data(d_sun.lon)
        purpose = get_key_data((d_sun.lon + 180) % 360)
        attraction = get_key_data(d_moon.lon)

        # 7. GENERATE REPORT (HIGH END CSS)
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');
            
            :root {{
                --gold: #D4AF37;
                --gold-dim: #AA8C2C;
                --bg-dark: #121212;
                --card-bg: #1E1E1E;
                --text-main: #E0E0E0;
                --text-muted: #A0A0A0;
                --accent-boardroom: #4682B4;
                --accent-sanctuary: #2E8B57;
                --accent-streets: #CD5C5C;
            }}

            body {{
                font-family: 'Lato', sans-serif;
                background-color: var(--bg-dark);
                color: var(--text-main);
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}

            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: var(--card-bg);
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border: 1px solid #333;
            }}

            h1, h2, h3 {{
                font-family: 'Cinzel', serif;
                color: var(--gold);
                text-transform: uppercase;
                letter-spacing: 2px;
            }}

            .header {{
                text-align: center;
                border-bottom: 1px solid var(--gold-dim);
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}

            .vibration-box {{
                background: linear-gradient(135deg, #2c2c2c, #1a1a1a);
                border: 1px solid var(--gold-dim);
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                margin-bottom: 30px;
            }}

            .section-card {{
                background: rgba(255, 255, 255, 0.03);
                border-left: 4px solid var(--gold);
                padding: 20px;
                margin-bottom: 25px;
                border-radius: 0 8px 8px 0;
            }}

            .boardroom {{ border-left-color: var(--accent-boardroom); }}
            .sanctuary {{ border-left-color: var(--accent-sanctuary); }}
            .streets {{ border-left-color: var(--accent-streets); }}
            .vault {{ 
                background: #000; 
                border: 1px solid #333; 
                border-left: 4px solid var(--gold);
            }}

            .list-item {{
                margin-bottom: 15px;
                border-bottom: 1px solid #333;
                padding-bottom: 10px;
            }}
            
            .list-item:last-child {{ border-bottom: none; }}

            .planet-name {{
                font-weight: 700;
                color: #fff;
                display: block;
                margin-bottom: 4px;
            }}

            .planet-desc {{
                font-size: 0.95em;
                color: var(--text-muted);
                font-style: italic;
            }}

            .highlight {{ color: var(--gold); font-weight: bold; }}
            
            .struggle-box {{
                margin-top: 40px;
                padding: 20px;
                background: rgba(212, 175, 55, 0.1);
                border-radius: 8px;
                text-align: center;
                border: 1px solid var(--gold-dim);
            }}
        </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>The Integrated Self</h2>
                    <span style="font-size: 14px; color: var(--gold-dim);">PREPARED FOR {data.name.upper()}</span>
                </div>

                <div class="vibration-box">
                    <span style="font-size: 12px; color: var(--text-muted); letter-spacing: 2px;">THE VIBRATION (LIFE PATH)</span>
                    <h3 style="margin: 10px 0;">{life_path['number']}: {life_path['name']}</h3>
                    <p style="margin: 0; font-style: italic;">"{life_path['desc']}"</p>
                </div>

                <div class="section-card">
                    <h3>🗝️ The Core ID</h3>
                    <p class="list-item">
                        <span class="planet-name">🎭 Profile: <span class="highlight">{hd_profile['name']}</span></span>
                    </p>
                    <div class="list-item">
                        <span class="planet-name">🧬 The Calling: <span class="highlight">{lifes_work['name']}</span></span>
                        <span class="planet-desc">"{lifes_work['story']}"</span>
                    </div>
                    <div class="list-item">
                        <span class="planet-name">🌍 The Growth Edge: <span class="highlight">{evolution['name']}</span></span>
                        <span class="planet-desc">"{evolution['story']}"</span>
                    </div>
                    <div class="list-item">
                        <span class="planet-name">🏹 The Path (Rising): {rising.sign}</span>
                        <span class="planet-desc">"{generate_desc('Rising', rising.sign)}"</span>
                    </div>
                </div>

                <div class="section-card boardroom">
                    <h3 style="color: var(--accent-boardroom)">The Boardroom</h3>
                    <span style="font-size: 12px; color: var(--text-muted); letter-spacing: 1px;">STRATEGY & GROWTH</span>
                    <div style="margin-top: 15px;">
                        <div class="list-item">
                            <span class="planet-name">🤝 The Broker (Mercury in {mercury.sign})</span>
                            <span class="planet-desc">"{generate_desc('Mercury', mercury.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">👔 The CEO (Saturn in {saturn.sign})</span>
                            <span class="planet-desc">"{generate_desc('Saturn', saturn.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">💰 The Mogul (Jupiter in {jupiter.sign})</span>
                            <span class="planet-desc">"{generate_desc('Jupiter', jupiter.sign)}"</span>
                        </div>
                    </div>
                </div>

                <div class="section-card sanctuary">
                    <h3 style="color: var(--accent-sanctuary)">The Sanctuary</h3>
                    <span style="font-size: 12px; color: var(--text-muted); letter-spacing: 1px;">CONNECTION & CARE</span>
                    <div style="margin-top: 15px;">
                        <div class="list-item">
                            <span class="planet-name">❤️ The Heart (Moon in {moon.sign})</span>
                            <span class="planet-desc">"{generate_desc('Moon', moon.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">🎨 The Muse (Venus in {venus.sign})</span>
                            <span class="planet-desc">"{generate_desc('Venus', venus.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">🌫️ The Dreamer (Neptune in {neptune.sign})</span>
                            <span class="planet-desc">"{generate_desc('Neptune', neptune.sign)}"</span>
                        </div>
                    </div>
                </div>

                <div class="section-card streets">
                    <h3 style="color: var(--accent-streets)">The Streets</h3>
                    <span style="font-size: 12px; color: var(--text-muted); letter-spacing: 1px;">POWER & DRIVE</span>
                    <div style="margin-top: 15px;">
                        <div class="list-item">
                            <span class="planet-name">🔥 The Hustle (Mars in {mars.sign})</span>
                            <span class="planet-desc">"{generate_desc('Mars', mars.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">⚡ The Disruptor (Uranus in {uranus.sign})</span>
                            <span class="planet-desc">"{generate_desc('Uranus', uranus.sign)}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">🕵️ The Kingpin (Pluto in {pluto.sign})</span>
                            <span class="planet-desc">"{generate_desc('Pluto', pluto.sign)}"</span>
                        </div>
                    </div>
                </div>

                <div class="section-card vault">
                    <h3>🔒 The Vault</h3>
                    <span style="font-size: 12px; color: var(--text-muted); letter-spacing: 1px;">UNCONSCIOUS BLUEPRINT</span>
                    <div style="margin-top: 15px;">
                        <div class="list-item">
                            <span class="planet-name">⚡ The Aura: <span class="highlight">{radiance['name']}</span></span>
                            <span class="planet-desc">"{radiance['story']}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">⚓ The Root: <span class="highlight">{purpose['name']}</span></span>
                            <span class="planet-desc">"{purpose['story']}"</span>
                        </div>
                        <div class="list-item">
                            <span class="planet-name">🧲 The Magnet: <span class="highlight">{attraction['name']}</span></span>
                            <span class="planet-desc">"{attraction['story']}"</span>
                        </div>
                    </div>
                </div>

                <div class="struggle-box">
                    <p><strong>Current Struggle:</strong> {data.struggle}</p>
                    <p><em>To overcome this, lean into your <strong>{rising.sign} Rising</strong> energy: {generate_desc('Rising', rising.sign)}.</em></p>
                </div>
            </div>
        </body>
        </html>
        """

        return {"report": report_html}

    except Exception as e:
        return {"report": f"<p style='color:red'>Calculation Error: {str(e)}</p>"}
