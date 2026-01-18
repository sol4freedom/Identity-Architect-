from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime
import traceback
import base64

# --- IMPORTS ---
from geopy.geocoders import Nominatim
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ==========================================
# 1. LOGIC & MATH (MOVED TO TOP FOR SAFETY)
# ==========================================

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
    53: {"name": "The Starter", "story": "Abundance. You are the pressure to begin something new."},
    54: {"name": "The Ambition", "story": "Ascension. You drive the tribe upward seeking success."},
    55: {"name": "The Spirit", "story": "Freedom in emotion."}, 56: {"name": "The Storyteller", "story": "Wandering through myths."},
    57: {"name": "The Intuitive", "story": "Clarity in the now."}, 58: {"name": "The Joy", "story": "Vitality against authority."},
    59: {"name": "The Sexual", "story": "Intimacy breaking barriers."}, 60: {"name": "The Limitation", "story": "Realism grounding magic."},
    61: {"name": "The Mystery", "story": "Sanctity of the unknown."}, 62: {"name": "The Detail", "story": "Precision of language."},
    63: {"name": "The Doubter", "story": "Truth through logic."}, 64: {"name": "The Confusion", "story": "Illumination of the mind."}
}

MEGA_MATRIX = {
    "Aries": {"Sun": "You are a pioneer; bold, independent, and direct.", "Mercury": "Direct, rapid-fire communication.", "Saturn": "Self-reliant discipline.", "Jupiter": "Wealth via bold risks.", "Moon": "Safety in independence.", "Venus": "Passionate, spontaneous love.", "Neptune": "Dreams of heroism.", "Mars": "Explosive, head-first drive.", "Uranus": "Individualistic rebellion.", "Pluto": "Destroying barriers.", "Rising": "Undeniable courage."},
    "Taurus": {"Sun": "You are a builder; grounded, patient, and reliable.", "Mercury": "Deliberate, methodical thinking.", "Saturn": "Building legacy through patience.", "Jupiter": "Compounding assets.", "Moon": "Safety in comfort.", "Venus": "Sensory love and touch.", "Neptune": "Dreams of abundance.", "Mars": "Unstoppable momentum.", "Uranus": "Revolutionizing values.", "Pluto": "Transformation of worth.", "Rising": "Calm reliability."},
    "Gemini": {"Sun": "You are a messenger; curious, adaptable, and witty.", "Mercury": "Brilliant, agile processing.", "Saturn": "Structuring the intellect.", "Jupiter": "Luck via networking.", "Moon": "Safety in conversation.", "Venus": "Mental love and wit.", "Neptune": "Telepathic connection.", "Mars": "Versatile, scattered drive.", "Uranus": "Disrupting narratives.", "Pluto": "Psychological reprogramming.", "Rising": "Youthful curiosity."},
    "Cancer": {"Sun": "You are a nurturer; intuitive, protective, and feeling.", "Mercury": "Intuitive, memory-based speech.", "Saturn": "Responsibility to the clan.", "Jupiter": "Wealth via real estate.", "Moon": "Safety in a shell.", "Venus": "Caretaking love.", "Neptune": "Dreams of the perfect home.", "Mars": "Defensive protection.", "Uranus": "Revolutionizing family.", "Pluto": "Ancestral healing.", "Rising": "Gentle, receptive aura."},
    "Leo": {"Sun": "You are a star; creative, generous, and radiant.", "Mercury": "Dramatic storytelling.", "Saturn": "Disciplined creativity.", "Jupiter": "Luck via visibility.", "Moon": "Safety in appreciation.", "Venus": "Grand, performative romance.", "Neptune": "Dreams of fame.", "Mars": "Drive fueled by honor.", "Uranus": "Disrupting the ego.", "Pluto": "Rebirth of identity.", "Rising": "Warm charisma."},
    "Virgo": {"Sun": "You are a healer; analytical, practical, and precise.", "Mercury": "Precise, analytical logic.", "Saturn": "Mastery of craft.", "Jupiter": "Expansion via details.", "Moon": "Safety in routine.", "Venus": "Devoted, practical love.", "Neptune": "Perfect healing.", "Mars": "Efficient action.", "Uranus": "Revolutionizing work.", "Pluto": "Deep purification.", "Rising": "Modest and sharp."},
    "Libra": {"Sun": "You are a diplomat; charming, fair, and balanced.", "Mercury": "Diplomatic negotiation.", "Saturn": "Structuring contracts.", "Jupiter": "Wealth via partnerships.", "Moon": "Safety in harmony.", "Venus": "Aesthetic love.", "Neptune": "Dreams of the soulmate.", "Mars": "Strategic alliances.", "Uranus": "Disrupting norms.", "Pluto": "Transformation via mirroring.", "Rising": "Graceful intelligence."},
    "Scorpio": {"Sun": "You are a mystic; intense, passionate, and transformative.", "Mercury": "Detective mind.", "Saturn": "Mastery of self-control.", "Jupiter": "Power via research.", "Moon": "Safety in deep trust.", "Venus": "Soul-merging fusion.", "Neptune": "Dreams of mysteries.", "Mars": "Relentless will.", "Uranus": "Disrupting taboos.", "Pluto": "Total metamorphosis.", "Rising": "Magnetic intensity."},
    "Sagittarius": {"Sun": "You are an explorer; optimistic, adventurous, and wise.", "Mercury": "Broad-minded philosophy.", "Saturn": "Structuring belief.", "Jupiter": "Luck via travel.", "Moon": "Safety in freedom.", "Venus": "Adventurous love.", "Neptune": "Dreams of nirvana.", "Mars": "Crusading for a cause.", "Uranus": "Disrupting dogma.", "Pluto": "Death of old beliefs.", "Rising": "Jovial optimism."},
    "Capricorn": {"Sun": "You are a boss; ambitious, disciplined, and strategic.", "Mercury": "Pragmatic thinking.", "Saturn": "Building institutions.", "Jupiter": "Success via career.", "Moon": "Safety in control.", "Venus": "Serious commitment.", "Neptune": "Spiritual authority.", "Mars": "Disciplined drive.", "Uranus": "Disrupting government.", "Pluto": "Exposing corruption.", "Rising": "Authoritative capability."},
    "Aquarius": {"Sun": "You are a visionary; original, independent, and humanitarian.", "Mercury": "Genius innovation.", "Saturn": "Structuring the future.", "Jupiter": "Luck via networks.", "Moon": "Safety in detachment.", "Venus": "Unconventional love.", "Neptune": "Dreams of utopia.", "Mars": "Rebellious drive.", "Uranus": "Awakening the collective.", "Pluto": "Power to the people.", "Rising": "Unique brilliance."},
    "Pisces": {"Sun": "You are a dreamer; compassionate, artistic, and spiritual.", "Mercury": "Poetic thinking.", "Saturn": "Form to chaos.", "Jupiter": "Compassionate expansion.", "Moon": "Safety in solitude.", "Venus": "Spiritual love.", "Neptune": "Dissolving into oneness.", "Mars": "Fluid adaptability.", "Uranus": "Disrupting reality.", "Pluto": "Soul transformation.", "Rising": "Dreamy empathy."}
}

NUMEROLOGY_LORE = {
    1: {"name": "The Pioneer", "desc": "Leading with independence."}, 2: {"name": "The Diplomat", "desc": "Thriving on partnership."},
    3: {"name": "The Creator", "desc": "Expressing joy and optimism."}, 4: {"name": "The Builder", "desc": "Building stability through work."},
    5: {"name": "The Adventurer", "desc": "Seeking freedom and change."}, 6: {"name": "The Nurturer", "desc": "Focusing on home and responsibility."},
    7: {"name": "The Seeker", "desc": "Searching for deep truth."}, 8: {"name": "The Powerhouse", "desc": "Mastering abundance and success."},
    9: {"name": "The Humanist", "desc": "Serving humanity."}, 11: {"name": "The Illuminator", "desc": "Channeling intuition."},
    22: {"name": "The Master Builder", "desc": "Turning dreams into reality."}, 33: {"name": "The Master Teacher", "desc": "Uplifting via compassion."}
}

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
    # SAFETY: Strip time from date string if present
    if "T" in date_str: date_str = date_str.split("T")[0]
    
    digits = [int(d) for d in date_str if d.isdigit()]
    total = sum(digits)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    data = NUMEROLOGY_LORE.get(total, {"name": "Mystery", "desc": ""})
    return {"number": total, "name": data["name"], "desc": data["desc"]}

def generate_desc(planet, sign):
    return MEGA_MATRIX.get(sign, {}).get(planet, f"Energy of {sign}")

# --- 3. SERVER-SIDE PDF GENERATOR ---
def create_pdf_b64(data, lp, hd, keys, objs, rising):
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 15)
            self.cell(0, 10, 'THE INTEGRATED SELF', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # User Info
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 10, f"Prepared for {data.name.upper()}", 0, 1, 'C')
    pdf.ln(5)
    
    # Sections
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(100, 50, 150) # Purple
    pdf.cell(0, 10, f"LIFE PATH: {lp['number']} - {lp['name']}", 0, 1)
    pdf.set_font("Helvetica", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, txt=f"{lp['desc']}")
    pdf.ln(5)
    
    # Cosmic Sig
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set
