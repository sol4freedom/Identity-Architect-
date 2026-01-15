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

# --- NOTE: Backend configuration removed to prevent ImportErrors.
# We rely on specific IDs list to prevent engine crashes.

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GENE KEYS DATA ---
RAVE_ORDER = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 
    62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 
    1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 
    37, 63, 22, 36
]

# --- THE 64 ARCHETYPES (THE TRANSLATOR) ---
KEY_NAMES = {
    1: "The Creator", 2: "The Receptive", 3: "The Innovator", 4: "The Logic Master",
    5: "The Fixer", 6: "The Peacemaker", 7: "The Leader", 8: "The Stylist",
    9: "The Focuser", 10: "The Self", 11: "The Idealist", 12: "The Articulate",
    13: "The Listener", 14: "The Power House", 15: "The Humanist", 16: "The Master",
    17: "The Opinion", 18: "The Improver", 19: "The Sensitive", 20: "The Now",
    21: "The Controller", 22: "The Grace", 23: "The Assimilator", 24: "The Rationalizer",
    25: "The Spirit", 26: "The Egoist", 27: "The Nurturer", 28: "The Risk Taker",
    29: "The Yes Man", 30: "The Passion", 31: "The Voice", 32: "The Conservative",
    33: "The Reteller", 34: "The Power", 35: "The Progress", 36: "The Crisis",
    37: "The Family", 38: "The Fighter", 39: "The Provocateur", 40: "The Aloneness",
    41: "The Fantasy", 42: "The Finisher", 43: "The Insight", 44: "The Alert",
    45: "The Gatherer", 46: "The Determination", 47: "The Realization", 48: "The Depth",
    49: "The Catalyst", 50: "The Values", 51: "The Shock", 52: "The Stillness",
    53: "The Starter", 54: "The Ambition", 55: "The Spirit", 56: "The Storyteller",
    57: "The Intuitive", 58: "The Joy", 59: "The Sexual", 60: "The Limitation",
    61: "The Mystery", 62: "The Detail", 63: "The Doubter", 64: "The Confusion"
}

def get_gene_key_name(degree):
    if degree is None: return "Unknown"
    index = int(degree / 5.625)
    if index >= 64: index = 0
    key_number = RAVE_ORDER[index]
    return KEY_NAMES.get(key_number, f"Archetype {key_number}")

# --- PLANET ARCHETYPES ---
INTERPRETATIONS = {
    "Aries": "The Pioneer", "Taurus": "The Builder", "Gemini": "The Messenger",
    "Cancer": "The Nurturer", "Leo": "The Creator", "Virgo": "The Editor",
