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
    # Full 64 Gate Logic
    deg = d % 360
    hex_idx = int(deg / 5.625)
    gates = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
    # Simple lookup fallback if list logic fails
    try: return gates[hex_idx]
    except: return 1

def resolve_loc(c):
    for k in CITY_DB:
        if k in str(c).lower(): return CITY_DB[k]
    try:
        g = Nominatim(user_agent="ia_v99_final")
        l = g.geocode(c)
        if l:
            from timezonefinder import TimezoneFinder
            return l.latitude, l.longitude, TimezoneFinder().timezone_at(lng=l.longitude, lat=l.latitude) or "UTC"
    except: pass
    return 51.50, -0.12, "Europe/London"

def get_tz(d, t, z):
    try:
        dt = datetime.datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
        return pytz.timezone(z).utcoffset(dt).total_seconds() / 3600.0
    except: return 0.0

# --- THE EPIC STORY ENGINE (RESTORED) ---
def gen_chapters(name, chart, orient, lp, struggle):
    sun, moon, ris = chart['Sun'], chart['Moon'], chart['Rising']
    s_lore = SIGN_LORE.get(sun['Sign'], "The Hero")
    m_lore = SIGN_LORE.get(moon['Sign'], "The Soul")
    r_lore = SIGN_LORE.get(ris['Sign'], "The Mask")
    
    gate_name = KEY_LORE.get(sun['Gate'], "Energy")
    dragon_name = struggle[0].replace("The Quest for ", "")
    dragon_desc = struggle[1]
    
    lp_desc = LIFE_PATH_LORE.get(lp, "A path of unique discovery.")

    # 1. ORIGIN
    c1 = f"Long ago, the universe conspired to create a unique frequency, and it named that frequency {name}. You were born under the blazing **Sun in {sun['Sign']}**. {s_lore} This is your core, your fuel, and your inevitable nature. It is the fire that burns within you, demanding expression.\n\nHowever, raw energy requires a vessel. To navigate the physical world, you adopted the mask of **{ris['Sign']} Rising**. {r_lore} This is your armor and your first impression. Your journey begins by reconciling these two: the inner fire of the {sun['Sign']} and the outer shield of the {ris['Sign']}."

    # 2. HEART
    c2 = f"But a warrior is nothing without a reason to fight. Beneath the armor lies a secret engine: your **Moon in {moon['Sign']}**. While others see your actions, only you feel the pull of this energy. {m_lore} This is what nourishes you. When you are alone, in the quiet dark, this is the voice that speaks. It governs your emotional tides. Ignoring this voice is what leads to burnout; honoring it is the secret to your endless regeneration."

    # 3. PATH
    c3 = f"Every hero needs a road to walk. Yours is the **Path of the {lp}**. {lp_desc} This is not a random wander; it is a destiny. The universe will constantly test you with challenges that force you to embody this number. It is a steep climb, and at times it will feel lonely, but the view from the top is the purpose you have been searching for."

    # 4. WEAPON
    c4 = f"To aid you on this path, you were gifted a specific weapon—a superpower woven into your DNA. In the language of the Archetypes, you carry the energy of **Archetype {sun['Gate']}: {gate_name}**. This is not a skill you learned in school; it is a frequency you emit naturally. When you trust this power, doors open without force. It is the sword in your hand. When you try to be someone else, you dull this blade. Your task is to wield it with precision."

    # 5. STRATEGY
    c5 = f"But power without control is dangerous. Your operating manual is defined by your Orientation: **{orient}**. You are not designed to move like everyone else. Your specific strategy requires you to honor your nature—whether that is to wait in your hermitage, to experiment fearlessly, or to network with your tribe. Deviation from this strategy is the root of your frustration. You must trust your unique style of engagement."

    # 6. DRAGON
    c6 = f"Every story has an antagonist. Yours takes the form of **{dragon_name}**. {dragon_desc} This struggle you feel—whether in wealth, love, or purpose—is not a punishment from the universe. It is the friction necessary to sharpen your blade. The dragon guards the treasure. By facing your Shadow and applying your Archetype, you do not just slay the dragon; you integrate it, turning your greatest weakness into your greatest wisdom."

    return [
        {"title": "🌟 THE ORIGIN", "body": c1},
        {"title": "❤️ THE HEART", "body": c2},
        {"title": "🏔️ THE PATH", "body": c3},
        {"title": "⚔️ THE WEAPON", "body": c4},
        {"title": "🗺️ THE STRATEGY", "body": c5},
        {"title": "🐉 THE DRAGON", "body": c6}
    ]

def clean_txt(t):
    if not t: return ""
    # Strip Emojis & Fix Fancy Quotes for PDF safety
    t = re.sub(r'[^\x00-\x7F]+', '', t) 
    return t.replace("—", "-").replace("’", "'").replace("**", "").encode('latin-1', 'replace').decode('latin-1')

def create_pdf(name, chaps, chart):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 10, 'THE LEGEND OF YOU', 0, 1, 'C')
        pdf.set_font("Helvetica", 'I', 12)
        pdf.cell(0, 10, clean_txt(f"The Epic of {name}"), 0, 1, 'C')
        pdf.ln(10)
        
        for c in chaps:
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, clean_txt(c['title']), 0, 1)
            pdf.set_font("Helvetica", '', 11)
            pdf.multi_cell(0, 6, clean_txt(c['body']))
            pdf.ln(5)
            
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Planetary Inventory", 0, 1)
        pdf.ln(5)
        for k, v in chart.items():
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 8, clean_txt(f"{k}: {v['Sign']} (Archetype {v['Gate']})"), 0, 1)
            pdf.set_font("Helvetica", '', 10)
            pdf.multi_cell(0, 5, clean_txt(KEY_LORE.get(v['Gate'], "")))
            pdf.ln(2)
            
        return base64.b64encode(pdf.output()).decode('utf-8')
    except Exception as e:
        logger.error(f"PDF Fail: {e}")
        return ""

@app.post("/calculate")
async def calculate(request: Request):
    d = await request.json()
    name = d.get("name", "Traveler")
    dob = safe_get_date(d.get("dob") or d.get("date")) or datetime.date.today().strftime("%Y-%m-%d")
    tob = clean_time(d.get("tob") or d.get("time"))
    city = d.get("city", "London")
    struggle = d.get("struggle", "general")

    try:
        lat, lon, tz = resolve_loc(city)
        off = get_tz(dob, tob, tz)
        dt = Datetime(dob.replace("-", "/"), tob, off)
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
        
        chaps = gen_chapters(name, c_data, orient, lp, s_data)
        pdf = create_pdf(name, chaps, c_data)
        
        # HTML GRID LAYOUT
        grid_html = ""
        for c in chaps:
            # HTML supports bold, so we convert markdown ** to <b>
            body_html = c['body'].replace("**", "<b>").replace("**", "</b>").replace("\n", "<br>")
            grid_html += f"""
            <div class="card">
                <h3>{c['title']}</h3>
                <p>{body_html}</p>
            </div>
            """
            
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
        <a href="data:application/pdf;base64,{pdf}" download="The_Legend_of_You.pdf" class="btn">⬇️ DOWNLOAD LEGEND</a>
        </body></html>
        """
        return {"report": html}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"report": "<h3>The stars are cloudy. Please try again.</h3>"}
