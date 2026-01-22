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

# --- 1. DATA: LOCATIONS (RESTORED) ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles")
}

# --- 2. DATA: NUMEROLOGY (LIFE PATH) ---
LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your journey is one of independence and innovation. You are learning to stand on your own two feet and lead without looking back.",
    2: "The Peacemaker. You are the bridge between souls. Your gift is intuition and diplomacy. You are here to learn the power of cooperation and to find the divine balance between giving and receiving.",
    3: "The Creative Spark. You are the child of the universe, here to express joy, art, and communication. Your path is to find your voice and scatter light into the darker corners of the world.",
    4: "The Master Builder. You are the stone foundation. Your life is about creating stability, order, and legacy. You turn the chaotic dreams of others into solid reality through hard work and systems.",
    5: "The Freedom Seeker. You are the wind of change. Your path is one of adventure, adaptability, and breaking chains. You are here to show the world how to embrace the unexpected.",
    6: "The Nurturer. You are the cosmic parent. Your heart beats for justice, home, and family. Your journey is to master the art of responsibility without carrying the weight of the entire world.",
    7: "The Seeker of Truth. You are the mystic and the analyst. Your path is a solitary climb for wisdom. You are here to look past the veil of illusion and discover the deeper spiritual mechanics of life.",
    8: "The Powerhouse. You are the executive of the material world. Your journey involves mastering money, power, and authority. You are here to build abundance and use it to empower the collective.",
    9: "The Humanitarian. You are the old soul. Your path is one of completion and letting go. You are here to serve the greater good, leading with compassion and wisdom for all of humanity.",
    11: "The Illuminator (Master). You are the lightning rod. You channel high-frequency spiritual insight. Your path is to inspire others by living your truth, often walking a line between genius and madness.",
    22: "The Master Architect. You bring heaven to earth. You have the vision of the 11 and the practicality of the 4. Your destiny is to build massive systems that change the course of history.",
    33: "The Master Teacher. You are the avatar of compassion. Your path is to uplift the vibration of humanity through unconditional love and spiritual guidance."
}

# --- 3. DATA: STRUGGLE ADVICE ---
STRUGGLE_LORE = {
    "wealth": {
        "title": "Wealth Architecture",
        "desc": "Your financial blocks are rarely about math; they are about energy. You are being called to look at where you are 'leaking' power. Abundance requires a container. Your chart suggests that when you align your work with your specific design (checking your Jupiter placement), the resources will flow. Stop chasing; start building a system that can hold what is coming."
    },
    "relationship": {
        "title": "Relational Design",
        "desc": "The friction you feel in relationships is a mirror. You are trying to act from a script that isn't yours. Your chart reveals a specific way you are designed to connect (look at your Venus sign). When you honor your own energy field first, you stop pulling at others and start magnetizing the right tribe to you."
    },
    "purpose": {
        "title": "Purpose Alignment",
        "desc": "You feel lost because you are looking for a 'destination' rather than a frequency. Your purpose is not a job title; it is the unique geometry of your energy field. Look to your North Node and your Sun Gate. When you simply *are* that energy, the path appears beneath your feet. Stop 'doing' and start 'being' your design."
    },
    "health": {
        "title": "Vitality Decoding",
        "desc": "Your physical body is the hardware for your consciousness. If you are exhausted, it is because you are running software that contradicts your design. Check your Saturn placement for where you need boundaries. Your vitality returns when you stop pushing against your own river and start floating with it."
    },
    "general": {
        "title": "Core Alignment",
        "desc": "The confusion you feel is simply a signal that you are out of alignment with your blueprint. You are trying to be a 'Normal' in a world designed for standardization. You are not standard. Return to your Rising Sign and your Orientation strategy. That is your anchor in the storm."
    }
}

# --- 4. DATA: ORIENTATION (LINES) ---
LINE_LORE = {
    1: {"title": "The Investigator", "desc": "The Foundation. Like a detective, you need to study and understand the details before you can trust the ground beneath you. You build confidence through knowledge."},
    2: {"title": "The Natural", "desc": "The Hermit. You have innate gifts you didn't study for. You prefer to be left alone until the right person calls you out to share your genius."},
    3: {"title": "The Experimenter", "desc": "The Martyr. You learn by bumping into life. There are no mistakes for you, only discoveries. You find what works by finding what doesn't."},
    4: {"title": "The Networker", "desc": "The Opportunist. You are deeply connected to your tribe. Your best opportunities don't come from strangers, but through your close web of friends."},
    5: {"title": "The Fixer", "desc": "The Heretic. Strangers project their hopes onto you. You provide practical, universal solutions that can 'save the day' in a crisis."},
    6: {"title": "The Role Model", "desc": "The Sage. You live in three phases: experimenting young, observing in mid-life, and emerging as a wise example of authenticity."}
}

# --- 5. DATA: ASTROLOGY (SIGNS) ---
SIGN_LORE = {
    "Aries": "The Initiator. Like the first sprout of spring, you break through the soil with raw, explosive energy. You are the warrior of the zodiac, unafraid to go where no one has gone before.",
    "Taurus": "The Builder. You are the garden itself—fertile, stable, and patient. You understand the value of slow growth and sensory pleasure. You build things that last for generations.",
    "Gemini": "The Messenger. You are the wind that carries the pollen. Your mind is a kaleidoscope of ideas, connecting dots that others don't even see. You keep the air moving.",
    "Cancer": "The Protector. You are the ocean tide—deep, rhythmic, and holding life within you. You build a shell to protect the vulnerable, leading with profound emotional intelligence.",
    "Leo": "The Radiant. You are the sun at high noon. You don't just enter a room; you warm it. Your creativity is a life-force that reminds others of the joy of existing.",
    "Virgo": "The Alchemist. You are the harvest maiden separating the wheat from the chaff. You see the flaw only because you love the potential for perfection. You serve by refining.",
    "Libra": "The Harmonizer. You are the scales of justice. You exist in the space 'between' people, constantly adjusting the energy to find equilibrium, beauty, and peace.",
    "Scorpio": "The Transformer. You are the phoenix in the fire. You are comfortable in the darkness that scares others, because you know that is where the treasure is buried.",
    "Sagittarius": "The Explorer. You are the arrow shot toward the horizon. You seek the truth, the philosophy, and the adventure. You remind the tribe that there is more out there.",
    "Capricorn": "The Architect. You are the mountain goat climbing the peak. You understand structure, time, and legacy. You are building an empire that will outlast you.",
    "Aquarius": "The Visionary. You are the lightning bolt. You see the future before it arrives. You break the old structures to make room for the collective evolution.",
    "Pisces": "The Mystic. You are the mist on the water. You dissolve the boundaries between self and other, dreaming the collective dream and touching the divine."
}

# --- 6. DATA: HUMAN DESIGN (GATES WITH STORIES) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "Long ago, there was a void. Then, a spark. You are that spark. You carry the energy of pure creation, bringing something out of nothingness."},
    2: {"name": "The Receptive", "story": "The spark needs a place to land. You are the womb of the universe. You are the blueprint that guides raw energy into beautiful form."},
    3: {"name": "The Innovator", "story": "In the beginning, there was order. Then you arrived. You are the necessary chaos that breaks the rules so that life can evolve into something new."},
    4: {"name": "The Logic Master", "story": "The tribe was plagued by doubt. You stepped forward with a formula. You provide the logic that calms the anxiety of the unknown."},
    5: {"name": "The Fixer", "story": "The storm raged, but you sat still. You understand the rhythm of nature. You teach the world that waiting is not inactivity; it is timing."},
    6: {"name": "The Peacemaker", "story": "Two sides stood ready for war. You stood in the middle. You carry the emotional intelligence to dissolve conflict and create a third way."},
    7: {"name": "The Leader", "story": "The army had strength but no direction. You pointed the way. You lead not by force, but by embodying the future the tribe wants to reach."},
    8: {"name": "The Stylist", "story": "The world was gray and uniform. Then you walked in. You inspire others simply by the courage of your own unique, authentic expression."},
    9: {"name": "The Focuser", "story": "While others looked at the mountain, you saw the loose stone. You have the power to focus on the tiny detail that determines success or failure."},
    10: {"name": "The Self", "story": "In a world of masks, you took yours off. You are here to master the hardest art of all: the art of simply being yourself."},
    11: {"name": "The Idealist", "story": "Darkness fell, and you lit a candle. You catch ideas from the ether, filling the collective mind with images of what *could* be."},
    12: {"name": "The Articulate", "story": "The tribe was silent. You opened your mouth, and the soul spoke. You master the timing of voice to impact the spirit of others."},
    13: {"name": "The Listener", "story": "They came to you with their secrets. You are the great vault of memory. You hold the past so the future can learn from it."},
    14: {"name": "The Power House", "story": "The wagon was heavy. You picked it up. You possess the unflagging creative fuel to drive the dreams of the world into reality."},
    15: {"name": "The Humanist", "story": "You walked with kings and beggars alike. You embrace all extremes of humanity, weaving them into a single, flowing tapestry."},
    16: {"name": "The Master", "story": "You practiced while others slept. You turn raw talent into effortless mastery through the magic of enthusiasm and repetition."},
    17: {"name": "The Opinion", "story": "You climbed the tower and looked ahead. You organize the chaos of the present into a logical view of the future."},
    18: {"name": "The Improver", "story": "You saw the crack in the foundation. You critique not to hurt, but to heal. You challenge the pattern so it can be perfected."},
    19: {"name": "The Sensitive", "story": "You felt the cold before anyone else. You are the barometer of the tribe, ensuring everyone has enough food, warmth, and love."},
    20: {"name": "The Now", "story": "There is no past, no future. Only this breath. You operate with pure, spontaneous clarity in the present moment."},
    21: {"name": "The Controller", "story": "The harvest was plentiful but wasted. You took charge. You manage the resources to ensure the survival and success of the tribe."},
    22: {"name": "The Grace", "story": "You listened, and they felt heard. You carry a social grace that opens doors, allowing emotional truth to enter the room."},
    23: {"name": "The Assimilator", "story": "The explanation was complex. You said it in three words. You strip away the noise to reveal the essential, simple truth."},
    24: {"name": "The Rationalizer", "story": "You sat in the silence until the answer returned. You revisit the past over and over to find the new way forward."},
    25: {"name": "The Spirit", "story": "The world was harsh, but you remained soft. You act as the Shaman, retaining universal love and innocence despite the wounds."},
    26: {"name": "The Egoist", "story": "You sold the dream. You are the great influencer, using your willpower to direct resources and attention where they are needed."},
    27: {"name": "The Nurturer", "story": "The child was hungry. You fed them. You are the guardian of the tribe, caring for the weak and preserving the heritage."},
    28: {"name": "The Risk Taker", "story": "Death whispered, and you smiled. You confront the fear of the end to find a life that is truly worth living."},
    29: {"name": "The Yes Man", "story": "The journey was dangerous. You said 'Yes' anyway. You commit to the experience, persevering through the abyss to find wisdom."},
    30: {"name": "The Passion", "story": "You felt a hunger that could not be fed. You burn with the fire of desire, teaching the world what it means to feel deeply."},
    31: {"name": "The Voice", "story": "The people were ready. You stood at the podium. You speak the vision of the collective, influencing the direction of the future."},
    32: {"name": "The Conservative", "story": "The wind blew, but the roots held. You assess what is valuable from the past and preserve it for future success."},
    33: {"name": "The Reteller", "story": "You retreated to the cave to think. You process the memories of the tribe, turning raw experience into wisdom."},
    34: {"name": "The Power", "story": "You are the giant in the room. You are the pure, independent force of life expressing itself through individual activity."},
    35: {"name": "The Progress", "story": "You were bored, so you started a fire. You are driven to taste every experience, knowing that change is the only constant."},
    36: {"name": "The Crisis", "story": "The sky turned black. You found the light. You survive the emotional storm to bring compassion to the darkness of others."},
    37: {"name": "The Family", "story": "You set the table for everyone. You build the community through friendship, bargains, and deep emotional affection."},
    38: {"name": "The Fighter", "story": "They told you to submit. You stood up. You fight the battles that give life meaning, preserving individual honor."},
    39: {"name": "The Provocateur", "story": "They were asleep. You poked them. You provoke the spirit of others to wake them up to their own emotional truth."},
    40: {"name": "The Aloneness", "story": "You built the wall to save the kingdom. You separate yourself from the group to regenerate your power and deliver deliverance."},
    41: {"name": "The Fantasy", "story": "You dreamed of a garden in the desert. You hold the seed of the fantasy that starts the new cycle of experience."},
    42: {"name": "The Finisher", "story": "You stayed until the last page was turned. You maximize the cycle and bring it to a satisfying, fruitful conclusion."},
    43: {"name": "The Insight", "story": "You heard a voice in the silence. You carry the breakthrough insight that changes the way the world thinks."},
    44: {"name": "The Alert", "story": "You smelled the rain before the clouds appeared. You use instinct to align the right people and resources for success."},
    45: {"name": "The Gatherer", "story": "You sat on the throne. You are the King/Queen who holds the resources together for the benefit of the kingdom."},
    46: {"name": "The Determination", "story": "You were in the right place at the right time. You succeed by honoring the sanctity of the physical body and its serendipity."},
    47: {"name": "The Realization", "story": "The puzzle was scattered. You saw the picture. You sort through the confusion of the past to find the sudden epiphany."},
    48: {"name": "The Depth", "story": "You dropped the bucket deep into the well. You bring fresh, deep solutions to surface problems using your vast depth."},
    49: {"name": "The Catalyst", "story": "The laws were unjust. You rewrote them. You reject old principles to establish a higher, more emotional order."},
    50: {"name": "The Values", "story": "You guarded the pot of stew. You are the guardian of the tribe's values, ensuring the laws serve the people."},
    51: {"name": "The Shock", "story": "Lightning struck the tower. You are the thunder. You shock people out of complacency and initiate them into the spirit."},
    52: {"name": "The Stillness", "story": "You sat as still as a mountain. You hold your energy in deep concentration until the perfect moment to act."},
    53: {"name": "The Starter", "story": "You planted the seed. You are the pressure to begin. You initiate the cycle of evolution without worrying about the end."},
    54: {"name": "The Ambition", "story": "You looked up at the stars. You drive the tribe upward, seeking spiritual and material mastery through ambition."},
    55: {"name": "The Spirit", "story": "The cup was half full. You drank it. You accept the intense highs and lows of emotion to find the spirit within."},
    56: {"name": "The Storyteller", "story": "You traveled far and returned with a tale. You weave the collective myth, teaching through distraction and wandering."},
    57: {"name": "The Intuitive", "story": "A twig snapped. You knew. You hear the truth in the acoustic vibration of the now. You survive by instinct."},
    58: {"name": "The Joy", "story": "You saw a better way. You challenge authority with the joy of making life better and more efficient for everyone."},
    59: {"name": "The Sexual", "story": "You broke down the wall. You use life-force energy to break barriers and create intimate union that produces life."},
    60: {"name": "The Limitation", "story": "The river needs banks to flow. You accept the boundaries of form so that the magic can transcend them."},
    61: {"name": "The Mystery", "story": "You asked 'Why?'. You dive into the unknowable mystery to bring back universal truth and inspiration."},
    62: {"name": "The Detail", "story": "You named the animals. You build a bridge of understanding through precise facts and details."},
    63: {"name": "The Doubter", "story": "You questioned the answer. You use critical logic to test the validity of the future. You doubt so we can know."},
    64: {"name": "The Confusion", "story": "You stared at the stars until they formed shapes. You process the chaos of images until they resolve into illumination."}
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
        geolocator = Nominatim(user_agent="ia_final_fix_v13")
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

# --- UPDATED STRATEGIC ADVICE ENGINE ---
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

# --- UPDATED PDF ENGINE ---
def create_pdf_b64(name, lp, lp_desc, orientation_title, orientation_body, advice, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
        pdf.ln(5)

        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1)
        pdf.ln(2)

        # 1. LIFE PATH
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Life Path: {lp}", 0, 1)
        pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 6, lp_desc)
        pdf.ln(5)

        # 2. ORIENTATION
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Orientation: {orientation_title}", 0, 1)
        pdf.set_font("Helvetica", '', 11)
        desc_lines = orientation_body.split("<br>")
        for line in desc_lines:
             clean_line = line.replace("<b>", "").replace("</b>", "")
             if clean_line.strip():
                 pdf.multi_cell(0, 6, clean_line.strip())
                 pdf.ln(1)
        pdf.ln(5)
        
        # 3. STRUGGLE
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"Insight: {advice[0]}", 0, 1)
        pdf.set_font("Helvetica", '', 12)
        clean_advice = advice[1].replace("**", "").replace("<br>", "\n")
        pdf.multi_cell(0, 7, clean_advice)
        pdf.ln(5)
        
        # 4. BLUEPRINT
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Planetary Blueprint", 0, 1)
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
        
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        chart_data = {"Sun": {"Sign": "Unknown", "Gate": 1, "Name": "Error", "Story": ""}}
        orientation_title = "Unknown"
        orientation_body = ""
        lp = 0
        lp_desc = "Unknown"

    topic, advice_text = get_strategic_advice(struggle, chart_data)
    pdf_b64 = create_pdf_b64(name, lp, lp_desc, orientation_title, orientation_body, (topic, advice_text), chart_data)

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
        .gate-desc {{ font-size: 0.95em; color: #444; display: block; margin-top: 4px; font-style: italic; }}
        .sign-desc {{ font-size: 0.9em; color: #666; display: block; margin-bottom: 10px; border-left: 3px solid #eee; padding-left: 10px; }}
        .orientation-tag {{ 
            background: #eee; padding: 5px 10px; border-radius: 4px; font-weight: bold; color: #555; font-size: 0.9em;
            display: inline-block; margin-top: 5px;
        }}
        .orientation-block {{
            background: #fafafa; padding: 15px; border-radius: 8px; font-size: 0.95em; color: #444; margin-top: 15px;
        }}
        .lp-block {{
            background: #fff8e1; padding: 15px; border-radius: 8px; font-size: 0.95em; color: #5d4037; margin-top: 10px; border: 1px solid #ffe0b2;
        }}
        .btn {{ 
            background-color: #D4AF37; color: white; border: none; padding: 15px 30px; 
            font-size: 16px; border-radius: 50px; cursor: pointer; display: block; 
            width: 100%; max-width: 300px; margin: 20px auto; text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-decoration: none;
        }}
        .spacer {{ height: 500px; }}
    </style>
    </head>
    <body>
        <div class="card" style="text-align:center;">
            <h2>The Integrated Self</h2>
            <p>Prepared for {name}</p>
            
            <p><strong>Life Path: {lp}</strong></p>
            <div class="lp-block" style="text-align: left;">
                {lp_desc}
            </div>
            
            <p style="margin-top: 20px;"><span class="orientation-tag">Orientation: {orientation_title}</span></p>
            <div class="orientation-block" style="text-align: left;">
                {orientation_body}
            </div>
        </div>

        <div class="card" style="border-left: 5px solid #D4AF37;">
            <h2>⚡ Strategic Insight: {topic}</h2>
            <p>{advice_text}</p>
        </div>

        <div class="card">
            <h2>The Blueprint</h2>
            
            <p><strong>☀️ Sun in {chart_data.get('Sun',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Sun',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Sun',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Sun',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Sun',{}).get('Story','')}"</span></p>
            
            <p><strong>🌙 Moon in {chart_data.get('Moon',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Moon',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Moon',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Moon',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Moon',{}).get('Story','')}"</span></p>
            
            <p><strong>🏹 Rising in {chart_data.get('Rising',{}).get('Sign','?')}</strong> (Gate {chart_data.get('Rising',{}).get('Gate',0)})<br>
            <span class="sign-desc">{chart_data.get('Rising',{}).get('SignLore','')}</span>
            <span class="gate-title">{chart_data.get('Rising',{}).get('Name','')}</span><br>
            <span class="gate-desc">"{chart_data.get('Rising',{}).get('Story','')}"</span></p>
        </div>

        <a href="data:application/pdf;base64,{pdf_b64}" download="Integrated_Self.pdf" target="_blank" class="btn">
            ⬇️ DOWNLOAD PDF REPORT
        </a>

        <div class="spacer"></div>
    </body>
    </html>
    """
    return {"report": html}
