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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- DATA LIBRARIES ---
CITY_DB = {
    "minneapolis": (44.9778, -93.2650, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "sao paulo": (-23.5558, -46.6396, "America/Sao_Paulo"),
    "ashland": (42.1946, -122.7095, "America/Los_Angeles"),
    "los angeles": (34.0522, -118.2437, "America/Los_Angeles")
}

LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master the invisible threads that connect people.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world.",
    4: "The Master Builder. You are the architect of the future. While others dream, you lay the bricks.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money, power, and influence.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness.",
    22: "The Master Architect. You are the bridge between heaven and earth. You possess the rare ability to turn visions into reality.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. You feel blocked financially not because you lack skill, but because you are fighting against your own energy flow. Wealth is a frequency. Align with your Jupiter sign."),
    "relationship": ("The Quest for Connection", "Disharmony. The friction is a signal you are using a script not written for you. Honor your Venus placement to magnetize your tribe."),
    "purpose": ("The Quest for Meaning", "The Void. You feel lost because you are looking for a destination, not a frequency. Your North Node defines your signal. Stop doing and start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Your body is the hardware for your consciousness, and it is overheating. Your Saturn placement holds your boundaries. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. You feel adrift because you are a unique design in a standardized world. Your Rising Sign is your compass. Return to your core strategy.")
}

LINE_LORE = {
    1: "The Investigator (Foundation Builder)",
    2: "The Natural (Reluctant Hero)",
    3: "The Experimenter (Fearless Explorer)",
    4: "The Networker (Tribal Weaver)",
    5: "The Fixer (The General)",
    6: "The Role Model (The Sage)"
}

SIGN_LORE = {
    "Aries": "The Warrior.", "Taurus": "The Builder.", "Gemini": "The Messenger.",
    "Cancer": "The Protector.", "Leo": "The Radiant.", "Virgo": "The Alchemist.",
    "Libra": "The Diplomat.", "Scorpio": "The Sorcerer.", "Sagittarius": "The Philosopher.",
    "Capricorn": "The Architect.", "Aquarius": "The Revolutionary.", "Pisces": "The Mystic."
}

KEY_LORE = {
    1: "The Creator", 2: "The Receptive", 3: "The Innovator", 4: "The Logic Master",
    5: "The Fixer", 6: "The Peacemaker", 7: "The Leader", 8: "The Stylist",
    9: "The Focuser", 10: "The Self", 11: "The Idealist", 12: "The Articulate",
    13: "The Listener", 14: "The Power House", 15: "The Humanist", 16: "The Master",
    17: "The Opinion", 18: "The Improver", 19: "The Sensitive", 20: "The Now",
    21: "The Controller", 22: "The Grace", 23: "The Assimilator", 24: "The Rationalizer",
    25: "The Spirit", 26: "The Egoist", 27: "The Nurturer", 28: "The Risk Taker",
    29: "The Devoted", 30: "The Passion", 31: "The Voice", 32: "The Conservative",
    33: "The Reteller", 34: "The Power", 35: "The Progress", 36: "The Crisis",
    37: "The Family", 38: "The Fighter", 39: "The Provocateur", 40: "The Aloneness",
    41: "The Fantasy", 42: "The Finisher", 43: "The Insight", 44: "The Alert",
    45: "The Gatherer", 46: "The Determination", 47: "The Realization", 48: "The Depth",
    49: "The Catalyst", 50: "The Values", 51: "The Shock", 52: "The Stillness",
    53: "The Starter", 54: "The Ambition", 55: "The Spirit", 56: "The Storyteller",
    57: "The Intuitive", 58: "The Joy", 59: "The Sexual", 60: "The Limitation",
    61: "The Mystery", 62: "The Detail", 63: "The Doubter", 64: "The Confusion"
}

# --- HELPER FUNCTIONS ---
def safe_get_date(date_input):
    if not date_input: return None
    s = str(date_input).strip()
    if "T" in s: s = s.split("T")[0]
    return s

def clean_time(t):
    if not t: return "12:00"
    s = str(t).upper().strip()
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if "PM" in s and h < 12: h += 12
        if "AM" in s and h == 12: h = 0
        return f"{h:02d}:{mn:02d}"
    return "12:00"

def get_gate(d):
    if d is None: return 1
    # Simple mathematical approximation for Gates (Standard Human Design Wheel)
    return {0:25, 1:17, 2:21, 3:51, 4:42, 5:3, 6:27, 7:24, 8:2, 9:23, 10:8, 11:20, 12:16, 13:35, 14:45, 15:12, 16:15, 17:52, 18:39, 19:53, 20:62, 21:56, 22:31, 23:33, 24:7, 25:4, 26:29, 27:59, 28:40, 29:64, 30:47, 31:6, 32:46, 33:18, 34:48, 35:57, 36:32, 37:50, 38:28, 39:44, 40:1, 41:43, 42:14, 43:34, 44:9, 45:5, 46:26, 47:11, 48:10, 49:58, 50:38, 51:54, 52:61, 53:60, 54:41, 55:19, 56:13, 57:49, 58:30, 59:55, 60:37, 61:63, 62:22, 63:36}.get(int((d%360)/5.625), 1)

def resolve_loc(c):
    # 1. Try Dictionary Match
    for k in CITY_DB:
        if k in str(c).lower(): return CITY_DB[k]
    
    # 2. Real Geocoding
    try:
        g = Nominatim(user_agent="ia_v99_final")
        l = g.geocode(c)
        if l:
            from timezonefinder import TimezoneFinder
            return l.latitude, l.longitude, TimezoneFinder().timezone_at(lng=l.longitude, lat=l.latitude) or "UTC"
    except: pass
    
    # 3. Fallback
    return 51.50, -0.12, "Europe/London"

def get_tz(d, t, z):
    try:
        dt = datetime.datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
        return pytz.timezone(z).utcoffset(dt).total_seconds() / 3600.0
    except: return 0.0

# --- THE EPIC STORY ENGINE ---
def gen_chapters(name, chart, orient, lp, struggle):
    sun, moon, ris = chart['Sun'], chart['Moon'], chart['Rising']
    s_lore = SIGN_LORE.get(sun['Sign'], "The Hero")
    m_lore = SIGN_LORE.get(moon['Sign'], "The Soul")
    r_lore = SIGN_LORE.get(ris['Sign'], "The Mask")
    
    gate_name = KEY_LORE.get(sun['Gate'], "Energy")
    dragon, d_desc = struggle[0].replace("The Quest for ", ""), struggle[1]
    
    c1 = f"It is said that before a soul enters the world, it chooses a specific geometry of energy. For you, {name}, that geometry began with the **Sun in {sun['Sign']}**. This is not merely a zodiac sign; it is your fuel source. As **{s_lore}**, you are designed to burn with a specific intensity. However, raw energy requires a vessel. To navigate the physical plane, you adopted the mask of the **{ris['Sign']} Rising**. To the outside world, you appear as **{r_lore}**. This is your armor, your style, and your first line of defense. The tension between your inner {sun['Sign']} fire and your outer {ris['Sign']} shield is the primary dynamic of your origin story."
    c2 = f"But a warrior is nothing without a reason to fight. Beneath the armor lies a secret engine: your **Moon in {moon['Sign']}**. While the world sees your actions, only you feel the pull of **{m_lore}**. This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. It governs your emotional tides and your deepest needs. Ignoring this voice is what leads to burnout and exhaustion; honoring it is the secret to your endless regeneration and emotional power."
    c3 = f"Every hero needs a road to walk. Yours is the **Path of the {lp}**. This is not a random wander; it is a destiny defined as: **{LIFE_PATH_LORE.get(lp, '')}** The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, and at times it will feel lonely, but the view from the top is the purpose you have been searching for. You are here to master this specific lesson."
    c4 = f"To aid you on this path, you were gifted a specific weapon—a superpower woven into your DNA. In the language of the Archetypes, you carry the energy of **Archetype {sun['Gate']}: {gate_name}**. This is not a skill you learned in school; it is a frequency you emit naturally. When you trust this power, doors open without force. It is the sword in your hand. When you try to be someone else, you dull this blade. Your task is to wield it with precision."
    c5 = f"But power without control is dangerous. Your operating manual is defined by your Orientation: **{orient}**. You are not designed to move like everyone else. Your specific strategy requires you to honor your
