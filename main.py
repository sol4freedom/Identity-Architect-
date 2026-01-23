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
        "desc": "Scarcity. You feel blocked because you are fighting your own flow. Abundance is a frequency. Align with your Jupiter sign to stop chasing gold and become the magnet that attracts it."
    },
    "relationship": {
        "title": "The Quest for Connection",
        "desc": "Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement. When you stand in your true design, you magnetize your true tribe."
    },
    "purpose": {
        "title": "The Quest for Meaning",
        "desc": "The Void. You feel lost because you look for a destination, not a frequency. Your North Node defines your signal. Stop 'doing' and start 'being'—the path will form beneath you."
    },
    "health": {
        "title": "The Quest for Vitality",
        "desc": "Exhaustion. Your body is overheating from running wrong software. Your Saturn placement holds your boundaries. Surrender to your internal rhythm; rest is a sacred act of power."
    },
    "general": {
        "title": "The Quest for Alignment",
        "desc": "Confusion. You are a unique design in a standardized world. Your Rising Sign is your compass. Return to your core strategy; your internal navigation is the only authority you need."
    }
}

# --- 4. DATA: ORIENTATION (THE AVATAR) ---
LINE_LORE = {
    1: {"title": "The Investigator", "desc": "The Foundation Builder. Like a master detective, you act only when you understand the ground beneath you. Certainty is your superpower."},
    2: {"title": "The Natural", "desc": "The Reluctant Hero. You possess innate gifts you never studied for. You wait in your hermitage until the right call summons you to save the day."},
    3: {"title": "The Experimenter", "desc": "The Fearless Explorer. There are no mistakes, only discoveries. You are the scientist of life, finding what works by discovering what doesn't."},
    4: {"title": "The Networker", "desc": "The Tribal Weaver. Your power is connection. Your opportunities come not from strangers, but from the web of allies you nurture."},
    5: {"title": "The Fixer", "desc": "The General. Strangers project hopes onto you. You arrive, provide a practical solution to the crisis, and vanish before the projection breaks."},
    6: {"title": "The Role Model", "desc": "The Sage. You live three lives: the reckless youth, the observer on the roof, and the wise example of authenticity."}
}

# --- 5. DATA: SIGNS (THE STARS) ---
SIGN_LORE = {
    "Aries": "The Warrior",
    "Taurus": "The Builder",
    "Gemini": "The Messenger",
    "Cancer": "The Protector",
    "Leo": "The Radiant",
    "Virgo": "The Alchemist",
    "Libra": "The Diplomat",
    "Scorpio": "The Sorcerer",
    "Sagittarius": "The Philosopher",
    "Capricorn": "The Architect",
    "Aquarius": "The Revolutionary",
    "Pisces": "The Mystic"
}

# --- 6. DATA: ARCHETYPES (THE SUPERPOWERS) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "The primal spark of creativity."},
    2: {"name": "The Receptive", "story": "The cosmic womb."},
    3: {"name": "The Innovator", "story": "The necessary chaos."},
    4: {"name": "The Logic Master", "story": "The answer to doubt."},
    5: {"name": "The Fixer", "story": "The power of waiting."},
    6: {"name": "The Peacemaker", "story": "The emotional diplomat."},
    7: {"name": "The Leader", "story": "The guide of the collective."},
    8: {"name": "The Stylist", "story": "The rebel of expression."},
    9: {"name": "The Focuser", "story": "The power of detail."},
    10: {"name": "The Self", "story": "The art of being."},
    11: {"name": "The Idealist", "story": "The light-catcher."},
    12: {"name": "The Articulate", "story": "The voice that mutates."},
    13: {"name": "The Listener", "story": "The keeper of secrets."},
    14: {"name": "The Power House", "story": "The fuel for dreams."},
    15: {"name": "The Humanist", "story": "The embrace of extremes."},
    16: {"name": "The Master", "story": "The virtuoso of skill."},
    17: {"name": "The Opinion", "story": "The eye of the future."},
    18: {"name": "The Improver", "story": "The healer of flaws."},
    19: {"name": "The Sensitive", "story": "The barometer of needs."},
    20: {"name": "The Now", "story": "The clarity of the present."},
    21: {"name": "The Controller", "story": "The manager of resources."},
    22: {"name": "The Grace", "story": "The open door."},
    23: {"name": "The Assimilator", "story": "The remover of obstacles."},
    24: {"name": "The Rationalizer", "story": "The inventor from the past."},
    25: {"name": "The Spirit", "story": "The innocent shaman."},
    26: {"name": "The Egoist", "story": "The great influencer."},
    27: {"name": "The Nurturer", "story": "The guardian of the tribe."},
    28: {"name": "The Risk Taker", "story": "The confronter of death."},
    29: {"name": "The Devoted", "story": "The commitment to the deep."},
    30: {"name": "The Passion", "story": "The fire of feeling."},
    31: {"name": "The Voice", "story": "The leader of the vision."},
    32: {"name": "The Conservative", "story": "The root of success."},
    33: {"name": "The Reteller", "story": "The wisdom of retreat."},
    34: {"name": "The Power", "story": "The independent giant."},
    35: {"name": "The Progress", "story": "The hunger for change."},
    36: {"name": "The Crisis", "story": "The light in the dark."},
    37: {"name": "The Family", "story": "The glue of friendship."},
    38: {"name": "The Fighter", "story": "The warrior for honor."},
    39: {"name": "The Provocateur", "story": "The awakener of spirit."},
    40: {"name": "The Aloneness", "story": "The deliverer."},
    41: {"name": "The Fantasy", "story": "The seed of the dream."},
    42: {"name": "The Finisher", "story": "The closing of the book."},
    43: {"name": "The Insight", "story": "The breakthrough voice."},
    44: {"name": "The Alert", "story": "The instinct for success."},
    45: {"name": "The Gatherer", "story": "The monarch of synergy."},
    46: {"name": "The Determination", "story": "The vessel of serendipity."},
    47: {"name": "The Realization", "story": "The epiphany maker."},
    48: {"name": "The Depth", "story": "The well of wisdom."},
    49: {"name": "The Catalyst", "story": "The revolutionary."},
    50: {"name": "The Values", "story": "The guardian of the law."},
    51: {"name": "The Shock", "story": "The thunder of initiation."},
    52: {"name": "The Stillness", "story": "The focused mountain."},
    53: {"name": "The Starter", "story": "The pressure to begin."},
    54: {"name": "The Ambition", "story": "The climber of stars."},
    55: {"name": "The Spirit", "story": "The abundance of emotion."},
    56: {"name": "The Storyteller", "story": "The wandering teacher."},
    57: {"name": "The Intuitive", "story": "The clarity of survival."},
    58: {"name": "The Joy", "story": "The vital challenger."},
    59: {"name": "The Sexual", "story": "The breaker of barriers."},
    60: {"name": "The Limitation", "story": "The transcendence of form."},
    61: {"name": "The Mystery", "story": "The knower of truth."},
    62: {"name": "The Detail", "story": "The bridge of facts."},
    63: {"name": "The Doubter", "story": "The logic of truth."},
    64: {"name": "The Confusion", "story": "The illumination of images."}
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
        geolocator = Nominatim(user_agent="ia_final_fix_v20")
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

# --- THE EPIC STORY ENGINE ---
def generate_epic_story(chart_data, orientation_title, lp, struggle_advice):
    sun_sign = chart_data['Sun']['Sign']
    sun_title = SIGN_LORE.get(sun_sign, "The Hero")
    sun_archetype = chart_data['Sun']['Name']
    
    moon_sign = chart_data['Moon']['Sign']
    moon_title = SIGN_LORE.get(moon_sign, "The Soul")
    
    ris_sign = chart_data['Rising']['Sign']
    ris_title = SIGN_LORE.get(ris_sign, "The Mask")
    
    lp_destiny = LIFE_PATH_LORE.get(lp, "A journey of mystery.").split(".")[0]
    
    dragon_name = struggle_advice[0].replace("The Quest for ", "")
    
    story = []
    
    # CHAPTER 1: THE ORIGIN
    story.append(f"CHAPTER 1: THE ORIGIN\n\nLong ago, the universe conspired to create a unique frequency, and it named that frequency 'You.' You were born under the blazing sun of {sun_sign}, imbuing you with the spirit of {sun_title}. This is your core, your fuel, and your inevitable nature. But to protect this intense light, you donned a mask. To the world, you first appear as {ris_sign}, {ris_title}. This is your armor and your first impression, the vehicle you drive through the physical world.")
    
    # CHAPTER 2: THE HEART
    story.append(f"CHAPTER 2: THE HEART\n\nBeneath the armor lies a secret engine: your Moon in {moon_sign}. While others see your actions, only you feel the pull of {moon_title}. This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. Ignoring this voice is what leads to exhaustion; honoring it is the secret to your endless regeneration.")
    
    # CHAPTER 3: THE PATH
    story.append(f"CHAPTER 3: THE PATH\n\nEvery hero needs a road to walk. Yours is the Path of the {lp}. This is not a random walk; it is a destiny of {lp_destiny}. The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, but the view from the top is the purpose you have been searching for.")
    
    # CHAPTER 4: THE WEAPON
    story.append(f"CHAPTER 4: THE WEAPON\n\nTo aid you on this path, you were gifted a specific superpower. In the language of the Archetypes, you carry the energy of '{sun_archetype}.' This is not a skill you learned; it is a frequency you emit. When you trust this power, doors open without force. When you doubt it, you meet resistance.")
    
    # CHAPTER 5: THE STRATEGY
    story.append(f"CHAPTER 5: THE STRATEGY\n\nBut power without control is dangerous. Your operating manual is defined by your Orientation: {orientation_title}. You are not designed to move like everyone else. Your specific strategy requires you to honor your nature—whether that is to wait, to respond, or to initiate. Deviation from this strategy is the root of your frustration.")
    
    # CHAPTER 6: THE DRAGON
    story.append(f"CHAPTER 6: THE DRAGON\n\nEvery story has an antagonist. Yours takes the form of {dragon_name}. This struggle you feel—whether in wealth, love, or purpose—is not a punishment. It is the friction necessary to sharpen your blade. The dragon guards the treasure. By facing your Shadow and applying your Archetype, you do not just slay the dragon; you integrate it.")
    
    # OUTRO
    story.append(f"This is the Legend of You. The map is in your hands. The stars have done their part; the rest of the story is yours to write.")
    
    return "\n\n".join(story)

# --- PDF ENGINE ---
def create_pdf_b64(name, lp, orientation_title, epic_story, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # TITLE
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 10, 'THE LEGEND OF YOU', 0, 1, 'C')
        pdf.set_font("Helvetica", 'I', 12)
        pdf.cell(0, 10, f"The Epic of {name}", 0, 1, 'C')
        pdf.ln(10)

        # THE STORY (Takes up the whole first section)
        pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 6, epic_story)
        pdf.ln(10)
        
        # BLUEPRINT SECTION (Page Break if needed)
        if pdf.get_y() > 200: pdf.add_page()
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Your Planetary Inventory", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        
        for k, v in chart.items():
            sign = v.get("Sign", "?")
            gate = v.get("Gate", "?")
            name_txt = v.get("Name", "")
            sign_txt = v.get("SignLore", "") # We use the short name now
            gate_story = v.get("Story", "")
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 8, f"{k}: {sign} (Archetype {gate}) - {name_txt}", 0, 1)
            
            pdf.set_font("Helvetica", '', 10)
            pdf.multi_cell(0, 5, f"{gate_story}")
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
        
        dt_obj = Datetime(dob.replace("-", "/"), tob, tz_offset)
        geo_obj = GeoPos(lat, lon)
        chart_p = Chart(dt_obj, geo_obj, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        design_date_obj = datetime.datetime.strptime(dob, "%Y-%m-%d") - datetime.timedelta(days=88)
        design_dob = design_date_obj.strftime("%Y/%m/%d")
        dt_design = Datetime(design_dob, tob, tz_offset)
        chart_d = Chart(dt_design, geo_obj, IDs=[const.SUN], hsys=const.HOUSES_PLACIDUS)

        chart_data = {}
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        p_sun = chart_p.get(const.SUN)
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1
        d_sun = chart_d.get(const.SUN)
        d_line = (int(d_sun.lon / 0.9375) % 6) + 1

        p_info = LINE_LORE.get(p_line, {"title": str(p_line), "desc": ""})
        d_info = LINE_LORE.get(d_line, {"title": str(d_line), "desc": ""})
        orientation_title = f"{p_info['title']} / {d_info['title']}"

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
        
        topic, advice_text = get_strategic_advice(struggle, chart_data)
        
        # GENERATE EPIC STORY
        epic_story = generate_epic_story(chart_data, orientation_title, lp, (topic, advice_text))
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1, "Name": "Error", "Story": ""}}
        orientation_title = "Unknown"
        lp = 0
        epic_story = "The legend is clouded. Please try again."
        topic, advice_text = ("Unknown", "Unknown")

    pdf_b64 = create_pdf_b64(name, lp, orientation_title, epic_story, chart_data)

    # HTML OUTPUT - Simple, Story-Focused
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
            <div class="story-text">{epic_story}</div>
        </div>

        <a href="data:application/pdf;base64,{pdf_b64}" download="The_Legend_of_You.pdf" target="_blank" class="btn">
            ⬇️ DOWNLOAD FULL LEGEND (PDF)
        </a>
    </body>
    </html>
    """
    return {"report": html}
