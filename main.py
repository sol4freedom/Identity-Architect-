import sys, base64, datetime, json, logging, re
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF
import pytz

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

# --- 1. DATA: LOCATIONS ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- 2. DATA: LIFE PATH (THE DESTINY) ---
LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone, conquer self-doubt, and lead the tribe into a new era.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master the invisible threads that connect people, teaching the world that power lies in cooperation.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world and remind humanity that life is meant to be celebrated.",
    4: "The Master Builder. You are the architect of the future. Your story is one of endurance and legacy. You are here to build a foundation so strong it supports generations.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability. You are here to break the chains of tradition and show the world what it looks like to be free.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility without breaking, nurturing the tribe until they can stand alone.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth to look past the veil of illusion and bring wisdom back to the valley.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money and influence. You use your resources to empower the collective.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go. You are here to heal the world, leading by the overwhelming power of compassion.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness, channeling insights that shock the world awake.",
    22: "The Master Architect. You are the bridge between heaven and earth. You possess the ability to turn impossible spiritual visions into concrete reality.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity through pure service."
}

# --- 3. DATA: STRUGGLE (THE DRAGON) ---
STRUGGLE_LORE = {
    "wealth": {
        "title": "The Quest for Abundance",
        "desc": "Your dragon is Scarcity. You feel blocked because you are fighting your own flow. Abundance is a frequency. Align with your Jupiter sign to stop chasing gold and become the magnet that attracts it."
    },
    "relationship": {
        "title": "The Quest for Connection",
        "desc": "Your dragon is Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement. When you stand in your true design, you magnetize your true tribe."
    },
    "purpose": {
        "title": "The Quest for Meaning",
        "desc": "Your dragon is The Void. You feel lost because you look for a destination, not a frequency. Your North Node defines your signal. Stop 'doing' and start 'being' - the path will form beneath you."
    },
    "health": {
        "title": "The Quest for Vitality",
        "desc": "Your dragon is Exhaustion. Your body is overheating from running wrong software. Your Saturn placement holds your boundaries. Surrender to your internal rhythm; rest is a sacred act of power."
    },
    "general": {
        "title": "The Quest for Alignment",
        "desc": "Your dragon is Confusion. You are a unique design in a standardized world. Your Rising Sign is your compass. Return to your core strategy; your internal navigation is the only authority you need."
    }
}

# --- 4. DATA: ORIENTATION (THE AVATAR) ---
LINE_LORE = {
    1: {"title": "The Investigator", "desc": "The Foundation Builder. Like a master detective, you act only when you understand the ground beneath your feet. Certainty is your superpower."},
    2: {"title": "The Natural", "desc": "The Reluctant Hero. You possess innate gifts you never studied for. You wait in your hermitage until the right call summons you to save the day."},
    3: {"title": "The Experimenter", "desc": "The Fearless Explorer. There are no mistakes, only discoveries. You are the scientist of life, finding what works by discovering what doesn't."},
    4: {"title": "The Networker", "desc": "The Tribal Weaver. Your power is connection. Your opportunities come not from strangers, but from the web of allies you nurture."},
    5: {"title": "The Fixer", "desc": "The General. Strangers project hopes onto you. You arrive, provide a practical solution to the crisis, and vanish before the projection breaks."},
    6: {"title": "The Role Model", "desc": "The Sage. You live three lives: the reckless youth, the observer on the roof, and the wise example of authenticity."}
}

# --- 5. DATA: SIGNS (THE STARS) ---
SIGN_LORE = {
    "Aries": "The Warrior. You are the spark that starts the fire. Driven by raw instinct and courage, you initiate the new cycle.",
    "Taurus": "The Builder. You are the earth. Patient, sensual, and unmovable, you build structures that last for generations.",
    "Gemini": "The Messenger. You are the wind. Your mind is a kaleidoscope, weaving stories and ideas that keep the world moving.",
    "Cancer": "The Protector. You are the tide. Deeply intuitive, you build the shell that protects the vulnerable heart of the tribe.",
    "Leo": "The Radiant. You are the sun. You don't just enter a room; you warm it. Your creativity reminds others of their own light.",
    "Virgo": "The Alchemist. You are the perfectionist. You see the flaw only because you love the potential. You refine the world into gold.",
    "Libra": "The Diplomat. You are the scales. You exist in the delicate balance between self and other, creating harmony.",
    "Scorpio": "The Sorcerer. You are the depths. Unafraid of the dark, you dive into mysteries to find the truth.",
    "Sagittarius": "The Philosopher. You are the arrow. Driven by hunger for truth, you expand the horizons of what is possible.",
    "Capricorn": "The Architect. You are the peak. Driven by legacy, you climb the hard path to build an empire that outlasts you.",
    "Aquarius": "The Revolutionary. You are the lightning. You see the future before it arrives, breaking structures to liberate the collective.",
    "Pisces": "The Mystic. You are the ocean. Dissolving boundaries, you dream the collective dream and touch the divine."
}

# --- 6. DATA: ARCHETYPES (THE SUPERPOWERS) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "The primal spark of creativity. You bring something out of nothingness."},
    2: {"name": "The Receptive", "story": "The cosmic womb. You guide raw chaos into beautiful form."},
    3: {"name": "The Innovator", "story": "The necessary chaos. You break rules so life can evolve."},
    4: {"name": "The Logic Master", "story": "The formula. You provide patterns that calm the anxiety of doubt."},
    5: {"name": "The Fixer", "story": "The rhythm. You teach the world that waiting is perfect timing."},
    6: {"name": "The Peacemaker", "story": "The diplomat. You use emotional intelligence to dissolve conflict."},
    7: {"name": "The Leader", "story": "The guide. You represent the collective hope, pointing toward the future."},
    8: {"name": "The Stylist", "story": "The rebel. You inspire others by having the courage to be authentically you."},
    9: {"name": "The Focuser", "story": "The detail. You see the one tiny thing that determines success or failure."},
    10: {"name": "The Self", "story": "The vessel. You master the hardest art of all: self-love and being."},
    11: {"name": "The Idealist", "story": "The light-catcher. You fill the collective mind with images of what could be."},
    12: {"name": "The Articulate", "story": "The voice. You channel words that can mutate the soul of the listener."},
    13: {"name": "The Listener", "story": "The vault. You hold the secrets of the past so the tribe can learn."},
    14: {"name": "The Power House", "story": "The fuel. You drive the dreams of the world into reality."},
    15: {"name": "The Humanist", "story": "The flow. You embrace all extremes of humanity, weaving them together."},
    16: {"name": "The Master", "story": "The virtuoso. You turn raw talent into effortless mastery through repetition."},
    17: {"name": "The Opinion", "story": "The eye. You organize chaos into a logical view of the future."},
    18: {"name": "The Improver", "story": "The critic. You see what is broken so that it can be perfected."},
    19: {"name": "The Sensitive", "story": "The barometer. You ensure everyone has food, warmth, and belonging."},
    20: {"name": "The Now", "story": "The breath. You operate with spontaneous clarity in the present moment."},
    21: {"name": "The Controller", "story": "The manager. You take the reins to ensure survival and success."},
    22: {"name": "The Grace", "story": "The open door. Your social grace allows emotional truth to enter."},
    23: {"name": "The Assimilator", "story": "The razor. You strip away complexity to reveal simple truth."},
    24: {"name": "The Rationalizer", "story": "The inventor. You revisit the past until the breakthrough arrives."},
    25: {"name": "The Spirit", "story": "The Shaman. You retain innocence and universal love despite wounds."},
    26: {"name": "The Egoist", "story": "The dealmaker. You direct resources exactly where they are needed."},
    27: {"name": "The Nurturer", "story": "The guardian. You protect the weak and preserve the heritage."},
    28: {"name": "The Risk Taker", "story": "The daredevil. You confront fear to find a life worth living."},
    29: {"name": "The Devoted", "story": "The commitment. You persevere through the abyss to find wisdom."},
    30: {"name": "The Passion", "story": "The fire. You teach the world what it means to feel deeply."},
    31: {"name": "The Voice", "story": "The elected. You speak the vision that moves the tribe forward."},
    32: {"name": "The Conservative", "story": "The root. You preserve what is valuable for enduring success."},
    33: {"name": "The Reteller", "story": "The historian. You turn raw experience into the wisdom of history."},
    34: {"name": "The Power", "story": "The giant. Pure life force expressing itself through activity."},
    35: {"name": "The Progress", "story": "The hunger. You ensure the human story never becomes stagnant."},
    36: {"name": "The Crisis", "story": "The survivor. You bring compassion to the emotional darkness."},
    37: {"name": "The Family", "story": "The glue. You hold the tribe together through friendship and affection."},
    38: {"name": "The Fighter", "story": "The warrior. You fight for individual honor against all odds."},
    39: {"name": "The Provocateur", "story": "The poker. You shake others awake to their emotional truth."},
    40: {"name": "The Aloneness", "story": "The wall builder. You separate to regenerate power and deliver deliverance."},
    41: {"name": "The Fantasy", "story": "The seed. You dream the fantasy that starts the new cycle."},
    42: {"name": "The Finisher", "story": "The closer. You bring cycles to a satisfying conclusion."},
    43: {"name": "The Insight", "story": "The voice within. You carry the breakthrough that changes the mind."},
    44: {"name": "The Alert", "story": "The instinct. You align resources to ensure success."},
    45: {"name": "The Gatherer", "story": "The monarch. You hold the tribe's resources together."},
    46: {"name": "The Determination", "story": "The vessel. You succeed by being in the right place at the right time."},
    47: {"name": "The Realization", "story": "The epiphany. You sort confusion to find the meaning."},
    48: {"name": "The Depth", "story": "The well. You bring deep solutions to surface problems."},
    49: {"name": "The Catalyst", "story": "The revolutionary. You reject unfair principles for a higher order."},
    50: {"name": "The Values", "story": "The custodian. You guard the values that keep the tribe alive."},
    51: {"name": "The Shock", "story": "The thunder. You shock people into spiritual initiation."},
    52: {"name": "The Stillness", "story": "The mountain. You hold energy in stillness until the right moment."},
    53: {"name": "The Starter", "story": "The pressure. You initiate evolution without knowing the end."},
    54: {"name": "The Ambition", "story": "The climber. You drive the tribe toward spiritual and material mastery."},
    55: {"name": "The Spirit", "story": "The cup. You find abundance in the highs and lows of emotion."},
    56: {"name": "The Storyteller", "story": "The wanderer. You weave the myth that teaches the tribe who they are."},
    57: {"name": "The Intuitive", "story": "The ear. You hear the truth in the now to ensure survival."},
    58: {"name": "The Joy", "story": "The vital. You challenge authority to make life better."},
    59: {"name": "The Sexual", "story": "The breaker. You penetrate barriers to create intimacy and life."},
    60: {"name": "The Limitation", "story": "The acceptance. You accept boundaries so magic can transcend them."},
    61: {"name": "The Mystery", "story": "The diver. You explore the unknowable to bring back truth."},
    62: {"name": "The Detail", "story": "The name. You build bridges of understanding through facts."},
    63: {"name": "The Doubter", "story": "The question. You doubt everything until the truth is proven."},
    64: {"name": "The Confusion", "story": "The resolver. You process chaos until it becomes illumination."}
}

# --- 7. LOGIC ENGINES ---

def clean_time(time_input):
    if not time_input: return "12:00"
    s = str(time_input).upper().strip()
    match = re.search(r'(\d{1,2}):(\d{2})', s)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        if "PM" in s and h < 12: h += 12
        if "AM" in s and h == 12: h = 0
        return f"{h:02d}:{m:02d}"
    return "12:00"

def get_gate_from_degree(degree):
    if degree is None: return 1
    if degree < 0 or degree >= 360: degree = degree % 360
    step = int(degree / 5.625)
    gate_map = {
        0: 25, 1: 17, 2: 21, 3: 51, 4: 42, 5: 3, 6: 27, 7: 24,
        8: 2, 9: 23, 10: 8, 11: 20, 12: 16, 13: 35, 14: 45, 15: 12,
        16: 15, 17: 52, 18: 39, 19: 53, 20: 62, 21: 56, 22: 31, 23: 33,
        24: 7, 25: 4, 26: 29, 27: 59, 28: 40, 29: 64, 30: 47, 31: 6,
        32: 46, 33: 18, 34: 48, 35: 57, 36: 32, 37: 50, 38: 28, 39: 44,
        40: 1, 41: 43, 42: 14, 43: 34, 44: 9, 45: 5, 46: 26, 47: 11,
        48: 10, 49: 58, 50: 38, 51: 54, 52: 61, 53: 60, 54: 41, 55: 19,
        56: 13, 57: 49, 58: 30, 59: 55, 60: 37, 61: 63, 62: 22, 63: 36
    }
    return gate_map.get(step, 1)

def safe_get_date(date_input):
    if not date_input: return None
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def resolve_location(city_name):
    city_lower = str(city_name).lower().strip()
    for key in CITY_DB:
        if key in city_lower: return CITY_DB[key]
    try:
        geolocator = Nominatim(user_agent="ia_final_fix_v22")
        loc = geolocator.geocode(city_name)
        if loc:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=loc.longitude, lat=loc.latitude) or "UTC"
            return loc.latitude, loc.longitude, tz
    except: pass
    return 51.50, -0.12, "Europe/London"

def get_tz_offset(date_str, time_str, tz_name):
    try:
        local = pytz.timezone(tz_name)
        dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        offset = local.utcoffset(dt).total_seconds() / 3600.0
        return offset
    except: return 0.0

def get_hd_data(degree):
    gate = get_gate_from_degree(degree)
    info = KEY_LORE.get(gate, {"name": f"Gate {gate}", "story": "Energy"})
    return {"gate": gate, "name": info["name"], "story": info["story"]}

def get_strategic_advice(struggle, chart):
    s = str(struggle).lower()
    category = "general"
    if any(x in s for x in ['money', 'career', 'job', 'wealth', 'finance']):
        category = "wealth"
    elif any(x in s for x in ['love', 'relationship', 'marriage', 'partner']):
        category = "relationship"
    elif any(x in s for x in ['purpose', 'direction', 'soul', 'path']):
        category = "purpose"
    elif any(x in s for x in ['health', 'body', 'energy', 'vitality']):
        category = "health"
    lore = STRUGGLE_LORE.get(category, STRUGGLE_LORE["general"])
    return lore["title"], lore["desc"]

def generate_hero_narrative(name, chart_data, orientation_title, lp, struggle_advice):
    # Retrieve all raw data
    sun_sign = chart_data['Sun']['Sign']
    sun_lore = SIGN_LORE.get(sun_sign, "The Hero")
    
    sun_gate_id = chart_data['Sun']['Gate']
    sun_gate_name = chart_data['Sun']['Name']
    sun_gate_story = KEY_LORE.get(sun_gate_id, {}).get("story", "")
    
    moon_sign = chart_data['Moon']['Sign']
    moon_lore = SIGN_LORE.get(moon_sign, "The Soul")
    
    ris_sign = chart_data['Rising']['Sign']
    ris_lore = SIGN_LORE.get(ris_sign, "The Mask")
    
    lp_lore = LIFE_PATH_LORE.get(lp, "A path of unique discovery.")
    
    dragon_name = struggle_advice[0].replace("The Quest for ", "")
    dragon_desc = struggle_advice[1]
    
    story = []
    
    # CHAPTER 1: THE ORIGIN (Sun & Rising)
    story.append(f"CHAPTER 1: THE ORIGIN\n\nLong ago, the universe conspired to create a unique frequency, and it named that frequency {name}. You were born under the blazing sun of {sun_sign}. {sun_lore} This is your core, your fuel, and your inevitable nature. It is the fire that burns within you, demanding expression.")
    
    story.append(f"But to protect this intense light, you donned a mask. To the world, you first appear as {ris_sign}. {ris_lore} This is your armor and your first impression, the vehicle you drive through the physical world. Your journey begins by reconciling these two: the inner fire of the {sun_sign} and the outer shield of the {ris_sign}.")
    
    # CHAPTER 2: THE HEART (Moon)
    story.append(f"CHAPTER 2: THE HEART\n\nBeneath the armor lies a secret engine: your Moon in {moon_sign}. While others see your actions, only you feel this pull. {moon_lore} This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. Ignoring this voice is what leads to exhaustion; honoring it is the secret to your endless regeneration.")
    
    # CHAPTER 3: THE PATH (Life Path)
    story.append(f"CHAPTER 3: THE PATH\n\nEvery hero needs a road to walk. Yours is the Path of the {lp}. {lp_lore} This is not a random walk; it is a destiny. The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, but the view from the top is the purpose you have been searching for.")
    
    # CHAPTER 4: THE WEAPON (Sun Archetype)
    story.append(f"CHAPTER 4: THE WEAPON\n\nTo aid you on this path, you were gifted a specific superpower. In the language of the Archetypes, you carry the energy of Archetype {sun_gate_id}: {sun_gate_name}. {sun_gate_story} This is not a skill you learned in school; it is a frequency you emit naturally. When you trust this power, doors open without force. When you doubt it, you meet resistance. It is the sword in your hand.")
    
    # CHAPTER 5: THE STRATEGY (Orientation)
    story.append(f"CHAPTER 5: THE STRATEGY\n\nBut power without control is dangerous. Your operating manual is defined by your Orientation: {orientation_title}. You are not designed to move like everyone else. Your specific strategy requires you to honor your nature - whether that is to wait in your hermitage, to experiment fearlessly, or to network with your tribe. Deviation from this strategy is the root of your frustration. Trust your style.")
    
    # CHAPTER 6: THE DRAGON (Struggle)
    story.append(f"CHAPTER 6: THE DRAGON\n\nEvery story has an antagonist. Yours takes the form of {dragon_name}. {dragon_desc} This struggle you feel is not a punishment. It is the friction necessary to sharpen your blade. The dragon guards the treasure. By facing your Shadow and applying your Archetype, you do not just slay the dragon; you integrate it, turning your greatest weakness into your greatest wisdom.")
    
    # OUTRO
    story.append(f"This is the Legend of {name}. The map is in your hands. The stars have done their part; the rest of the story is yours to write.")
    
    return "\n\n".join(story)

# --- CLEANER FUNCTION FOR PDF ---
def clean_text_for_pdf(text):
    if not text: return ""
    # Standardize fancy punctuation to Latin-1 safe characters
    replacements = {
        "—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Final safeguard: remove anything else strictly incompatible
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- PDF ENGINE ---
def create_pdf_b64(name, lp, lp_desc, orientation_title, orientation_body, hero_story, advice, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # TITLE
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 10, clean_text_for_pdf('THE LEGEND OF YOU'), 0, 1, 'C')
        pdf.set_font("Helvetica", 'I', 12)
        pdf.cell(0, 10, clean_text_for_pdf(f"The Epic of {name}"), 0, 1, 'C')
        pdf.ln(10)

        # THE STORY (Takes up the whole first section)
        pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 6, clean_text_for_pdf(hero_story))
        pdf.ln(10)
        
        # BLUEPRINT SECTION (Page Break if needed)
        pdf.add_page()
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, clean_text_for_pdf("Your Planetary Inventory"), 0, 1)
        pdf.set_font("Helvetica", '', 12)
        
        for k, v in chart.items():
            sign = v.get("Sign", "?")
            gate = v.get("Gate", "?")
            name_txt = v.get("Name", "")
            sign_txt = v.get("SignLore", "") # We use the short name now
            gate_story = v.get("Story", "")
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 8, clean_text_for_pdf(f"{k}: {sign} (Archetype {gate}) - {name_txt}"), 0, 1)
            
            pdf.set_font("Helvetica", '', 10)
            pdf.multi_cell(0, 5, clean_text_for_pdf(f"{gate_story}"))
            pdf.ln(3)
            
        pdf_bytes = pdf.output()
        return base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"PDF Error: {str(e)}")
        return ""

# --- 5. API ROUTES ---

@app.get("/")
def root():
    return {"status": "online", "message": "Identity Architect is Running."}

@app.post("/calculate")
async def calculate_chart(request: Request):
    data = {}
    try:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct: data = await request.json()
        else: data = dict(await request.form())
    except: pass
    
    name = data.get("name") or "Traveler"
    
    raw_date = data.get("dob") or data.get("date")
    dob = safe_get_date(raw_date)
    if not dob: dob = datetime.date.today().strftime("%Y-%m-%d")

    raw_time = data.get("tob") or data.get("time") or data.get("birth_time") or "12:00"
    tob = clean_time(raw_time)

    city = data.get("city") or "London"
    struggle = data.get("struggle") or "General"

    try:
        lat, lon, tz_name = resolve_location(city)
        tz_offset = get_tz_offset(dob, tob, tz_name)
        
        # Calc Personality
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        chart_p = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        # Calc Design
        design_date_obj = datetime.datetime.strptime(dob, "%Y-%m-%d") - datetime.timedelta(days=88)
        design_dob = design_date_obj.strftime("%Y/%m/%d")
        dt_design = Datetime(design_dob, tob, tz_offset)
        chart_d = Chart(dt_design, geo_obj, IDs=[const.SUN], hsys=const.HOUSES_PLACIDUS)

        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        # Lines
        p_sun = chart_p.get(const.SUN)
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1
        d_sun = chart_d.get(const.SUN)
        d_line = (int(d_sun.lon / 0.9375) % 6) + 1

        p_info = LINE_LORE.get(p_line, {"title": str(p_line), "desc": ""})
        d_info = LINE_LORE.get(d_line, {"title": str(d_line), "desc": ""})
        orientation_title = f"{p_info['title']} / {d_info['title']}"
        orientation_body = f"<b>{p_info['title']}:</b> {p_info['desc']}<br><br><b>{d_info['title']}:</b> {d_info['desc']}"

        for p in planets:
            obj = chart_p.get(getattr(const, p.upper()))
            info = get_hd_data(obj.lon)
            sign_lore = SIGN_LORE.get(obj.sign, "Energy")
            chart_data[p] = {
                "Sign": obj.sign, 
                "SignLore": sign_lore,
                "Gate": info['gate'], 
                "Name": info['name'], 
                "Story": info['story']
            }
            
        asc = chart_p.get(const.ASC)
        asc_info = get_hd_data(asc.lon)
        asc_sign_lore = SIGN_LORE.get(asc.sign, "Energy")
        chart_data["Rising"] = {
            "Sign": asc.sign, 
            "SignLore": asc_sign_lore,
            "Gate": asc_info['gate'], 
            "Name": asc_info['name'], 
            "Story": asc_info['story']
        }
        
        try:
            digits = [int(d) for d in dob if d.isdigit()]
            total = sum(digits)
            while total > 9 and total not in [11, 22, 33]:
                total = sum(int(d) for d in str(total))
            lp = total
        except: lp = 0
        
        lp_desc = LIFE_PATH_LORE.get(lp, "A path of unique discovery.")
        
        topic, advice_text = get_strategic_advice(struggle, chart_data)
        hero_story = generate_hero_narrative(name, chart_data, orientation_title, lp, (topic, advice_text))
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1, "Name": "Error", "Story": ""}}
        orientation_title = "Unknown"
        orientation_body = ""
        lp = 0
        lp_desc = "Unknown"
        hero_story = "The mists of time obscure your legend. Please try again."
        topic, advice_text = ("Unknown", "Unknown")

    pdf_b64 = create_pdf_b64(name, lp, lp_desc, orientation_title, orientation_body, hero_story, (topic, advice_text), chart_data)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
        body {{ font-family: 'Source Sans Pro', sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
        .card {{ background: #fff; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h2 {{ font-family: 'Playfair Display', serif; color: #D4AF37; margin-top: 0; }}
        .story-text {{ white-space: pre-wrap; font-size: 1.05em; color: #444; }}
        .btn {{ 
            background-color: #D4AF37; color: white; border: none; padding: 15px 30px; 
            font-size: 16px; border-radius: 50px; cursor: pointer; display: block; 
            width: 100%; max-width: 300px; margin: 20px auto; text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-decoration: none;
        }}
    </style>
    </head>
    <body>
        <div class="card">
            <h2 style="text-align:center;">The Legend of {name}</h2>
            <div class="story-text">{hero_story}</div>
        </div>

        <a href="data:application/pdf;base64,{pdf_b64}" download="The_Legend_of_You.pdf" target="_blank" class="btn">
            ⬇️ DOWNLOAD FULL LEGEND (PDF)
        </a>
    </body>
    </html>
    """
    return {"report": html}
