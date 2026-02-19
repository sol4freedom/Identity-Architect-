import sys, base64, datetime, json, logging, re, io
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import pytz

# --- REPORTLAB PDF ENGINE ---
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- LORE DATABASES ---
CITY_DB = {
    "minneapolis": (44.97, -93.26, "America/Chicago"), "london": (51.50, -0.12, "Europe/London"),
    "new york": (40.71, -74.00, "America/New_York"), "ashland": (42.19, -122.70, "America/Los_Angeles"),
    "los angeles": (34.05, -118.24, "America/Los_Angeles"), "sao paulo": (-23.55, -46.63, "America/Sao_Paulo")
}

LIFE_PATH_LORE = {
    1: "The Primal Leader. You are the arrow that leaves the bow first.",
    2: "The Peacemaker. You are the diplomat of the soul.",
    3: "The Creative Spark. You are the voice of the universe expressing its joy.",
    4: "The Master Builder. You are the architect of the future.",
    5: "The Freedom Seeker. You are the wind that cannot be caged.",
    6: "The Cosmic Guardian. You are the protector of the hearth.",
    7: "The Mystic Sage. You are the walker between worlds.",
    8: "The Sovereign. You are the CEO of the material plane.",
    9: "The Humanitarian. You are the old soul on one last mission.",
    11: "The Illuminator. You are the lightning rod.",
    22: "The Master Architect. You are the bridge between heaven and earth.",
    33: "The Avatar of Love. You are the teacher of teachers."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "Scarcity. Wealth is a frequency. Align with your Jupiter sign."),
    "relationship": ("The Quest for Connection", "Disharmony. Honor your Venus placement to magnetize your tribe."),
    "purpose": ("The Quest for Meaning", "The Void. Your North Node defines your signal. Stop doing and start being."),
    "health": ("The Quest for Vitality", "Exhaustion. Your Saturn placement holds your boundaries. Surrender to rhythm."),
    "general": ("The Quest for Alignment", "Confusion. Your Rising Sign is your compass. Return to your core strategy.")
}

LINE_LORE = {1:"The Investigator", 2:"The Natural", 3:"The Experimenter", 4:"The Networker", 5:"The Fixer", 6:"The Role Model"}

SIGN_LORE = {
    "Aries": "The Warrior", "Taurus": "The Builder", "Gemini": "The Messenger", "Cancer": "The Protector",
    "Leo": "The Radiant", "Virgo": "The Alchemist", "Libra": "The Diplomat", "Scorpio": "The Sorcerer",
    "Sagittarius": "The Philosopher", "Capricorn": "The Architect", "Aquarius": "The Revolutionary", "Pisces": "The Mystic"
}

SUN_LORE = {
    "Aries": "Your core essence is the primal spark of initiation. You are fueled by the raw, unbridled energy of beginnings. Your conscious purpose is not to manage what already exists, but to fearlessly carve new paths where there are none. You shine brightest when you are taking independent action, trusting your immediate instincts, and leading the charge into the unknown.",
    "Taurus": "Your core essence is the profound power of stabilization. You are fueled by the creation of lasting, tangible value. Your conscious purpose is to take the raw sparks of life and anchor them into physical reality through slow, deliberate, and masterful effort. You shine most brilliantly when you are deeply grounded, cultivating beauty, and refusing to be rushed by a chaotic world.",
    "Gemini": "Your core essence is the relentless pursuit of cosmic data. You are fueled by curiosity, mental agility, and the cross-pollination of ideas. Your conscious purpose is to act as the universe's translator—gathering diverse fragments of information and weaving them into new, brilliant perspectives. You shine when you are free to explore, question, and change your mind.",
    "Cancer": "Your core essence is the profound mastery of emotional resonance. You are fueled by the creation of sanctuary, both physical and energetic. Your conscious purpose is to fiercely protect the vulnerable and nurture the deep, unseen roots of human connection. You shine most powerfully when you trust your oceanic intuition and lead from a space of radical empathy.",
    "Leo": "Your core essence is the profound frequency of pure, unabashed radiation. You are fueled by radical self-expression, play, and the sheer joy of existence. Your conscious purpose is not to shrink to make others comfortable, but to burn so brightly and authentically that you naturally warm and inspire everyone in your orbit. You shine your brightest when you lead directly from the heart.",
    "Virgo": "Your core essence is the pursuit of ultimate refinement. You are fueled by the desire to take the chaotic, raw materials of life and distill them into pure, functioning perfection. Your conscious purpose is devotion through extreme competence. You shine most brilliantly when you are serving the world by offering your brilliant, analytical mind to heal, organize, and elevate the systems around you.",
    "Libra": "Your core essence is the pursuit of ultimate equilibrium and aesthetic truth. You are fueled by the creation of harmony, both in your physical environments and your relationships. Your conscious purpose is to act as the cosmic bridge—bringing opposing forces together to find the exquisite middle ground. You shine most powerfully when you are advocating for fairness, designing beauty, and uniting people.",
    "Scorpio": "Your core essence is the mastery of the underworld. You are fueled by intensity, absolute truth, and the courage to dive into the shadows where others refuse to look. Your conscious purpose is to catalyze profound rebirth—destroying the illusions of the surface world to reveal the raw power underneath. You shine most brilliantly when you are navigating the depths of human psychology, intimacy, and profound transformation.",
    "Sagittarius": "Your core essence is the relentless pursuit of ultimate truth and expansion. You are fueled by freedom, big-picture meaning, and the sheer adventure of the unknown. Your conscious purpose is to synthesize your vast, raw, lived experiences into profound wisdom. You shine most brilliantly when you refuse to be confined by dogma, choosing instead to act as a visionary guide for the collective.",
    "Capricorn": "Your core essence is the absolute mastery of the material realm. You are fueled by integrity, discipline, and the profound desire to build structures that outlast your lifetime. Your conscious purpose is not simply to climb the world's ladders, but to become the ultimate, sovereign authority of your own life. You shine your brightest when you are transforming abstract visions into enduring, tangible reality.",
    "Aquarius": "Your core essence is the frequency of collective mutation. You are fueled by innovation, rebellion, and a radical commitment to authenticity. Your conscious purpose is to stand outside the system, observe its flaws, and shatter outdated paradigms to make room for humanity's future. You shine most powerfully when you stop trying to fit in and instead fully embrace your role as a cosmic disruptor.",
    "Pisces": "Your core essence is the dissolution of all boundaries. You are fueled by universal consciousness, profound compassion, and the invisible threads that connect all living things. Your conscious purpose is to act as a conduit for the divine, translating the unseen world into art, healing, and empathy. You shine your brightest when you surrender the need for logical control and trust the vast currents of your intuition."
}

MOON_LORE = {
    "Aries": "Your inner world is a blazing fire. You process emotions quickly, physically, and directly. For you, emotional safety is found in total independence and the freedom to act on your feelings without restriction. When you feel overwhelmed or unsafe, you need physical movement to burn off the stagnant energy, transforming your emotional turbulence back into pure life-force.",
    "Taurus": "Your emotional landscape requires deep, unshakeable roots. You find emotional safety in predictability, physical comfort, and the sensory experiences of the present moment. You process your feelings slowly; when life becomes chaotic, your absolute best medicine is returning to the simple, rhythmic cadences of nature and your physical body.",
    "Gemini": "Your emotional world is intricately tied to your nervous system and your mind. You do not just feel your emotions; you need to conceptualize and verbalize them. Emotional safety for you means being deeply understood. When you feel overwhelmed, your greatest release is not found in silence, but in dialogue, journaling, or expressing the rapid currents of your inner state.",
    "Cancer": "The Moon is your absolute domain. Your inner world is incredibly vast, sensitive, and profoundly psychic. You absorb the emotional weather of your environment like a sponge. True emotional safety requires you to build a fiercely protected inner sanctum. Your healing comes from honoring the natural, cyclical ebbing and flowing of your emotional tides without judgment.",
    "Leo": "Your emotional landscape requires warmth, validation, and a stage to be witnessed. You do not just feel your emotions; you experience them as epic narratives. Emotional safety for you means feeling truly seen, celebrated, and adored by your inner circle. When you feel disconnected or low, your greatest medicine is creative expression—taking your internal heavy feelings and transforming them into art, movement, or dramatic release.",
    "Virgo": "Your emotional world is intimately connected to your physical nervous system and your daily rituals. For you, emotional safety is found in order, cleanliness, and predictability. When your internal world feels chaotic, talking about it is rarely enough; your truest emotional medicine is somatic. Organizing your physical space, returning to a pure diet, or engaging in a grounded physical routine is how you process and release heavy emotions.",
    "Libra": "Your emotional landscape requires deep, relational mirroring. You find emotional safety in peaceful, beautiful, and conflict-free environments. Because you are so sensitive to the energetic discord of others, you often process your own emotions by talking things through with a trusted partner. When you feel off-balance, your medicine is aesthetic and relational: surrounding yourself with high-frequency art, music, or a deeply harmonizing conversation.",
    "Scorpio": "Your inner world is a deep, fiercely guarded ocean. You experience emotions with an intensity that can feel consuming, and because of this, absolute privacy and absolute loyalty are your requirements for emotional safety. You do not process your feelings loudly or publicly; your medicine is found in private, intense emotional alchemy. You heal by going into the dark, feeling the absolute bottom of the emotion, and resurrecting yourself.",
    "Sagittarius": "Your emotional landscape is a wide-open horizon. You absolutely cannot heal in a cage. For you, emotional safety equates to total spatial and philosophical freedom. When you feel emotionally heavy or stagnant, your ultimate medicine is movement—whether that means physically traveling to a new environment, or diving into a paradigm-shifting book that completely alters your perspective.",
    "Capricorn": "Your inner world is built on a foundation of profound responsibility. You find emotional safety in competence, boundaries, and achieving what you set out to do. Because you are naturally wired to carry the weight of the world, your deepest emotional wounds often stem from feeling unsupported. Your ultimate healing is the somatic release of pressure—allowing yourself to rest, be held, and drop the armor of having to hold it all together.",
    "Aquarius": "Your emotional world is highly complex, operating almost like an electrical grid. You find emotional safety in intellectual objectivity and the space to be completely, weirdly yourself. You do not process emotions by drowning in them; you process them by stepping back, observing them logically, and understanding their root cause. Healing for you means radical self-acceptance of your own alien nature.",
    "Pisces": "Your emotional landscape is an infinite, highly porous ocean. You do not just feel your own feelings; you absorb the energetic grief, joy, and frequency of the entire world. Because of this, emotional safety requires fierce, non-negotiable boundaries. When you are overwhelmed, your only true medicine is absolute retreat—withdrawing from the world to drain out the energies of others and return to source."
}

RISING_LORE = {
    "Aries": "You meet the universe head-on. The energetic mask you wear is fierce, direct, and completely unapologetic. Your aura cuts through stagnation like a blade, forcing the people and environments around you to wake up and take action. You are designed to make an immediate, electrifying first impression.",
    "Taurus": "You meet the world as the ultimate anchor. Your outward vessel projects a calm, stoic, and incredibly reliable frequency. People instantly feel a sense of grounding when they enter your aura. You do not need to demand attention; your sheer, immovable presence naturally commands the space.",
    "Gemini": "You meet the world with electric adaptability. Your outward mask is highly perceptive, quick-witted, and constantly absorbing the subtle data of your environment. You have the energetic ability to completely mirror the frequency of whoever you are speaking to, allowing you to seamlessly navigate incredibly diverse social landscapes.",
    "Cancer": "You navigate the world through feeling rather than logic. Your aura is a protective shell, instinctively reading the safety of a room before you ever truly reveal yourself. Once you determine a space is safe, your vessel radiates an immense, warming maternal energy that naturally invites people to drop their armor and exhale.",
    "Leo": "You meet the universe with undeniable gravity. The energetic mask you wear is regal, generous, and immensely magnetic. You do not need to fight for attention when you enter a room; your sheer presence naturally draws the spotlight. People are instinctively drawn to your vessel because it projects an aura of immense vitality, courage, and protective warmth.",
    "Virgo": "You navigate the world through a lens of sharp, discerning observation. Your outward mask is highly capable, meticulously put-together, and deeply analytical. Before you fully engage with an environment, your aura scans the room, immediately identifying exactly what is out of place and what can be improved. You project an initial frequency of quiet, observant mastery.",
    "Libra": "You meet the world with effortless grace. Your outward vessel is incredibly disarming, charming, and aesthetically attuned. You have the energetic capacity to walk into a room of tension and instantly soften the edges of everyone there. Your mask is designed to make others feel comfortable, seen, and immediately at ease in your presence.",
    "Scorpio": "You meet the universe as an impenetrable, magnetic force. Your energetic mask is quiet, intense, and profoundly observant. When you enter a room, your aura naturally pierces through the superficial layers of everyone there; you immediately see people's hidden motives. You project a frequency of immense, quiet power that naturally commands respect and fascination.",
    "Sagittarius": "You meet the world with an unbridled, visionary fire. The energetic mask you wear is incredibly expansive, optimistic, and unapologetically blunt. Your vessel does not do 'small talk'; your aura naturally invites people to immediately drop into conversations about meaning, purpose, and the grand design. You project a frequency that makes the world feel endlessly full of possibility.",
    "Capricorn": "You navigate the world with commanding gravity. Your outward mask projects immense capability, ancient wisdom, and quiet authority. Before you even speak, people instinctively trust your vessel to handle the heavy lifting. You have the energetic ability to walk into a room of total chaos and instantly ground the space simply by standing firmly in your own power.",
    "Aquarius": "You meet the universe as an electric shock to the status quo. Your energetic mask is highly observant, unpredictable, and slightly detached. Your aura does not blend; it constantly hums with a futuristic frequency. People are drawn to your vessel because it implicitly gives them permission to drop their own societal conditioning and be exactly who they are.",
    "Pisces": "You navigate the world through a fluid, dreamlike frequency. Your outward mask is deeply compassionate, reflective, and infinitely adaptable. You have a shape-shifting aura; people tend to see whatever they most need to see when they look at you. Your vessel naturally invites others to drop their earthly guards and experience a moment of true, soul-level recognition."
}

KEY_LORE = {
    1: "The Creator. You hold the primal frequency of pure self-expression. Your gift is not merely about making art; it is the raw, catalytic power to bring the unmanifested into reality just by being yourself.<br/><br/>When you are out of alignment, this energy turns inward, creating restlessness or a feeling of being misunderstood. When mastered, you realize that your entire life is your canvas, and your truest creation is your authentic self.",
    2: "The Receptive. You are the ultimate anchor for universal flow. While others push and force their will upon the world, your power lies in absolute magnetic alignment. You have an innate inner compass that knows exactly where you need to be and when.<br/><br/>Your challenge is trusting the silence. When you surrender the need to control the outcome and instead drop deeply into your own state of being, the right opportunities, people, and resources naturally gravitate to your field.",
    3: "The Innovator. You are the sacred agent of mutation and change. Your energy is designed to step into chaos, break down stagnant systems, and establish a completely new paradigm. You see the world not for what it is, but for what it is evolving into.<br/><br/>This path can initially feel deeply confusing, as you must wade through the unknown before the new order reveals itself. Trust your unique perspective; your periods of melancholy or confusion are simply the incubation phase before a massive breakthrough.",
    4: "The Logic Master. You possess a brilliant, analytical frequency designed to bring order to mental chaos. Your gift is the ability to see the underlying patterns of reality and formulate solutions that stand the test of time.<br/><br/>When operating out of fear, this energy can become trapped in endless doubt or an obsessive need for absolute certainty. When mastered, you realize that true logic is not about having all the answers, but about asking the right questions and trusting the natural rhythm of understanding.",
    5: "The Fixer. You are deeply attuned to the heartbeat of life and the natural rhythms of the universe. Your true power does not lie in rushing to solve problems, but in your profound capacity for patience and alignment with universal timing.<br/><br/>When forced or impatient, you may feel perpetually out of sync or stuck in destructive, repetitive habits. When you surrender to your natural pacing, you become a stabilizing force, effortlessly untangling chaos simply by grounding yourself in the present moment.",
    6: "The Peacemaker. You carry the profound energetic blueprint of emotional alchemy. You are designed to step into the friction of human relationships and transform conflict into deeper intimacy and mutual understanding.<br/><br/>If you avoid necessary conflict out of a desire to 'keep the peace,' you absorb the toxic energy of your environment. True mastery for you means recognizing that authentic peace is not the absence of storms, but the courage to stand firmly within them and speak your truth.",
    7: "The Leader. You emit a natural frequency of authority and future-oriented direction. People are instinctively drawn to your energy when they are lost, sensing that you hold the compass for the collective journey forward.<br/><br/>When out of alignment, you may try to force your authority or shrink away from the heavy mantle of leadership altogether. True mastery is the realization that you do not need to demand followers; you simply need to walk your authentic path, and the right people will naturally align behind you.",
    8: "The Stylist. You are the embodiment of unique, unrepeatable contribution. Your energy is not meant to blend in; it is designed to disrupt the mundane by expressing your most authentic, individualized self in a way that inspires others.<br/><br/>The shadow of this energy is the fear of being truly seen, leading to imitation or hiding your eccentricities. When you fully embrace your distinct nature, your very existence becomes a masterpiece that implicitly gives others permission to be themselves.",
    9: "The Focuser. You possess the monumental power of applied concentration. Your gift is the ability to take vast, overwhelming visions and anchor them into reality through relentless focus on the microscopic details.<br/><br/>When distracted or overwhelmed by the big picture, your energy scatters into anxious inaction. Your mastery lies in surrendering the need to see the entire staircase; you change the world simply by giving your absolute, unbroken presence to the single step directly in front of you.",
    10: "The Self. You carry the profound frequency of pure self-love and behavior. Your primary purpose is not to 'do' anything specific for others, but to perfectly embody your own authentic nature. By simply being yourself, you show others how to be themselves.<br/><br/>When out of alignment, you may obsess over how you are perceived, leading to deep insecurity or a loss of identity. True mastery occurs when you surrender the need for external validation; your unshakeable self-acceptance becomes the silent medicine the world craves.",
    11: "The Idealist. You are the dreamer who conceptualizes what is possible. Your energy flows through the realm of ideas, constantly seeking harmony, peace, and the light at the end of the tunnel. You see the divine potential in humanity.<br/><br/>Your shadow emerges when you become lost in illusion, expecting the real world to match the perfect pictures in your head. Mastery is the realization that true light can only be known by understanding the dark; you are here to hold the vision of perfection while fiercely loving the world in its imperfection.",
    12: "The Articulate. You possess the rare gift of transformative speech. Your voice carries an energetic weight that can shift the emotional state of a room in a single sentence. You are designed to speak deep, often unspoken truths.<br/><br/>When operating in shadow, you either withhold your voice out of a fear of rejection, or you speak impulsively and cause unintended destruction. Mastery is learning the sacred pause. You must wait for the exact right moment to speak, ensuring your words land as a revelation rather than a disruption.",
    13: "The Listener. You are the ultimate energetic vault. People are naturally drawn to confess their deepest truths, pains, and stories to you, because you hold space with profound, non-judgmental empathy.<br/><br/>If you do not set boundaries, you risk becoming completely weighed down by the heavy emotional baggage of others. True mastery means learning to hear the world's pain without absorbing it into your own body, recognizing that your gift is to witness their truth, not to carry their burden.",
    14: "The Power House. You are a generator of immense, creative life-force energy. When you are aligned with what you love, you possess an almost magical ability to attract wealth, resources, and momentum into your life and the lives of those around you.<br/><br/>When you compromise your energy by doing work you despise, you quickly burn out and feel deeply enslaved to the material world. Your absolute mastery is recognizing that your joy is your currency; you only generate true abundance when you are profoundly passionate about where you are directing your energy.",
    15: "The Humanist. You are designed to experience the absolute extreme spectrums of the human condition. You embody the vastness of life, holding the frequencies of both profound love and immense pain, light and dark, chaos and rhythm.<br/><br/>When you judge your own extremes, you feel broken or chaotic. Mastery is radical acceptance. By refusing to label any part of the human experience as 'wrong,' you become an anchor of profound compassion, showing the world how to embrace the totality of what it means to be alive.",
    16: "The Master. You carry the frequency of deep, unwavering dedication. Your path to mastery is not linear; it is driven by sheer, unbridled enthusiasm. When you find something that ignites your soul, you have the capacity to cultivate world-class skill.<br/><br/>Your shadow is the fear of inadequacy, which can make you jump constantly from one interest to another without ever committing. Mastery requires surrendering to the long, often repetitive process of practice, knowing that true genius takes time to refine.",
    17: "The Opinion. You are designed to see the future logically. Your mind has a brilliant capacity to observe the chaotic patterns of the present and organize them into a clear, structured concept of what needs to happen next.<br/><br/>When out of alignment, your gift degrades into rigid dogma, forcing your opinions on others who did not ask for them. True mastery is understanding that your vision is meant to be an offering, not a demand. You change the world by presenting your profound logic and trusting those who are ready to hear it.",
    18: "The Improver. You possess the eagle-eye of correction. You are energetically wired to walk into any system, pattern, or environment and immediately spot the one thing that is flawed, broken, or out of integrity.<br/><br/>If you direct this critical eye inward, you will tear yourself apart with endless self-judgment. Your mastery lies in recognizing that your gift of correction is a profound act of love meant to be shared with the world, aimed at healing and perfecting the collective, never at destroying yourself.",
    19: "The Sensitive. You possess a profound emotional antenna, designed to feel the unspoken needs, moods, and frequencies of the community around you. You are the energetic barometer of your environment.<br/><br/>When operating in shadow, you over-identify with the pain of others, leading to codependency or emotional burnout. True mastery is realizing that empathy does not mean absorption; you must fiercely guard your own emotional boundaries so you can offer compassion without losing yourself.",
    20: "The Now. You are the absolute embodiment of existential presence. Your gift is not about analyzing the past or predicting the future; it is the sheer, clarifying power of seeing things exactly as they are in this very second.<br/><br/>When you slip into anxiety, it is because your mind has time-traveled to a future that does not exist. Your mastery is acting as a clear, unflinching mirror for the world, grounding everyone around you simply by anchoring yourself entirely in the present tense.",
    21: "The Controller. You are endowed with the formidable ability to manage resources, create material order, and take charge of physical domains. You are the architect of structure in a chaotic world.<br/><br/>Your shadow is the micromanaging fear of losing grip, tightening your hold until you suffocate the very things you are trying to build. Mastery is surrendering the illusion of absolute control; you learn to guide resources with an open hand, trusting the natural flow of abundance.",
    22: "The Grace. You carry the frequency of profound emotional depth and social elegance. You possess the rare ability to express the most intense, turbulent feelings in a way that is beautiful, moving, and deeply human.<br/><br/>If you judge your own emotional waves, you may act out with sudden volatility or shut down entirely out of feeling misunderstood. Mastery is learning to ride your emotional tides without being consumed by them, offering yourself the same radical grace you so easily extend to others.",
    23: "The Assimilator. You are the ultimate translator of the universe. Your mind takes vast, complex, abstract knowing and strips away the unnecessary, distilling it into clear, actionable, paradigm-shifting language.<br/><br/>When out of alignment, you may speak out of turn and feel alienated when people do not understand your sudden insights. Mastery is learning the discipline of the wait; when you hold your brilliant tongue until you are genuinely invited to speak, your words become absolute revelation.",
    24: "The Rationalizer. You are the master of mental review and renewal. Your mind is designed to circle around a mystery, viewing it from every angle until you find the true, undeniable essence at its core.<br/><br/>The shadow of this energy is getting trapped in endless, anxious mental loops, overthinking until you are paralyzed. Mastery is learning to let the mind rest in the void of the unknown, trusting that the answer will naturally click into place when the time is right.",
    25: "The Spirit. You hold the profound frequency of unconditional, universal love. You are designed to walk through life's deepest trials and initiations while keeping your heart radically, vulnerably open.<br/><br/>When wounded, you may feel victimized by the harshness of the world and close yourself off to protect your spirit. Your ultimate mastery is maintaining your spiritual innocence, trusting the divine orchestration of the universe, and loving the world no matter how it scars you.",
    26: "The Egoist. You possess the magnetic power of influence, memory, and a healthy, unashamed ego. Your gift is the ability to pitch ideas, rally the collective, and bend reality through sheer persuasion.<br/><br/>When insecure, this energy devolves into manipulation or boastfulness to mask a lack of self-worth. Mastery is realizing that a strong ego is not a sin; when you use your immense influence to empower and elevate the collective, your ego becomes a sacred tool for the greater good.",
    27: "The Nurturer. You carry the profound energetic blueprint of compassion and preservation. Your aura naturally provides the nourishment, care, and safety required to sustain life and foster deep growth.<br/><br/>The shadow of this frequency is martyrdom—giving to others until you are completely hollowed out and resentful. Mastery is the radical understanding that self-care is the absolute prerequisite for universal care; you can only truly nourish the world when your own cup is overflowing.",
    28: "The Risk Taker. You are the courageous player of the game of life. Your energy is designed to face the darkness, push limits, and find profound meaning through struggle and extreme experiences.<br/><br/>When operating blindly, you may create unnecessary drama or take reckless gambles just to feel alive. True mastery is transforming your fear into wisdom; you learn to take calculated risks not for the thrill of the adrenaline, but for the evolution of your highest purpose.",
    29: "The Devoted. You are the embodiment of deep, enduring commitment. When you say 'yes,' you throw your entire being into the experience, possessing the stamina to persist through the longest cycles of life.<br/><br/>If you commit to things out of obligation, you will drag yourself through profound exhaustion. Your mastery is learning the sacred power of 'no.' When you fiercely protect your energy, your authentic 'yes' retains its immense, world-moving power.",
    30: "The Passion. You are the clinging fire. You experience life through a lens of intense, burning desire and emotional depth, hungering for the raw, unfiltered experience of what it means to be human.<br/><br/>The shadow is becoming entirely consumed by your desires, chasing the next high until you burn out. Mastery is surrendering to the feeling without needing to act on every impulse; you learn to let the fire of your passion warm you rather than destroy you.",
    31: "The Voice. You are a natural, influential leader through the spoken word. You possess the energetic capacity to manifest collective vision into reality simply by articulating the direction forward.<br/><br/>When driven by ego, you may dictate, demand, or speak without ever listening to those you lead. True mastery is recognizing that you are a vessel; your leadership only works when you are authentically voicing the true needs and direction of your community.",
    32: "The Conservative. You hold the instinctual knowing of what truly has value. Your gift is the ability to look at any system, tradition, or business and know exactly what must be preserved to ensure survival and success.<br/><br/>When paralyzed by the fear of failure, you may cling to dead traditions that no longer serve you. Mastery is becoming the dynamic preserver; you learn to fiercely protect the core essence of a thing while allowing its outer form to evolve with the times.",
    33: "The Reteller. You are the keeper of collective memory. Your energy is designed to process intense experiences, retreat into solitude, and then emerge to share the profound wisdom you have extracted from the journey.<br/><br/>The shadow of this frequency is getting stuck in the past or isolating yourself so deeply that you refuse to share your lessons. Mastery is balancing the retreat with the return; you step away to heal and reflect, then step back into the world to enrich us with your story.",
    34: "The Power. You possess a pure, independent, and monumental life-force energy. You have the raw capacity to simply 'do,' remaining entirely self-sufficient and moving mountains through sheer kinetic force.<br/><br/>When out of alignment, you may force outcomes, accidentally bully others with your intensity, or exhaust yourself by doing everything alone. Mastery is acting only in response to what is correct for you, transforming your raw power from forceful pushing into effortless, magnetic empowerment.",
    35: "The Progress. You are the hungry explorer of human consciousness. Your gift is the expansion of the collective through a relentless desire to try everything once, gather the experience, and evolve.<br/><br/>If you lack depth, this turns into chronic boredom, constantly chasing the next superficial thrill to avoid sitting still. Mastery is slowing down enough to extract the deep, lasting wisdom from every fleeting experience, sharing that evolution with the world.",
    36: "The Crisis. You carry the profound emotional depth required to grow through intense turbulence. You are the catalyst for change, designed to navigate the darkest waters and emerge transformed on the other side.<br/><br/>When trapped in the shadow, you may subconsciously create chaos out of boredom or fall into a deep narrative of victimhood. Mastery is riding the waves of crisis with absolute grace, understanding that every single breakdown in your life is simply a breakthrough in disguise.",
    37: "The Family. You are the creator of the hearth. Your frequency naturally fosters community, loyalty, affection, and a deep, warming sense of belonging for everyone lucky enough to enter your aura.<br/><br/>Your shadow emerges when you remain in toxic dynamics simply out of a sense of traditional loyalty or codependency. Mastery is redefining family based on energetic resonance rather than obligation, consciously cultivating an environment of true communal harmony.",
    38: "The Fighter. You possess an unyielding, warrior-like determination. You hold the necessary energetic tension to fight for your individuality, your purpose, and the ultimate meaning of your life.<br/><br/>When you lack a true purpose, you will fight simply for the sake of fighting, pushing people away with sheer stubbornness. Mastery is realizing that your energy is sacred; you learn to lay down your sword over petty things, choosing to only fight the battles that elevate the human spirit.",
    39: "The Provocateur. You are the divine agitator. Your gift is poking at the status quo, intentionally stirring up stagnant energy to catalyze emotional, spiritual, and systemic growth in those around you.<br/><br/>The shadow of this energy is antagonizing others just for the fun of it, causing unnecessary pain or drama. Mastery is using your provocative nature as a precise, compassionate energetic scalpel, intentionally triggering others into their highest alignment.",
    40: "The Aloneness. You embody the immense power of independent work and the absolute necessity of restorative solitude. You are the one who can always be counted on to deliver on your promises.<br/><br/>When out of balance, you may deny your need for others entirely, working yourself to the bone in total isolation. Mastery is fiercely guarding your solitary recharge time without shutting the world out, so you can repeatedly re-enter your community with a full, generous heart.",
    41: "The Fantasy. You are the origin point of all human longing and imagination. Your frequency holds the pure, visionary pressure to dream of a future that does not yet exist, fueling the evolution of the collective.<br/><br/>When operating in shadow, you may get completely lost in daydreams, perpetually dissatisfied with your current reality. Mastery is recognizing that your imagination is a blueprint, not an escape hatch; you learn to ground your visions by taking practical steps to build them in the physical world.",
    42: "The Finisher. You possess the monumental energetic stamina to close cycles. Once you commit your life force to an experience, a project, or a relationship, you naturally carry it all the way through to its ultimate conclusion and harvest the resulting wisdom.<br/><br/>The shadow is remaining tethered to dead cycles simply because you are afraid to let go, dragging out endings until they become toxic. True mastery is the somatic recognition of 'done.' When you gracefully close a chapter that has run its course, you instantly liberate energy for your next great beginning.",
    43: "The Insight. You are the channel for sudden, unpredictable breakthroughs. Your mind operates outside of traditional logic, receiving complete flashes of deep, individualized knowing that can shatter old paradigms.<br/><br/>If you force your insights on people before they are ready, you will be dismissed as eccentric or deaf to the room. Mastery is cultivating the patience to hold your inner knowing in silence until you are explicitly asked; only then does your unique perspective land as sheer genius.",
    44: "The Alert. You are the keeper of cellular memory. You have an instinctual, full-body radar for spotting patterns, instantly recognizing who or what is safe, aligned, and correct based on the unwritten history stored in your bones.<br/><br/>When hijacked by fear, this energy turns into profound paranoia, projecting past failures onto future possibilities. Mastery is clearing the static of old trauma so you can trust your somatic radar completely, effortlessly magnetizing the right people and opportunities into your life.",
    45: "The Gatherer. You hold the natural, magnetic frequency of the sovereign. You are energetically designed to act as the central hub of your community, overseeing resources, educating your tribe, and ensuring collective prosperity.<br/><br/>The shadow of this energy is the hoarding of wealth or demanding loyalty through dominance rather than respect. Your highest mastery is benevolent distribution; you realize that true power lies not in what you keep for yourself, but in how profoundly you elevate and resource the people around you.",
    46: "The Determination. You are the embodiment of serendipity and physical grace. When you are fully surrendered to the present moment, you possess a magical ability to be in exactly the right place at exactly the right time.<br/><br/>When you try to mentally force your path or push past your body’s limits, you stumble, push the wrong doors, and experience deep physical exhaustion. Mastery is dropping entirely into your physical being; by letting your body—not your mind—guide your steps, your life becomes a sequence of perfect, effortless synchronicities.",
    47: "The Realization. You are the alchemist of the past. Your mind is uniquely designed to sift through memories, confusion, and psychological oppression, eventually extracting a profound, organizing truth that brings peace to the collective.<br/><br/>If you turn this immense mental pressure inward, you will drown in anxiety and self-doubt. Mastery is understanding that your mental confusion is not a flaw, but a necessary incubation state. When you stop fighting the pressure, the 'aha' moment naturally arrives to liberate you.",
    48: "The Depth. You are an endless well of natural, unforced wisdom. You carry a frequency that naturally understands the underlying mechanics of life, capable of offering profound solutions to the most complex human struggles.<br/><br/>The shadow of this energy is a crippling fear of inadequacy, convincing yourself that you need 'just one more certification' before you are ready to share your gifts. True mastery is stepping into the arena as you are, trusting that your depth is already infinite and the right answers will rise to the surface the exact moment they are needed.",
    49: "The Catalyst. You are the energetic gatekeeper of the community. You possess the revolutionary power to establish principles, distribute resources, and dictate exactly who is allowed inside your trusted inner circle.<br/><br/>When operating out of emotional reactivity, you may ruthlessly cut people out of your life over minor infractions, isolating yourself in a fortress of rules. Mastery is softening your rigid boundaries with profound compassion, ensuring your principles serve to protect the tribe's harmony rather than simply punishing its flaws.",
    50: "The Values. You are the living cauldron of tribal law. You carry the instinctual, energetic responsibility to maintain the harmony, ethics, and moral foundation of your community, knowing exactly what is corrupt and what is pure.<br/><br/>The shadow is becoming paralyzed by the fear of taking on too much responsibility, leading you to tolerate toxic environments to avoid rocking the boat. Mastery is standing completely firm in your highest values, knowing that your unwavering integrity is the exact medicine required to heal your environment.",
    51: "The Shock. You are the lightning strike of initiation. Your purpose is not to be comfortable; it is to jolt yourself and others out of complacency, initiating profound leaps in consciousness through sudden, unpredictable action.<br/><br/>When acting from the ego, you may create unnecessary chaos or shock people simply to feed your need for attention. Your ultimate mastery is acting as a conduit for spiritual awakening, intentionally using your disruptive energy to shock the world back into a state of love and profound aliveness.",
    52: "The Stillness. You are the unshakable mountain. You possess the profound, passive capacity to sit entirely still, grounding the chaotic energy around you and focusing deeply on the perfection of the present moment.<br/><br/>If you force yourself to move when your body requires rest, your energy scatters into deep physical tension and restlessness. Mastery is fully honoring your requirement to pause. By mastering the art of non-action, your eventual movement becomes immensely concentrated, accurate, and powerful.",
    53: "The Starter. You are the spark of all new cycles. Your frequency is a pure, surging life-force designed to initiate new projects, new relationships, and new chapters of human evolution.<br/><br/>The shadow of this energy is the guilt of never finishing what you start, leading you to force yourself through cycles that drain your soul. Mastery is the radical acceptance that you are the ignition, not the engine. You are here to breathe life into the new, and it is entirely correct to hand the project off to others once the fire is lit.",
    54: "The Ambition. You carry the intense, driving force to rise. You possess the relentless energy to climb the material and spiritual ladders of life, transforming the mundane into the extraordinary through sheer will.<br/><br/>When driven by blind greed, you may compromise your integrity or step on others to achieve your goals, leaving you spiritually bankrupt. Mastery is the realization that true ambition is holistic; your material success only finds its highest meaning when it is used to elevate the spiritual consciousness of your community.",
    55: "The Spirit. You are the absolute core of emotional abundance. Your journey is deeply tied to the romantic, melancholic, and ecstatic waves of the human spirit, experiencing life at its most beautifully intense.<br/><br/>The shadow is getting trapped in the melancholic low, convincing yourself that your sadness is a permanent reality. Mastery is recognizing that your emotions are the weather, not the sky. By refusing to judge your lows, you unlock a profound, unconditional emotional freedom that has nothing to do with external circumstances.",
    56: "The Storyteller. You are the ultimate wanderer and weaver of beliefs. Your energy is designed to move through the world, gather a multitude of stimulating experiences, and translate them into stories that shift the perspective of the collective.<br/><br/>If you become addicted to the stimulation of the journey, you may run from depth, using your stories to distract from your own pain. Mastery is realizing that you do not need to constantly seek the next thrill; the most profound stories arise when you finally sit still and share the wisdom of your own healing.",
    57: "The Intuitive. You are the acoustic master of the now. You possess a brilliant, instantaneous survival instinct that operates through your physical body, hearing the subtle vibrations of truth and danger before the mind even registers them.<br/><br/>When you ignore this quiet inner voice, your energy is hijacked by a deep, paralyzing fear of the future. Mastery is learning to tune out the noise of the world and drop completely into your somatic knowing, trusting that your intuition will always keep you perfectly safe in the exact moment you need it.",
    58: "The Joy. You are the bubbling, irrepressible wellspring of vitality. You carry an enormous pressure to improve the world, driven by a deep, underlying love for the pure experience of being alive.<br/><br/>The shadow of this frequency is turning your desire for improvement into relentless criticism, constantly pointing out the flaws in yourself and others. Mastery is channeling this vitality into true service; you realize that the most profound way to correct the world is simply to model your own overflowing, unapologetic joy.",
    59: "The Sexual. You hold the profound, penetrating energy that dissolves the barriers between people. Your frequency is designed to break down walls, creating deep, generative intimacy that leads to physical, emotional, and creative reproduction.<br/><br/>When operating out of fear, you may use intimacy as a tool for control, or constantly seek union to avoid facing your own void. True mastery is realizing that your ability to connect is sacred; you use your penetrating aura to create safe, deeply authentic spaces where total transparency and mutual creation can thrive.",
    60: "The Limitation. You are the pulse of mutation. You carry the profound, heavy energy of structure and restraint, holding the tension required to force deep, lasting evolutionary change into existence.<br/><br/>The shadow is viewing your limitations as punishments, leading to deep depression and a feeling of being permanently stuck. Mastery is the radical acceptance of your boundaries; you realize that just as a river needs banks to flow with power, your limitations are the exact structures required to focus your energy into a massive breakthrough.",
    61: "The Mystery. You are the mind of the mystic. You possess the intense, constant mental pressure to know the unknowable, drawn to the hidden, the occult, and the deepest underlying truths of the universe.<br/><br/>When you try to force the universe to give you logical answers, you will drive yourself into profound mental anxiety. Your highest mastery is learning to simply play in the mystery, trusting that true inspiration does not come from relentless searching, but naturally arrives the moment your mind finally surrenders into stillness.",
    62: "The Detail. You are the organizing genius of the practical world. Your mind has an exquisite capacity to take vast, confusing concepts and anchor them into reality by identifying the exact, precise details required to make them function.<br/><br/>If you get lost in the minutiae, you may become excessively pedantic, losing the soul of the project by obsessing over its mechanics. Mastery is using your brilliant precision as a bridge, organizing the abstract into language and structure so the rest of the world can finally understand and utilize it.",
    63: "The Doubter. You are the origin point of logical inquiry. Your energy begins the process of understanding the world through a healthy, necessary skepticism, identifying exactly what is flawed so it can be fixed.<br/><br/>When you point this doubt at yourself or your relationships, you create a spiral of deep paranoia and self-sabotage. Mastery is understanding that your doubt is a tool meant strictly for systems, ideas, and logic; you heal your life by questioning the patterns of the world while maintaining absolute, unwavering faith in your own worth.",
    64: "The Confusion. You are the visualizer of the past. Your mind is a constantly swirling kaleidoscope of images, memories, and abstract data, holding the raw pressure to make sense of the entire human story.<br/><br/>The shadow of this energy is trying to force these abstract images into a neat, logical sequence, which only leads to profound mental exhaustion. True mastery is stepping back and simply watching the movie of your mind without judgment, trusting that the ultimate meaning of your life will reveal itself when the puzzle pieces naturally fall into place."
}

# --- HELPERS ---
def safe_get_date(d):
    if not d: return None
    return str(d).split("T")[0]

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
    gates = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
    return gates[int((d%360)/5.625)]

def resolve_loc(c):
    for k in CITY_DB:
        if k in str(c).lower(): return CITY_DB[k]
    try:
        g = Nominatim(user_agent="ia_app_v2")
        l = g.geocode(c)
        if l:
            from timezonefinder import TimezoneFinder
            return l.latitude, l.longitude, TimezoneFinder().timezone_at(lng=l.longitude, lat=l.latitude) or "UTC"
    except: pass
    return 51.50, -0.12, "Europe/London"

# --- PDF BUILDER ---
def create_pdf(name, chaps, chart):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], alignment=1, spaceAfter=20, fontSize=24, textColor=HexColor("#D4AF37"))
    header_style = ParagraphStyle('ChapterHead', parent=styles['Heading2'], spaceBefore=15, spaceAfter=10, fontSize=16, textColor=HexColor("#2c3e50"))
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], spaceAfter=12, fontSize=11, leading=14)

    story.append(Spacer(1, 60))
    story.append(Paragraph("THE LEGEND OF YOU", title_style))
    story.append(Paragraph(f"The Epic of {name}", styles['Italic']))
    story.append(Spacer(1, 40))
    story.append(PageBreak())

    for c in chaps:
        story.append(Paragraph(c['title'], header_style))
        clean_body = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c['body'])
        clean_body = clean_body.replace("\n", "<br/>")
        story.append(Paragraph(clean_body, body_style))
    
    story.append(PageBreak())
    
    story.append(Paragraph("Planetary Inventory", header_style))
    for k, v in chart.items():
        # Keep the title short for the inventory list
        short_title = KEY_LORE.get(v['Gate'], '').split(".")[0]
        txt = f"<b>{k}:</b> {v['Sign']} (Archetype {v['Gate']}) - {short_title}"
        story.append(Paragraph(txt, body_style))

    doc.build(story)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# --- MAIN ENDPOINT ---
@app.post("/calculate")
async def calculate(request: Request):
    d = await request.json()
    name = d.get("name", "Traveler")
    dob = safe_get_date(d.get("dob") or d.get("date")) or datetime.date.today().strftime("%Y-%m-%d")
    tob = clean_time(d.get("tob") or d.get("time"))
    city = d.get("city", "London")
    struggle = d.get("struggle", "general")

    try:
        lat, lon, tz_str = resolve_loc(city)
        
        # Calculate exact timezone offset for their birth city and date
        local_tz = pytz.timezone(tz_str)
        birth_dt = datetime.datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        localized_dt = local_tz.localize(birth_dt)
        utc_offset = localized_dt.utcoffset().total_seconds() / 3600.0
        
        dt = Datetime(dob.replace("-", "/"), tob, utc_offset)
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
        
        c_data = {}
        for p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            obj = chart.get(getattr(const, p.upper()))
            c_data[p] = {"Sign": obj.sign, "Gate": get_gate(obj.lon)}
        
        asc = chart.get(const.ASC)
        c_data["Rising"] = {"Sign": asc.sign, "Gate": get_gate(asc.lon)}
        
        p_sun = chart.get(const.SUN)
        p_line = (int(p_sun.lon / 0.9375) % 6) + 1
        d_line = (int(((p_sun.lon - 88) % 360) / 0.9375) % 6) + 1
        orient = f"{LINE_LORE.get(p_line, '')} / {LINE_LORE.get(d_line, '')}"
        
        try:
            lp = sum([int(n) for n in dob if n.isdigit()])
            while lp > 9 and lp not in [11, 22, 33]: lp = sum(int(n) for n in str(lp))
        except: lp = 0
        
        s_data = STRUGGLE_LORE.get(struggle, STRUGGLE_LORE["general"])
        
        sun, moon, ris = c_data['Sun'], c_data['Moon'], c_data['Rising']
        gate = KEY_LORE.get(sun['Gate'], "Energy")
        dragon = struggle[0].replace("The Quest for ", "")
        
        trinity_text = f"""Before we begin your legend, you must understand your geometric pillars. These are the three coordinates that define your frequency:

**☀️ The Sun in {sun['Sign']} ({SIGN_LORE.get(sun['Sign'])})**<br/>
{SUN_LORE.get(sun['Sign'], '')}

**🌙 The Moon in {moon['Sign']} ({SIGN_LORE.get(moon['Sign'])})**<br/>
{MOON_LORE.get(moon['Sign'], '')}

**🏹 The Rising in {ris['Sign']} ({SIGN_LORE.get(ris['Sign'])})**<br/>
{RISING_LORE.get(ris['Sign'], '')}"""

        origin_text = f"The primary tension in your chart exists between your inner **{sun['Sign']}** fire and your outer **{ris['Sign']}** shield. While the world meets you as the {SIGN_LORE.get(ris['Sign'])}, you know that beneath the armor burns the intensity of the {SIGN_LORE.get(sun['Sign'])}. Balancing these two forces is your first great mission."

        chaps = [
            {"title": "🔮 YOUR COSMIC TRINITY", "body": trinity_text},
            {"title": "🌟 THE ORIGIN STORY", "body": origin_text},
            {"title": "🏔️ THE PATH", "body": f"Your road is the **Path of the {lp}**: {LIFE_PATH_LORE.get(lp, '')} The universe will test you here, but the view from the top is your purpose."},
            {"title": "⚔️ THE WEAPON", "body": f"Your superpower is **Archetype {sun['Gate']}**.<br/><br/>{gate}"},
            {"title": "🗺️ THE STRATEGY", "body": f"Your operating manual is **{orient}**. You are not designed to move like everyone else. Trust your unique style of engagement."},
            {"title": "🐉 THE DRAGON", "body": f"Your antagonist is **{dragon}**. {s_data[1]} This struggle is not a punishment; it is the friction that sharpens your blade."}
        ]

        pdf_b64 = create_pdf(name, chaps, c_data)
        
        grid_html = ""
        for c in chaps:
            body_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c['body'])
            body_html = body_html.replace("\n", "<br>")
            grid_html += f"<div class='card'><h3>{c['title']}</h3><p>{body_html}</p></div>"
            
        html = f"""
        <html><head><style>
        body {{ font-family: 'Helvetica', sans-serif; padding: 20px; background: #fdfdfd; }}
        h2 {{ text-align: center; color: #D4AF37; font-size: 2rem; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 6px 15px rgba(0,0,0,0.08); border-top: 5px solid #D4AF37; }}
        .card h3 {{ margin-top: 0; color: #2c3e50; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
        .card p {{ color: #555; line-height: 1.6; font-size: 1rem; }}
        .btn {{ display: block; width: 220px; margin: 40px auto; padding: 15px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .btn:hover {{ background: #b8952b; }}
        </style></head><body>
        <h2>The Legend of {name}</h2>
        <div class="grid">{grid_html}</div>
        <a href="data:application/pdf;base64,{pdf_b64}" download="The_Legend_of_You.pdf" class="btn">⬇️ DOWNLOAD LEGEND</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": f"<h3>Error: {e}</h3>"}
