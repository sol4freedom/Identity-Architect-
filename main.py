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
    1: "The Primal Leader. You are the arrow that leaves the bow first. Your destiny is to stand alone, conquer self-doubt, and lead the tribe into a new era. You are not here to follow footprints; you are here to make them.",
    2: "The Peacemaker. You are the diplomat of the soul. Your hero's journey is to master the invisible threads that connect people, teaching the world that power lies in cooperation, not dominance.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy. Your destiny is to lift the heaviness of the world using your words, art, and radiant optimism to remind humanity that life is meant to be celebrated.",
    4: "The Master Builder. You are the architect of the future. While others dream, you lay the bricks. Your story is one of endurance and legacy. You are here to build a foundation so strong it supports generations.",
    5: "The Freedom Seeker. You are the wind that cannot be caged. Your path is radical adaptability. You are here to break the chains of tradition and show the world what it looks like to be truly, terrifyingly free.",
    6: "The Cosmic Guardian. You are the protector of the hearth. Your journey is to carry the weight of responsibility without breaking, nurturing the tribe until they are strong enough to stand on their own.",
    7: "The Mystic Sage. You are the walker between worlds. Your path is a solitary climb up the mountain of truth. You are here to look past the veil of illusion and bring that wisdom back to the valley.",
    8: "The Sovereign. You are the CEO of the material plane. Your destiny involves the mastery of money, power, and influence. You are here to prove that spiritual abundance can exist in the physical world.",
    9: "The Humanitarian. You are the old soul on one last mission. Your story is one of letting go. You are here to heal the world, leading not by force, but by the overwhelming power of compassion.",
    11: "The Illuminator. You are the lightning rod. You walk the line between genius and madness, channeling high-frequency insights that shock the world awake. You see the dawn before the sun rises.",
    22: "The Master Architect. You are the bridge between heaven and earth. You possess the rare ability to turn the most impossible spiritual visions into concrete reality. You build systems that change history.",
    33: "The Avatar of Love. You are the teacher of teachers. Your path is to uplift the vibration of humanity through pure, unadulterated service. You heal the world simply by being present within it."
}

# --- 3. DATA: STRUGGLE (THE DRAGON) ---
STRUGGLE_LORE = {
    "wealth": {
        "title": "The Quest for Abundance",
        "desc": "Your dragon is Scarcity. You feel blocked financially not because you lack skill, but because you are fighting against your own energy flow. Your chart reveals that abundance is a frequency, not a number. When you align your work with your Jupiter placement, you stop chasing the gold and become the magnet that attracts it."
    },
    "relationship": {
        "title": "The Quest for Connection",
        "desc": "Your dragon is Disharmony. The friction you feel is a signal that you are trying to read from a script that wasn't written for you. Your Venus placement reveals your true love language. Your quest is to stop contorting yourself to fit others and instead stand firmly in your own magnetic design."
    },
    "purpose": {
        "title": "The Quest for Meaning",
        "desc": "Your dragon is The Void. You feel lost because you are looking for a 'destination' on a map that doesn't exist. Purpose is not a job; it is a geometry. Your North Node and Sun Archetype define your unique frequency. Stop 'doing' and start 'being'—the path will form beneath your feet."
    },
    "health": {
        "title": "The Quest for Vitality",
        "desc": "Your dragon is Exhaustion. Your body is the hardware for your consciousness, and it is overheating because you are running software that contradicts your design. Your Saturn placement holds the key to your boundaries. Your quest is to surrender to your own internal rhythm; rest is a sacred act of power."
    },
    "general": {
        "title": "The Quest for Alignment",
        "desc": "Your dragon is Confusion. You feel adrift because you are a unique design trying to function in a standardized world. You are not standard. Your Rising Sign and Orientation hold the compass you need. Your quest is to return to your core strategy, trusting your internal navigation."
    }
}

# --- 4. DATA: ORIENTATION (THE AVATAR) ---
LINE_LORE = {
    1: {"title": "The Investigator", "desc": "The Foundation Builder. Like a master detective, you act only when you understand the ground beneath your feet. Certainty is your superpower. You build confidence through deep study and research."},
    2: {"title": "The Natural", "desc": "The Reluctant Hero. You possess innate gifts that you never had to study for—you are simply 'good at it.' You wait in your hermitage until the right person calls you out to save the day."},
    3: {"title": "The Experimenter", "desc": "The Fearless Explorer. You learn by bumping into the walls of life. For you, there are no mistakes, only discoveries. You are the scientist of the human experience."},
    4: {"title": "The Networker", "desc": "The Tribal Weaver. You are the heart of the community. Your power lies in your connections. Your greatest opportunities will never come from strangers, but from the web of friends you nurture."},
    5: {"title": "The Fixer", "desc": "The General. Strangers project their hopes onto you, seeing you as the savior. Your superpower is practical, universal solutions. You arrive, you fix the problem, and you vanish."},
    6: {"title": "The Role Model", "desc": "The Sage on the Mountain. Your life is a three-act play: the reckless experimenter (youth), the observer on the roof (mid-life), and finally, the wise example of authenticity (maturity)."}
}

# --- 5. DATA: SIGNS (THE STARS) ---
SIGN_LORE = {
    "Aries": "The Warrior. You are the spark that starts the fire. Driven by raw instinct and courage, you are here to initiate the new cycle.",
    "Taurus": "The Builder. You are the earth itself. Patient, sensual, and unmovable, you build the structures that last for generations.",
    "Gemini": "The Messenger. You are the wind. Your mind is a kaleidoscope of connections, weaving stories and ideas that keep the world moving.",
    "Cancer": "The Protector. You are the tide. Deeply intuitive and fiercely loyal, you build the shell that protects the vulnerable heart of the tribe.",
    "Leo": "The Radiant. You are the sun. You do not just enter a room; you warm it. Your creativity is the life-force that reminds others of their own light.",
    "Virgo": "The Alchemist. You are the perfectionist. You see the flaw only because you love the potential. You serve the world by refining it into gold.",
    "Libra": "The Diplomat. You are the scales. You exist in the delicate balance between self and other, constantly adjusting the energy to create harmony.",
    "Scorpio": "The Sorcerer. You are the depths. Unafraid of the dark, you dive into the mysteries of birth, death, and rebirth to find the truth.",
    "Sagittarius": "The Philosopher. You are the arrow. Driven by a hunger for truth and adventure, you expand the horizons of what is possible.",
    "Capricorn": "The Architect. You are the mountain peak. Driven by ambition and legacy, you climb the hard path to build an empire that outlasts you.",
    "Aquarius": "The Revolutionary. You are the lightning bolt. You see the future before it arrives, breaking old structures to liberate the collective.",
    "Pisces": "The Mystic. You are the ocean. Dissolving boundaries, you dream the collective dream, touching the divine and bringing it down to earth."
}

# --- 6. DATA: ARCHETYPES (THE SUPERPOWERS) ---
KEY_LORE = {
    1: {"name": "The Creator", "story": "In the void, there was nothing. Then, you arrived. You are the primal spark of creativity, here to birth something entirely new into the universe."},
    2: {"name": "The Receptive", "story": "You are the cosmic womb. You provide the direction and the blueprint that guides raw, chaotic energy into beautiful form."},
    3: {"name": "The Innovator", "story": "Order is stagnant. You are the necessary chaos. You break the established rules so that life can mutate and evolve into something better."},
    4: {"name": "The Logic Master", "story": "The world is full of doubt. You bring the formula. Your superpower is providing the logic and patterns that calm the anxiety of
