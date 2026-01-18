from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Union
import datetime
import traceback
import base64

# --- IMPORTS ---
from geopy.geocoders import Nominatim
# Lazy loading applied later for heavy libs (TimezoneFinder, FPDF)
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from fpdf import FPDF

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ==========================================
# 1. LOGIC & MATH
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
    23: {"name": "The Assimilator", "story": "Simplicity from
