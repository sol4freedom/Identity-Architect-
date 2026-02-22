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

# --- LORE DATABASES PART 1 ---
CITY_DB = {
    "minneapolis": (44.97, -93.26, "America/Chicago"), "london": (51.50, -0.12, "Europe/London"),
    "new york": (40.71, -74.00, "America/New_York"), "ashland": (42.19, -122.70, "America/Los_Angeles"),
    "los angeles": (34.05, -118.24, "America/Los_Angeles"), "sao paulo": (-23.55, -46.63, "America/Sao_Paulo")
}

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

ORIGIN_SUN_LORE = {
    "Aries": "Your soul incarnated with a fierce, burning directive: to be the untamed spark of initiation. The core psychological wound you carry is the deep, suffocating fear of being controlled, managed, or having your fire extinguished by the collective. The ultimate illusion you are here to shatter is the belief that peace requires submission. Your origin journey demands that you stop apologizing for your intensity and realize that your raw, unapologetic drive is exactly what the universe needs to evolve.",
    "Taurus": "Your soul chose this lifetime to master the profound magic of the physical realm. The core psychological wound you carry is the lingering anxiety of scarcity—the fear that you are not inherently valuable unless you are producing or securing resources. The grand illusion you are here to shatter is that your worth must be earned through suffering and endless labor. Your origin journey requires you to reclaim your divine right to pleasure, stillness, and inherent, unshakeable abundance.",
    "Gemini": "Your soul incarnated with an insatiable hunger to understand the grand paradox of the universe. The core illusion you are here to shatter is the deeply ingrained belief that you must choose a single, fixed identity to be taken seriously. Your origin journey requires you to stop fragmenting yourself to please a world that demands consistency, and instead realize that your brilliant, ever-changing multiplicity is your truest power.",
    "Cancer": "Your soul incarnated to be the ultimate guardian of human vulnerability. The core psychological wound you carry is the visceral fear of emotional abandonment—the lingering sense that the world is too harsh to hold your profound depths safely. The illusion you are here to shatter is the belief that having intense emotional needs makes you weak. Your origin journey requires you to realize that your oceanic sensitivity is not a liability; it is a highly advanced, protective radar.",
    "Leo": "Your soul incarnated with the magnificent, terrifying purpose of being seen. The core psychological wound you carry is the quiet, devastating fear of being invisible, ordinary, or uncelebrated by the world. The ultimate illusion you are here to shatter is the belief that your radiant light somehow takes away from others. Your origin journey requires you to stop shrinking to make others comfortable, and realize that your unapologetic, joyous self-expression is the exact medicine that gives others permission to shine.",
    "Virgo": "Your soul chose this lifetime to be the ultimate vessel of refinement and devotion. The core psychological wound you carry is the crushing anxiety of imperfection—the underlying fear that if you are not useful, you are not inherently worthy. The grand illusion you are here to shatter is the belief that the world is broken and it is entirely your job to fix it. Your origin journey requires you to surrender your relentless inner critic and recognize that your supreme analytical gifts are meant to serve your joy, not to punish your humanity.",
    "Libra": "Your soul incarnated to master the profound art of equilibrium. The core psychological wound you carry is the visceral terror of discord, conflict, and rejection. The ultimate illusion you are here to shatter is the deeply ingrained belief that keeping the peace is the same thing as creating harmony. Your origin journey demands that you stop abandoning your own needs to keep everyone else comfortable, and realize that true, authentic connection can only exist when you are willing to bring your absolute truth to the table.",
    "Scorpio": "Your soul chose this lifetime to traverse the absolute depths of the human experience. The core psychological wound you carry is the profound fear of betrayal, leading to an underlying belief that the world is fundamentally unsafe and power is easily abused. The grand illusion you are here to shatter is the idea that vulnerability is a weakness. Your origin journey requires you to stop holding your breath waiting for the other shoe to drop, and to realize that your capacity to feel the darkest shadows is exactly what gives you access to the most blinding light.",
    "Sagittarius": "Your soul incarnated with an unquenchable thirst for ultimate truth and expansion. The core psychological wound you carry is the suffocating fear of being trapped, bored, or limited by the mundane world. The grand illusion you are here to shatter is the belief that true freedom means constantly running away from commitment. Your origin journey requires you to stop chasing the horizon to escape the present, and realize that the most profound adventure of your life is synthesizing your vast experiences into deep, grounded wisdom.",
    "Capricorn": "Your soul chose this lifetime to achieve the absolute mastery of the material and spiritual realms. The core psychological wound you carry is the heavy, exhausting fear of failure—the underlying belief that your worth is strictly defined by your tangible output and success. The ultimate illusion you are here to shatter is the idea that you have to earn your right to exist. Your origin journey demands that you transform your relentless ambition from a trauma response into a tool for true, sovereign creation.",
    "Aquarius": "Your soul incarnated with the radical purpose of collective mutation and systemic disruption. The core psychological wound you carry is a profound sense of alienation—the quiet, lingering grief of feeling like an alien who was dropped onto the wrong planet. The grand illusion you are here to shatter is the belief that to belong to humanity, you must conform to its outdated rules. Your origin journey requires you to stop agonizing over not fitting in, and fully embrace your destiny as the architect of the future.",
    "Pisces": "Your soul chose this lifetime to experience the ultimate dissolution of boundaries and act as a conduit for divine empathy. The core psychological wound you carry is the crushing weight of existential grief—the pain of absorbing the suffering of the world as if it were your own. The ultimate illusion you are here to shatter is the martyr complex: the belief that you must sacrifice yourself to heal others. Your origin journey requires you to realize that your infinite compassion is only sustainable when anchored by fierce, unapologetic boundaries."
}

ORIGIN_RISING_LORE = {
    "Aries": "To survive your early environment, you forged an armor of constant motion and preemptive strikes. You learned early on that if you didn't fight for your space, it would be taken from you, leading you to project a fiercely independent, sometimes intimidating shield. The tension of your life lies here: you must unlearn the habit of treating every interaction as a battle. Your ultimate initiation is to put down the sword and realize that your mere presence is powerful enough to command respect—you no longer need to fight to be seen.",
    "Taurus": "To navigate a chaotic early world, you built an impenetrable armor of stubborn stoicism. You learned that being the 'unbreakable rock' for everyone else was the safest way to maintain control and prevent your environment from collapsing. You conditioned yourself to absorb pressure without flinching. Your ultimate initiation is to slowly dismantle this heavy, isolating wall. You must learn the profound courage it takes to be soft, to ask for help, and to let yourself be held by the world you work so hard to stabilize.",
    "Gemini": "To survive a world that often misunderstands this complexity, you had to build a specific shield. You developed an armor of electric adaptability, learning early on to act as a mirror, seamlessly absorbing the frequency of your environment and shape-shifting to keep the peace. The tension of your life lies here: you must unlearn the habit of talking your way out of your own depths. Your ultimate initiation is to stop reflecting the world back to itself, and finally demand that the world stand still long enough to witness the real you.",
    "Cancer": "To protect your incredibly porous heart, you developed a hardened, external shell. You likely took on the role of the caretaker early in life, mothering and nurturing everyone around you as a subconscious strategy to ensure you wouldn't be abandoned. This mask keeps you safe, but it keeps you starved of receiving. Your ultimate initiation is to put down the heavy mantle of always having to be the emotional anchor, and dare to let someone else take care of you.",
    "Leo": "To navigate your early environment, you forged an armor of performance and regal invulnerability. You learned that if you were the brightest, the strongest, or the most entertaining, you would be safe and loved. You built a vessel that projects immense confidence, often hiding your deepest insecurities behind a dazzling smile or generous leadership. Your ultimate initiation is to step off the stage. You must realize that you are profoundly worthy of love even when you are messy, exhausted, and have absolutely nothing to give the audience.",
    "Virgo": "To survive the chaos of your early world, you built an armor of extreme, unshakeable competence. You learned early on that if you could organize, predict, and flawlessly manage your environment, you could prevent pain. You walk through the world projecting a shield of total self-sufficiency, often convincing others that you never need help. Your ultimate initiation is to allow yourself to be deeply, beautifully messy. You must put down the clipboard, let the system break, and trust that you will still be safe in the chaos.",
    "Libra": "To protect yourself in your early environment, you forged an armor of flawless diplomacy and aesthetic perfection. You learned how to read a room instantly, softening your edges and shape-shifting to become exactly what others needed you to be. Your vessel projects an effortless, charming grace that actively avoids making waves. The tension of your life lies here: you must unlearn the habit of people-pleasing. Your ultimate initiation is to realize that your authentic voice is far more valuable than your compliance, even if speaking it causes a temporary storm.",
    "Scorpio": "To navigate a world you perceived as dangerous, you built an impenetrable fortress of secrecy, control, and intimidation. You learned early on to observe everything while revealing absolutely nothing, projecting a quiet, intense aura that keeps people at a safe distance. Your vessel is a master of hiding in plain sight. Your ultimate initiation is lowering the drawbridge. You must face the terrifying task of letting someone see your soft, intensely feeling core without constantly testing them to see if they will break your trust.",
    "Sagittarius": "To survive the heaviness of your early environment, you forged an armor of philosophical detachment, humor, and constant motion. You learned early on that if things got too intense, you could simply intellectualize the pain, make a joke, or literally leave the room. You project an aura of bulletproof optimism. Your ultimate initiation is to stay in the fire. You must unlearn the habit of using your visionary nature as an escape hatch, and dare to let people see the vulnerable human behind the traveling philosopher.",
    "Capricorn": "To navigate the chaos or lack of structure in your early world, you built an impenetrable armor of authority and hyper-independence. You likely had to grow up far too fast, taking on burdens and responsibilities that were not yours to carry. You project a vessel of extreme capability, silently convincing the world that you never need a break. Your ultimate initiation is to take off the heavy crown. You must realize that resting is not failing, and allowing yourself to be supported is your highest demonstration of power.",
    "Aquarius": "To protect yourself from the overwhelming emotional turbulence of your early environment, you forged an armor of intellectual detachment. You learned to float above the chaos, observing life logically rather than feeling it physically. Your vessel projects a brilliant, slightly unpredictable, and deeply independent frequency. The tension of your life lies here: you must unlearn the habit of severing your mind from your heart. Your ultimate initiation is to drop back down into your physical body and let the world connect with your messy humanity, not just your brilliant ideas.",
    "Pisces": "To survive the harshness of your early world, you built an armor of shape-shifting and elusiveness. You learned how to become the ultimate chameleon, seamlessly retreating into fantasy or molding yourself into whatever the room needed you to be in order to stay safe. Your vessel is a mirror, reflecting everyone else's dreams back to them while hiding your own. Your ultimate initiation is to anchor yourself in reality. You must stop dissolving into the background and force the world to see the true, definitive shape of who you are."
}
LIFE_PATH_LORE = {
    1: "The Primal Leader. Your road is the Path of the 1. You are the arrow that leaves the bow first. Your overarching soul mission is the realization of absolute, sovereign independence. You are not here to follow the trails blazed by others; you are here to hack through the dense jungle and create the path yourself.<br/><br/>The universe will test you by placing you in situations where you feel utterly unsupported, forcing you to develop profound self-reliance. When operating in shadow, you may try to aggressively force outcomes or steamroll others. Your mastery lies in realizing that true leadership is not about demanding followers; it is about having the terrifying courage to walk your authentic path alone until the right people naturally align behind you.",
    2: "The Peacemaker. Your road is the Path of the 2. You are the diplomat of the soul. Your overarching mission is the mastery of relationship, duality, and deep intuitive listening. You are here to learn the profound energetics of how humans connect, balance, and heal one another.<br/><br/>The universe will continually test your boundaries, drawing you toward heavy, complicated dynamics. When out of alignment, you risk slipping into codependency or absorbing the toxic emotional waste of your environment. True mastery for you is learning that saying 'no' is an act of love. You can only act as a true anchor for peace when your own energetic boundaries are fiercely protected.",
    3: "The Creative Spark. Your road is the Path of the 3. You are the voice of the universe expressing its joy. Your mission in this lifetime is the mastery of authentic self-expression and emotional vulnerability. You are designed to take the heavy, dense experiences of life and alchemize them into art, communication, and inspiration.<br/><br/>The universe will test you through profound self-doubt and the fear of judgment. In shadow, you may scatter your energy, hiding your true depth behind superficial charm or silencing yourself entirely. Your mastery is the realization that your unapologetic joy is not frivolous—it is a deeply necessary, high-frequency medicine the world desperately needs.",
    4: "The Master Builder. Your road is the Path of the 4. You are the architect of the future. Your soul's mission is the mastery of foundational security, dedication, and transforming abstract ideas into concrete, lasting reality. You are here to do the unglamorous, sacred work of building systems that survive the test of time.<br/><br/>The universe will test you with sudden chaos, forcing you to learn the difference between healthy structure and rigid control. When in shadow, you may work yourself to the bone, confusing endless suffering with worthiness. Mastery is learning to build with the flow of the universe rather than against it, establishing unshakeable foundations without sacrificing your own joy and vitality.",
    5: "The Freedom Seeker. Your road is the Path of the 5. You are the wind that cannot be caged. Your mission is the mastery of change, profound adaptability, and experiencing the absolute maximum spectrum of human existence. You are here to break the stagnant rules and show humanity what it means to be truly, wildly alive.<br/><br/>The universe will test you through restlessness and the fear of being trapped. In shadow, this frequency devolves into chaos, escapism, and the inability to commit to anything deep enough to extract its wisdom. Mastery is the realization that true freedom is an internal state; it is found not by constantly running, but by grounding yourself enough to experience the profound depth of the present moment.",
    6: "The Cosmic Guardian. Your road is the Path of the 6. You are the protector of the hearth. Your soul chose to master the frequencies of unconditional love, responsibility, and deep communal healing. You possess an aura that naturally draws broken things to you so they can be made whole.<br/><br/>The universe will test you by pushing you to the absolute limits of your caretaking capacity. When out of alignment, you devolve into martyrdom, carrying the burdens of the world until you are completely hollowed out and resentful. Your ultimate mastery is the radical, somatic understanding that you must ruthlessly prioritize your own self-care, for you cannot pour from an empty cup.",
    7: "The Mystic Sage. Your road is the Path of the 7. You are the walker between worlds. Your overarching mission is the pursuit of ultimate spiritual and intellectual truth. You are naturally wired to look behind the curtain of reality, questioning the superficial and demanding to know the profound mechanics of existence.<br/><br/>The universe will test you through profound feelings of isolation and the tendency to over-intellectualize your feelings. In shadow, you may lock yourself in an ivory tower of cynicism, disconnecting from your own humanity. Mastery is bridging the gap: you must take the profound esoteric wisdom you gather in the silence and courageously bring it down into the messy, beautiful physical world.",
    8: "The Sovereign. Your road is the Path of the 8. You are the CEO of the material plane. Your soul's mission is the absolute mastery of power, wealth, and systemic influence. You are not here to reject the material world; you are here to spiritualize it, proving that abundance and integrity can coexist.<br/><br/>The universe will repeatedly test your relationship with control, power, and money. When operating in fear, you may become ruthless, greedy, or deeply obsessed with status to mask a lack of self-worth. True mastery is benevolent sovereignty: recognizing that your immense power is a sacred tool meant to generate abundance not just for yourself, but to elevate and resource your entire community.",
    9: "The Humanitarian. Your road is the Path of the 9. You are the old soul on one last mission. Your path is the mastery of completion, universal compassion, and the profound art of letting go. You carry the energetic weight of past cycles and are here to help humanity close the chapters that no longer serve it.<br/><br/>The universe will test you through intense, painful attachments to the past. In shadow, you may hold onto bitter resentments or refuse to let dead things die, dragging heavy baggage into your future. Mastery is radical forgiveness and surrender; by gracefully releasing what is over, you instantly liberate yourself and become a pure conduit for universal love.",
    11: "The Illuminator. Your road is the Path of the Master Number 11. You are the lightning rod. Your mission is to act as a direct channel for divine inspiration, psychic insight, and spiritual illumination. You hold twice the intuitive power of the 2, combined with the fierce, independent drive of the 1.<br/><br/>The universe will test your highly sensitive nervous system to its absolute limits. In shadow, you may be paralyzed by profound anxiety, self-doubt, or the sheer overwhelming volume of the energetic data you receive. Mastery is learning to ground your electric current; you must ruthlessly protect your physical vessel so you can safely channel your blinding insights to the collective.",
    22: "The Master Architect. Your road is the Path of the Master Number 22. You are the bridge between heaven and earth. Your soul carries the most potent manifesting frequency available, designed to take massive, world-altering spiritual visions and anchor them permanently into the physical plane.<br/><br/>The universe will test you by handing you blueprints that seem impossibly large. When out of alignment, the sheer scale of your potential will paralyze you with the fear of failure, causing you to shrink into the mundane. Mastery is entirely about the slow, methodical grind; you change the world by breaking your monumental vision down into microscopic daily actions and relentlessly building.",
    33: "The Avatar of Love. Your road is the Path of the Master Number 33. You are the teacher of teachers. Your ultimate mission is the profound expression of pure, unconditional love and the elevation of global consciousness. You possess an aura that fundamentally shifts the vibration of anyone who enters it.<br/><br/>The universe will test you through extreme emotional empathy. In shadow, you may completely lose your identity by attempting to absorb and heal all the suffering of the world, leading to utter destruction of your own vessel. Your mastery is the realization that your highest service is simply your state of being. You heal the world by modeling what absolute, joyous self-love looks like."
}

STRUGGLE_LORE = {
    "wealth": ("The Quest for Abundance", "The Dragon of Scarcity. You have entered the Quest for Abundance. Your antagonist in this chapter of your life is the deep, cellular anxiety that there is not enough—not enough money, not enough time, or not enough of you to go around. This struggle is not a punishment; it is the friction required to teach you that wealth is a frequency, not just a bank balance.<br/><br/>When you fight this dragon, you hustle blindly, burn out, and view every dollar as a matter of survival. To tame it, you must honor your Jupiter placement and realize that you only magnetize true, lasting resources when you stop forcing outcomes and start directing your energy strictly toward what brings you profound, unshakeable joy."),
    "relationship": ("The Quest for Connection", "The Dragon of Disharmony. You have entered the Quest for Connection. Your antagonist is the pain of feeling unseen, misunderstood, or trapped in toxic dynamics. This struggle is the universe's ultimate mirror; it is showing you exactly where you have abandoned your own boundaries in order to be loved.<br/><br/>When you fight this dragon, you either build massive emotional walls to keep people out, or you completely lose your identity trying to people-please. To tame it, you must honor your Venus placement. True intimacy requires you to drop the armor, stand firmly in your highest values, and realize that you can only attract your true tribe when you are brave enough to show them exactly who you are."),
    "purpose": ("The Quest for Meaning", "The Dragon of The Void. You have entered the Quest for Meaning. Your antagonist is the profound, heavy numbness of feeling lost, disconnected from your soul’s mission, and wondering, 'Is this all there is?' This void is not a sign that you are broken; it is the sacred incubation space before a massive rebirth.<br/><br/>When you fight this dragon, you desperately grasp at new jobs, titles, or distractions to fill the emptiness. To tame it, you must align with your North Node and stop trying to 'do' your purpose. Your ultimate mastery is the realization that your purpose is not a career—it is your unique state of being. Drop into the present moment and simply let your life unfold."),
    "health": ("The Quest for Vitality", "The Dragon of Exhaustion. You have entered the Quest for Vitality. Your antagonist is the physical breakdown of your vessel—chronic fatigue, somatic tension, or feeling completely disconnected from your own body. This struggle is your nervous system slamming on the brakes because you have been living out of alignment with your natural rhythm.<br/><br/>When you fight this dragon, you try to push through the pain, relying on caffeine, willpower, and guilt to keep moving. To tame it, you must honor your Saturn placement and establish radical boundaries. Your healing requires you to stop viewing your body as a machine to be optimized, and start treating it as a sacred temple that requires immense rest, grace, and listening."),
    "general": ("The Quest for Alignment", "The Dragon of Confusion. You have entered the Quest for Alignment. Your antagonist is the mental static of overwhelm—the feeling of being pulled in a hundred different directions by the expectations of the world, unsure of which path is truly yours.<br/><br/>When you fight this dragon, you get trapped in your head, constantly overthinking and asking everyone else for advice, which only creates more chaos. To tame it, you must return to the compass of your Rising Sign. You heal this confusion by entirely dropping out of your anxious mind and returning to the absolute authority of your physical body. Trust your unique strategy, take one grounded step, and the path will naturally illuminate itself.")
}

LINE_LORE = {
    1: "You carry the frequency of the Investigator. Your strategy requires a foundation of absolute, undeniable truth. You are not meant to leap blindly into the void; you are energetically designed to dig into the basement of any subject, relationship, or system until you understand its core mechanics.<br/><br/>The shadow of this line is chronic insecurity—the paralyzing fear that you still don't know enough to act, leading to endless rabbit holes of research. Your ultimate mastery is realizing when the foundation is solid enough to stand on. When you finally trust your depth of knowledge, you become an unshakeable, unquestionable authority that others naturally build upon.",
    2: "You carry the frequency of the Natural. Your strategy operates entirely on innate, effortless genius. You contain profound gifts that you likely cannot explain or teach to others; you simply *do* them. You naturally require significant alone time to let this unforced energy flow without interference.<br/><br/>The shadow of this line is a crippling imposter syndrome, combined with the urge to hide away to avoid the projections of others. You often cannot see your own brilliance until someone points it out. True mastery is the surrender to your own flow. You do not need to figure out how to market yourself; you simply need to engage in your joy and allow the right people to call you out of your cave to share your gifts.",
    3: "You carry the frequency of the Experimenter. Your strategy is the sacred path of trial and error. You are fundamentally designed to bump into life, break things, figure out what does not work, and discover the truth through raw, lived experience. You are the ultimate pioneer.<br/><br/>The shadow of this line is profound shame. The world may have conditioned you to believe that your 'mistakes' mean you are broken or chaotic. Mastery is the radical reframe of your failures: you realize that you are not messing up, you are gathering data. When you drop the shame of getting it wrong, you become the wisest guide in the room, saving others from the pitfalls you have already mapped out.",
    4: "You carry the frequency of the Networker. Your strategy is anchored entirely in intimate, warm relationships. Your opportunities, wealth, and profound breakthroughs are not designed to come from cold-calling strangers; they are meant to flow seamlessly through your established community and the people who already trust you.<br/><br/>The shadow of this line is the deep, cellular fear of rejection, which can keep you trapped in toxic friendships or stagnant environments simply because you are afraid to be alone. Mastery is the ruthless curation of your inner circle. When you protect your heart and only invest in high-frequency, authentic relationships, your network becomes the ultimate catalyst for your destiny.",
    5: "You carry the frequency of the Fixer. Your strategy is to be the ultimate, practical problem-solver. You possess an intensely magnetic, projected aura—people look at you and subconsciously believe you are the savior who can step in and fix their crises.<br/><br/>The shadow of this line is the crushing weight of these expectations. If you try to save everyone, or step in when you do not actually have the practical solution, you will inevitably disappoint them and be metaphorically burned at the stake. Your absolute mastery is strict, unyielding boundary setting. You must learn to fiercely protect your energy, only stepping in to fix the problems that practically serve you and where you are genuinely invited and rewarded.",
    6: "You carry the frequency of the Role Model. Your strategy spans a massive, three-part evolutionary arc. You are designed to spend your youth making messy mistakes, your mid-life retreating to the roof to heal and observe, and your later years descending as the wise, living embodiment of everything you have learned.<br/><br/>The shadow of this line is a deep, agonizing aloofness—a feeling of being totally disconnected from the messy, mundane struggles of humanity, or falling into the trap of telling others how to live without walking the talk yourself. Mastery is profound, somatic authenticity. You change the world not by preaching from the roof, but by walking on the ground as the absolute, integrated embodiment of your truth."
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
    24: "The Rationalizer. You are the master of mental review and renewal. Your mind is designed to circle around a mystery, viewing it from every angle until you find the true, undeniable essence at its core.<br/><br/>The shadow of this frequency is getting trapped in endless, anxious mental loops, overthinking until you are paralyzed. Mastery is learning to let the mind rest in the void of the unknown, trusting that the answer will naturally click into place when the time is right.",
    25: "The Spirit. You hold the profound frequency of unconditional, universal love. You are designed to walk through life's deepest trials and initiations while keeping your heart radically, vulnerably open.<br/><br/>When wounded, you may feel victimized by the harshness of the world and close yourself off to protect your spirit. Your ultimate mastery is maintaining your spiritual innocence, trusting the divine orchestration of the universe, and loving the world no matter how it scars you.",
    26: "The Egoist. You possess the magnetic power of influence, memory, and a healthy, unashamed ego. Your gift is the ability to pitch ideas, rally the collective, and bend reality through sheer persuasion.<br/><br/>When insecure, this energy devolves into manipulation or boastfulness to mask a lack of self-worth. Mastery is realizing that a strong ego is not a sin; when you use your immense influence to empower and elevate the collective, your ego becomes a sacred tool for the greater good.",
    27: "The Nurturer. You carry the profound energetic blueprint of compassion and preservation. Your aura naturally provides the nourishment, care, and safety required to sustain life and foster deep growth.<br/><br/>The shadow of this frequency is martyrdom—giving to others until you are completely hollowed out and resentful. Mastery is the radical understanding that self-care is the absolute prerequisite for universal care; you can only truly nourish the world when your own cup is overflowing.",
    28: "The Risk Taker. You are the courageous player of the game of life. Your energy is designed to face the darkness, push limits, and find profound meaning through struggle and extreme experiences.<br/><br/>When operating blindly, you may create unnecessary drama or take reckless gambles just to feel alive. True mastery is transforming your fear into wisdom; you learn to take calculated risks not for the thrill of the adrenaline, but for the evolution of your highest purpose.",
    29: "The Devoted. You are the embodiment of deep, enduring commitment. When you say 'yes,' you throw your entire being into the experience, possessing the stamina to persist through the longest cycles of life.<br/><br/>If you commit to things out of obligation, you will drag yourself through profound exhaustion. Your mastery is learning the sacred power of 'no.' When you fiercely protect your energy, your authentic 'yes' retains its immense, world-moving power.",
    30: "The Passion. You are the clinging fire. You experience life through a lens of intense, burning desire and emotional depth, hungering for the raw, unfiltered experience of what it means to be human.<br/><br/>The shadow is becoming entirely consumed by your desires, chasing the next high until you burn out. Mastery is surrendering to the feeling without needing to act on every impulse; you learn to let the fire of your passion warm you rather than destroy you.",
    31: "The Voice. You are a natural, influential leader through the spoken word. You possess the energetic capacity to manifest collective vision into reality simply by articulating the direction forward.<br/><br/>When driven by ego, you may dictate, demand, or speak without ever listening to those you lead. True mastery is recognizing that you are a vessel; your leadership only works when you are authentically voicing the true needs and direction of your community.",
    32: "The Conservative. You hold the instinctual knowing of what truly has value. Your gift is the ability to look at any system, tradition, or business and know exactly what must be preserved to ensure survival and success.<br/><br/>When paralyzed by the fear of failure, you may cling to dead traditions that no longer serve you. Mastery is becoming the dynamic preserver; you learn to fiercely protect the core essence of a thing while allowing its outer form to evolve with the times."
}
KEY_LORE.update({
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
})

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
        
        trinity_text = f"Before we begin your legend, you must understand your geometric pillars. These are the three coordinates that define your frequency:\n\n**☀️ The Sun in {sun['Sign']} ({SIGN_LORE.get(sun['Sign'])})**<br/>\n{SUN_LORE.get(sun['Sign'], '')}\n\n**🌙 The Moon in {moon['Sign']} ({SIGN_LORE.get(moon['Sign'])})**<br/>\n{MOON_LORE.get(moon['Sign'], '')}\n\n**🏹 The Rising in {ris['Sign']} ({SIGN_LORE.get(ris['Sign'])})**<br/>\n{RISING_LORE.get(ris['Sign'], '')}"

        origin_text = f"**The Inner Awakening ({sun['Sign']} Sun)**<br/>{ORIGIN_SUN_LORE.get(sun['Sign'], '')}<br/><br/>**The Outer Initiation ({ris['Sign']} Rising)**<br/>{ORIGIN_RISING_LORE.get(ris['Sign'], '')}"

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
            
        html = f'''
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
        '''
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": f"<h3>Error: {e}</h3>"}

# --- FREE SNAPSHOT ENDPOINT (LEAD MAGNET) ---
@app.post("/calculate-free")
async def calculate_free(request: Request):
    d = await request.json()
    name = d.get("name", "Traveler")
    dob = safe_get_date(d.get("dob") or d.get("date")) or datetime.date.today().strftime("%Y-%m-%d")
    tob = clean_time(d.get("tob") or d.get("time"))
    city = d.get("city", "London")
    struggle = d.get("struggle", "general")

    try:
        lat, lon, tz_str = resolve_loc(city)
        
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
        
        try:
            lp = sum([int(n) for n in dob if n.isdigit()])
            while lp > 9 and lp not in [11, 22, 33]: lp = sum(int(n) for n in str(lp))
        except: lp = 0
        
        sun, moon, ris = c_data['Sun'], c_data['Moon'], c_data['Rising']
        dragon = struggle[0].replace("The Quest for ", "")
        
        # --- THE FREE CONTENT (TITLES ONLY) ---
        snapshot_text = f"""Welcome to your Cosmic Snapshot. Here are the geometric pillars that define your baseline frequency:<br/><br/>
        **☀️ The Sun in {sun['Sign']} ({SIGN_LORE.get(sun['Sign'])})**<br/>
        This is your Core Essence and conscious purpose.<br/><br/>
        **🌙 The Moon in {moon['Sign']} ({SIGN_LORE.get(moon['Sign'])})**<br/>
        This is your Inner World and emotional sanctuary.<br/><br/>
        **🏹 The Rising in {ris['Sign']} ({SIGN_LORE.get(ris['Sign'])})**<br/>
        This is your Vessel and style of engagement."""

        cta_text = f"""This snapshot is just the surface.<br/><br/>
        Locked inside your full chart is your **Archetype {sun['Gate']}** superpower, your exact Human Design Strategy, and the profound, multi-page Origin Story of your {sun['Sign']} Sun and {ris['Sign']} Rising.<br/><br/>
        You are currently facing the **Dragon of {dragon}**.<br/><br/>
        To discover how to tame this Dragon and unlock your ultimate behavioral blueprint, upgrade to the Full Epic Legend through The Integrated Self."""

        chaps = [
            {"title": "✨ YOUR COSMIC SNAPSHOT", "body": snapshot_text},
            {"title": "🏔️ YOUR LIFE PATH", "body": f"You are walking the **Path of the {lp}**: {LIFE_PATH_LORE.get(lp, '').split('.')[0]}."},
            {"title": "🔓 THE MYSTERY AWAITS", "body": cta_text}
        ]

        # Generate the shorter PDF
        pdf_b64 = create_pdf(name, chaps, c_data)
        
        # Build the HTML Grid
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
        .cta-box {{ background: #2c3e50; color: white; padding: 25px; border-radius: 12px; margin-top: 30px; text-align: center; box-shadow: 0 6px 15px rgba(0,0,0,0.2); }}
        .cta-box h3 {{ color: #D4AF37; margin-top: 0; }}
        .btn {{ display: block; width: 250px; margin: 30px auto; padding: 15px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .btn:hover {{ background: #b8952b; }}
        </style></head><body>
        <h2>The Snapshot of {name}</h2>
        <div class="grid">{grid_html}</div>
        <div class="cta-box">
            <h3>Ready for the Deep Dive?</h3>
            <p>Upgrade to the Full Epic Legend to unlock your Origin Story, your Archetype, and the secret to taming your Dragon.</p>
        </div>
        <a href="data:application/pdf;base64,{pdf_b64}" download="Cosmic_Snapshot.pdf" class="btn">⬇️ DOWNLOAD SNAPSHOT</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": f"<h3>Error: {e}</h3>"}

# --- COSMIC CLARITY BUNDLE ENDPOINT ---
@app.post("/calculate-bundle")
async def calculate_bundle(request: Request):
    d = await request.json()
    name = d.get("name", "Traveler")
    dob = safe_get_date(d.get("dob") or d.get("date")) or datetime.date.today().strftime("%Y-%m-%d")
    tob = clean_time(d.get("tob") or d.get("time"))
    city = d.get("city", "London")

    try:
        lat, lon, tz_str = resolve_loc(city)
        
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
        
        try:
            lp = sum([int(n) for n in dob if n.isdigit()])
            while lp > 9 and lp not in [11, 22, 33]: lp = sum(int(n) for n in str(lp))
        except: lp = 0
        
        sun, moon, ris = c_data['Sun'], c_data['Moon'], c_data['Rising']
        
        # --- THE 5 QUESTIONS CONTENT ---
        q1_text = f"Your purpose is a frequency, not a job title. You do not need to 'find' your purpose; you just need to embody your geometry. As a **{sun['Sign']} Sun**, {SUN_LORE.get(sun['Sign'], '')}<br/><br/>You are simultaneously walking the **Path of the {lp}**: {LIFE_PATH_LORE.get(lp, '')}"
        
        q2_text = f"We repeat cycles when our nervous system mistakes familiar chaos for safety. Your emotional world is ruled by your **{moon['Sign']} Moon**. {MOON_LORE.get(moon['Sign'], '')}<br/><br/>To break painful relationship patterns, you must fiercely protect this specific emotional sanctuary and only invite in those who honor it."
        
        q3_text = f"Abundance requires you to operate using your specific energetic mechanics. As a **{ris['Sign']} Rising**, {RISING_LORE.get(ris['Sign'], '')}<br/><br/>Furthermore, your conscious strategy in the material world is the **Line {p_line}**. {LINE_LORE.get(p_line, '')}"
        
        q4_text = f"Burnout happens when you carry armor that isn't yours. To survive your early environment, you built a very specific shield based on your **{ris['Sign']} Rising**: {ORIGIN_RISING_LORE.get(ris['Sign'], '')}<br/><br/>This is the root of your exhaustion. It is time to put this heavy armor down."
        
        q5_text = f"To break mental static and paralysis, you must apply the R.I.D. Wave (Recognize, Identify, Decide) through the lens of your unconscious strategy.<br/><br/>Recognize the pattern of overwhelm. Identify the root cause. Then, Decide to act based on your **Line {d_line}** operating manual: {LINE_LORE.get(d_line, '')}"

        chaps = [
            {"title": "1. What is my true life purpose?", "body": q1_text},
            {"title": "2. Why do I attract painful relationships?", "body": q2_text},
            {"title": "3. How can I attract true abundance?", "body": q3_text},
            {"title": "4. Why am I so exhausted and burned out?", "body": q4_text},
            {"title": "5. How do I get unstuck and make a decision?", "body": q5_text}
        ]

        # Generate the Bundle PDF
        pdf_b64 = create_pdf(name, chaps, c_data)
        
        # Build the HTML Grid
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
        .btn {{ display: block; width: 250px; margin: 30px auto; padding: 15px; background: #D4AF37; color: white; text-align: center; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .btn:hover {{ background: #b8952b; }}
        </style></head><body>
        <h2>The Cosmic Clarity Bundle for {name}</h2>
        <div class="grid">{grid_html}</div>
        <a href="data:application/pdf;base64,{pdf_b64}" download="Cosmic_Clarity_Bundle.pdf" class="btn">⬇️ DOWNLOAD BUNDLE</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": f"<h3>Error: {e}</h3>"}
