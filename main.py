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

# --- 1. DATA: THE HERO'S DESTINY (LIFE PATH) ---
LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the first arrow fired into the unknown. Your story is one of radical independence. You are not here to follow footprints; you are here to make them. Your destiny is to stand alone, conquer your self-doubt, and lead the tribe into a new era.",
    2: "The Peacemaker. You are the diplomat of the soul. In a world of noise, you are the whisper that brings harmony. Your hero's journey is to master the invisible threads that connect people, teaching the world that true power lies in cooperation, not dominance.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your weapon is your word, your art, and your radiant optimism. Your destiny is to lift the heaviness of the world and remind humanity that life is meant to be celebrated, not just endured.",
    4: "The Master Builder. You are the architect of the future. While others dream, you lay the bricks. Your story is one of endurance, legacy, and order. You are here to build a foundation so strong that it supports generations to come.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your hero's path is one of radical adaptability and adventure. You are here to break the chains of tradition and show the world what it looks like to be truly, terrifyingly free.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your heart beats for justice and beauty. Your journey is to carry the weight of responsibility without breaking, nurturing the tribe until they are strong enough to stand on their own.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth. You are here to look past the veil of illusion, solving the mysteries of existence and bringing that wisdom back to the valley.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money, power, and influence. You are here to prove that spiritual abundance can exist in the physical world, using your resources to empower the collective.",
    9: "The Humanitarian. You are the old soul returning for one last mission. Your story is one of letting go and unconditional love. You are here to heal the wounds of the world, leading not by force, but by the overwhelming power of your compassion.",
    11: "The Illuminator. You are the lightning rod of the divine. You walk the line between genius and madness, channeling high-frequency insights that shock the world awake. Your path is to be the visionary who sees the dawn before the sun rises.",
    22: "The Master Builder of Dreams. You are the bridge between heaven and earth. You possess the rare ability to turn the most impossible spiritual visions into concrete reality. Your destiny is to build systems that change the course of history.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity through pure, unadulterated service. You heal the world simply by being present within it."
}

# --- 2. DATA: THE DRAGON (STRUGGLE) ---
STRUGGLE_LORE = {
    "wealth": {
        "title": "The Quest for Abundance",
        "desc": "Your dragon is Scarcity. You feel blocked financially not because you lack skill, but because you are fighting against your own energy flow. Your chart reveals that abundance is a frequency, not a number. When you align your work with your Jupiter placement, you stop chasing the gold and become the magnet that attracts it. Your quest is to build a container worthy of the wealth seeking you."
    },
    "relationship": {
        "title": "The Quest for Connection",
        "desc": "Your dragon is Disharmony. The friction you feel is a signal that you are trying to read from a script that wasn't written for you. Your Venus placement reveals your true love language. Your quest is to stop contorting yourself to fit others and instead stand firmly in your own magnetic design. When you honor your own energy, the right tribe will find you."
    },
    "purpose": {
        "title": "The Quest for Meaning",
        "desc": "Your dragon is The Void. You feel lost because you are looking for a 'destination' on a map that doesn't exist. Purpose is not a job; it is a geometry. Your North Node and Sun Gate define your unique frequency. Your quest is to stop 'doing' and start 'being.' When you simply emit your true signal, the path will form beneath your feet."
    },
    "health": {
        "title": "The Quest for Vitality",
        "desc": "Your dragon is Exhaustion. Your body is the hardware for your consciousness, and it is overheating because you are running software that contradicts your design. Your Saturn placement holds the key to your boundaries. Your quest is to surrender to your own internal rhythm, honoring your need for rest as a sacred act of power."
    },
    "general": {
        "title": "The Quest for Alignment",
        "desc": "Your dragon is Confusion. You feel adrift because you are a unique design trying to function in a standardized world. You are not standard. Your Rising Sign and Orientation hold the compass you need. Your quest is to return to your core strategy, trusting that your internal navigation system is the only authority you need."
    }
}

# --- 3. DATA: THE AVATAR (ORIENTATION) ---
LINE_LORE = {
    1: {"title": "The Investigator", "desc": "The Foundation Builder. Like a master detective, you cannot act until you understand the ground beneath your feet. Your superpower is certainty. You build your confidence through deep study and research."},
    2: {"title": "The Natural", "desc": "The Reluctant Hero. You possess innate gifts that you never had to study for—you are simply 'good at it.' You crave solitude, waiting in your hermitage until the right person calls you out to save the day."},
    3: {"title": "The Experimenter", "desc": "The Fearless Explorer. You learn by bumping into the walls of life. For you, there are no mistakes, only discoveries. You are the scientist of the human experience, finding what works by discovering what doesn't."},
    4: {"title": "The Networker", "desc": "The Tribal Weaver. You are the heart of the community. Your power lies in your connections. Your greatest opportunities will never come from strangers, but from the web of friends and allies you nurture."},
    5: {"title": "The Fixer", "desc": "The General. Strangers project their hopes onto you, seeing you as the savior in times of crisis. Your superpower is practical, universal solutions. You arrive, you fix the problem, and you vanish."},
    6: {"title": "The Role Model", "desc": "The Sage on the Mountain. Your life is a three-act play: the reckless experimenter (youth), the observer on the roof (mid-life), and finally, the wise example of authenticity (maturity)."}
}

# --- 4. DATA: THE STARS (SIGNS) ---
SIGN_LORE = {
    "Aries": "The Warrior. You are the spark that starts the fire. Driven by raw instinct and courage, you are here to initiate the new cycle.",
    "Taurus": "The Builder. You are the earth itself. Patient, sensual, and unmovable, you build the structures that last for generations.",
    "Gemini": "The Messenger. You are the wind. Your mind is a kaleidoscope of connections, weaving stories and ideas that keep the world moving.",
    "Cancer": "The Protector. You are the tide. Deeply intuitive and fiercely loyal, you build the shell that protects the vulnerable heart of the tribe.",
    "Leo": "The King/Queen. You are the sun. You do not just enter a room; you warm it. Your creativity is the life-force that reminds others of their own light.",
    "Virgo": "The Alchemist. You are the perfectionist. You see the flaw only because you love the potential. You serve the world by refining it into gold.",
    "Libra": "The Diplomat. You are the scales. You exist in the delicate balance between self and other, constantly adjusting the energy to create harmony.",
    "Scorpio": "The Sorcerer. You are the depths. Unafraid of the dark, you dive into the mysteries of birth, death, and rebirth to find the truth.",
    "Sagittarius": "The Philosopher. You are the arrow. Driven by a hunger for truth and adventure, you expand the horizons of what is possible.",
    "Capricorn": "The Architect. You are the mountain peak. Driven by ambition and legacy, you climb the hard path to build an empire that outlasts you.",
    "Aquarius": "The Revolutionary. You are the lightning bolt. You see the future before it arrives, breaking old structures to liberate the collective.",
    "Pisces": "The Mystic. You are the ocean. Dissolving boundaries, you dream the collective dream, touching the divine and bringing it down to earth."
}

# --- 5. DATA: THE SUPERPOWERS (GATES) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "In the void, there was nothing. Then, you arrived. You are the primal spark of creativity, here to birth something entirely new into the universe."},
    2: {"name": "The Receptive", "story": "You are the cosmic womb. You provide the direction and the blueprint that guides raw, chaotic energy into beautiful form."},
    3: {"name": "The Innovator", "story": "Order is stagnant. You are the necessary chaos. You break the established rules so that life can mutate and evolve into something better."},
    4: {"name": "The Logic Master", "story": "The world is full of doubt. You bring the formula. Your superpower is providing the logic and patterns that calm the anxiety of the tribe."},
    5: {"name": "The Fixer", "story": "The storm rages, but you wait. You understand the rhythm of nature. You teach the world that waiting is not inactivity; it is perfect timing."},
    6: {"name": "The Peacemaker", "story": "Where there is conflict, you bring flow. You use your profound emotional intelligence to dissolve friction and create resolution."},
    7: {"name": "The Leader", "story": "You do not force; you guide. You are the true leader who represents the collective hope of the tribe, pointing them toward the future."},
    8: {"name": "The Stylist", "story": "You are the rebel of expression. You inspire others not by telling them what to do, but by having the courage to be authentically you."},
    9: {"name": "The Focuser", "story": "You see the needle in the haystack. Your power is the ability to focus on the one tiny detail that determines the success or failure of the whole."},
    10: {"name": "The Self", "story": "In a world of masks, you are the face. Your journey is to master the hardest art of all: the art of self-love and authentic being."},
    11: {"name": "The Idealist", "story": "You catch ideas from the heavens. You are the vessel for the images and light that inspire humanity to strive for something greater."},
    12: {"name": "The Articulate", "story": "When you speak, the world listens. You master the timing of the voice, channeling words that can mutate the soul of the listener."},
    13: {"name": "The Listener", "story": "You are the keeper of secrets. The past whispers to you, and you hold the collective memory so the tribe can learn from history."},
    14: {"name": "The Power House", "story": "You are the fuel tank. You possess the unflagging creative energy and wealth to drive the dreams of the world into reality."},
    15: {"name": "The Humanist", "story": "You embrace the extremes. From the gutters to the stars, you accept the full rhythm of humanity, weaving it into a single flow."},
    16: {"name": "The Master", "story": "You are the virtuoso. Through enthusiasm and repetition, you turn raw talent into effortless mastery that dazzles the world."},
    17: {"name": "The Opinion", "story": "You see the pattern. You organize the chaos of the present into a logical, farsighted view of what is coming next."},
    18: {"name": "The Improver", "story": "You see what is broken. You critique not to hurt, but to heal. Your gift is the relentless drive to perfect the world."},
    19: {"name": "The Sensitive", "story": "You feel the need before it is spoken. You are the barometer of the tribe, ensuring that everyone has food, warmth, and a place to belong."},
    20: {"name": "The Now", "story": "There is no past. There is no future. There is only this breath. You operate with pure, spontaneous clarity in the present moment."},
    21: {"name": "The Controller", "story": "You take the reins. In a chaotic world, you manage the resources and the people to ensure the survival and success of the kingdom."},
    22: {"name": "The Grace", "story": "You open the door. Your social grace and emotional openness create a space where others feel safe to express their truth."},
    23: {"name": "The Assimilator", "story": "You cut through the noise. You are the remover of obstacles, stripping away complexity to reveal the simple, essential truth."},
    24: {"name": "The Rationalizer", "story": "You act as the silence between the notes. You revisit the past, thinking in circles until the breakthrough of invention arrives."},
    25: {"name": "The Spirit", "story": "You are the Shaman. Despite the wounds of the world, you retain a spirit of universal love and innocence that heals others."},
    26: {"name": "The Egoist", "story": "You are the dealmaker. You use your willpower and charm to direct resources and attention exactly where they are needed."},
    27: {"name": "The Nurturer", "story": "You are the guardian. You protect the weak and feed the hungry, ensuring that the heritage and values of the tribe survive."},
    28: {"name": "The Risk Taker", "story": "You look death in the eye. You confront the darkest fears to find a purpose that makes life truly worth living."},
    29: {"name": "The Devoted", "story": "You say 'Yes.' When you commit, you commit all the way, persevering through the abyss to find the wisdom on the other side."},
    30: {"name": "The Passion", "story": "You burn. You carry the fire of desire and emotion, teaching the world what it means to feel life with absolute intensity."},
    31: {"name": "The Voice", "story": "You stand at the podium. You are the elected voice of the collective, speaking the vision that moves the tribe forward."},
    32: {"name": "The Conservative", "story": "You are the root. You assess what is valuable from the past and preserve it, ensuring that success is enduring and stable."},
    33: {"name": "The Reteller", "story": "You retreat to the cave. You process the memories of the tribe, turning raw experience into the wisdom of history."},
    34: {"name": "The Power", "story": "You are the giant. You are the pure, independent force of life expressing itself through individual power and activity."},
    35: {"name": "The Progress", "story": "You ignite the change. Driven by a hunger for experience, you ensure that the human story never becomes stagnant."},
    36: {"name": "The Crisis", "story": "You walk through the fire. You survive the emotional darkness to bring the light of compassion to a suffering world."},
    37: {"name": "The Family", "story": "You build the home. You are the glue of the community, holding the tribe together through friendship, touch, and affection."},
    38: {"name": "The Fighter", "story": "You stand your ground. You fight the battles that give life meaning, preserving your individual honor against all odds."},
    39: {"name": "The Provocateur", "story": "You poke the bear. You provoke the spirit of others, shaking them out of their slumber and forcing them to feel."},
    40: {"name": "The Aloneness", "story": "You build the wall to save the city. You separate yourself from the tribe to regenerate your power and deliver deliverance."},
    41: {"name": "The Fantasy", "story": "You hold the seed. You are the dreamer who imagines a new world, starting the cycle of experience with a single fantasy."},
    42: {"name": "The Finisher", "story": "You close the book. You maximize the cycle of experience, bringing things to a satisfying and fruitful conclusion."},
    43: {"name": "The Insight", "story": "You hear the voice within. You carry the breakthrough insight that creates a new knowing, changing the world's mind."},
    44: {"name": "The Alert", "story": "You smell the future. Your instinct allows you to align the right people and resources to ensure the success of the tribe."},
    45: {"name": "The Gatherer", "story": "You sit on the throne. You are the King/Queen who holds the tribe's resources together, ruling through education and synergy."},
    46: {"name": "The Determination", "story": "You are the vessel. You succeed by being in the right place at the right time, honoring the sanctity of the physical body."},
    47: {"name": "The Realization", "story": "You connect the dots. You sort through the confusion of the past to find the sudden epiphany that makes sense of it all."},
    48: {"name": "The Depth", "story": "You draw from the well. You possess a depth of talent and wisdom that provides fresh solutions to the world's problems."},
    49: {"name": "The Catalyst", "story": "You rewrite the contract. You reject the old, unfair principles to establish a higher, more emotional order for the tribe."},
    50: {"name": "The Values", "story": "You guard the cauldron. You are the custodian of the tribe's laws and values, ensuring that the community thrives."},
    51: {"name": "The Shock", "story": "You are the thunder. You shock people out of their complacency, initiating them into the power of the individual spirit."},
    52: {"name": "The Stillness", "story": "You are the mountain. You hold your energy in deep, focused stillness, waiting for the perfect moment to act."},
    53: {"name": "The Starter", "story": "You plant the seed. You are the pressure to begin. You initiate the new cycle without worrying about how it will end."},
    54: {"name": "The Ambition", "story": "You climb the ladder. You drive the tribe upward, seeking spiritual and material mastery through ambition and drive."},
    55: {"name": "The Spirit", "story": "You drink the cup. You accept the intense highs and lows of emotion to find the abundance of the spirit within."},
    56: {"name": "The Storyteller", "story": "You are the wanderer. You travel through ideas and places, weaving the collective myth that teaches the tribe who they are."},
    57: {"name": "The Intuitive", "story": "You hear the silence. You possess a penetrating intuition that hears the truth in the now, ensuring your survival."},
    58: {"name": "The Joy", "story": "You fix what is broken. You challenge authority with the joy of making life better, healthier, and more efficient."},
    59: {"name": "The Sexual", "story": "You break the barrier. You use life-force energy to penetrate the walls between people, creating intimacy and new life."},
    60: {"name": "The Limitation", "story": "You accept the walls. You understand that magic needs a container. You accept the boundaries of form to transcend them."},
    61: {"name": "The Mystery", "story": "You ask 'Why?'. You dive into the unknowable mystery to bring back universal truths that inspire the world."},
    62: {"name": "The Detail", "story": "You name the animals. You build a bridge of understanding through precise facts, details, and logical language."},
    63: {"name": "The Doubter", "story": "You question the answer. You use critical logic to test the future, doubting everything until the truth is proven."},
    64: {"name": "The Confusion", "story": "You watch the movie. You process the chaos of mental images until they resolve into a moment of pure illumination."}
}

# --- 6. LOGIC ENGINES ---

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
        geolocator = Nominatim(user_agent="ia_final_fix_v14")
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

# --- STORY ENGINE: THE LEGEND OF YOU ---
def generate_hero_narrative(chart_data, orientation_title):
    sun_sign = chart_data['Sun']['Sign']
    sun_gate_name = chart_data['Sun']['Name']
    ris_sign = chart_data['Rising']['Sign']
    
    story = f"The Legend begins with a {sun_sign}. You were born with the heart of {sun_sign}, carrying the superpower of '{sun_gate_name}.' "
    story += f"But the world does not always see this inner fire immediately. To the world, you appear as a {ris_sign}, walking the path of {orientation_title}. "
    story += "Your journey is to integrate these two worlds: to use your outer mask to protect your inner light, and to master your unique strategy to slay the dragons of resistance."
    return story

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

# --- PDF ENGINE ---
def create_pdf_b64(name, lp, lp_desc, orientation_title, orientation_body, hero_story, advice, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # TITLE
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, 'THE LEGEND OF YOU', 0, 1, 'C')
        pdf.ln(5)

        # 1. THE HERO (Intro)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        pdf.multi_cell(0, 7, hero_story)
        pdf.ln(5)

        # 2. THE DESTINY (Life Path)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Your Destiny (Life Path {lp})", 0, 1)
        pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 6, lp_desc)
        pdf.ln(5)

        # 3. THE AVATAR (Orientation)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Your Avatar: {orientation_title}", 0, 1)
        pdf.set_font("Helvetica", '', 11)
        desc_lines = orientation_body.split("<br>")
        for line in desc_lines:
             clean_line = line.replace("<b>", "").replace("</b>", "")
             if clean_line.strip():
                 pdf.multi_cell(0, 6, clean_line.strip())
                 pdf.ln(1)
        pdf.ln(5)
        
        # 4. THE QUEST (Struggle)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Current Quest: {advice[0]}", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        clean_advice = advice[1].replace("**", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, clean_advice)
        pdf.ln(5)
        
        # 5. SUPERPOWERS (Planets)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Your Inventory (Planetary Blueprint)", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        
        for k, v in chart.items():
            sign = v.get("Sign", "?")
            gate = v.get("Gate", "?")
            name_txt = v.get("Name", "")
            sign_txt = v.get("SignLore", "")
            gate_story = v.get("Story", "")
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 8, f"{k}: {sign} (Gate {gate}) - {name_txt}", 0, 1)
            
            pdf.set_font("Helvetica", 'I', 10)
            pdf.multi_cell(0, 5, f"{sign_txt}")
            
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
        
        # Life Path
        try:
            digits = [int(d) for d in dob if d.isdigit()]
            total = sum(digits)
            while total > 9 and total not in [11, 22, 33]:
                total = sum(int(d) for d in str(total))
            lp = total
        except: lp = 0
        
        lp_desc = LIFE_PATH_LORE.get(lp, "A path of unique discovery.")
        
        # HERO STORY GENERATION
        hero_story = generate_hero_narrative(chart_data, orientation_title)
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1, "Name": "Error", "Story": ""}}
        orientation_title = "Unknown"
        orientation_body = ""
        lp = 0
        lp_desc = "Unknown"
        hero_story = "The mists of time obscure your legend. Please try again."

    topic, advice_text = get_strategic_advice(struggle, chart_data)
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
        .gate-title {{ color: #C71585; font-weight: bold; font-size: 1.1em; }}
        .gate-desc {{ font-size: 0.95em; color: #44
