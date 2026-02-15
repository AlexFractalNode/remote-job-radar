import requests
import json
import os
import time
import html
from collections import Counter

# --- KONFIGURATION (HIER DEINE DATEN EINTRAGEN!) ---
OUTPUT_DIR = 'job_board'
CACHE_FILE = 'ai_cache.json'
SITE_NAME = "RemoteRadar 📡"

# Domain später hier eintragen
# Vorläufige GitHub URL (ersetze [...] mit deinen Daten)
BASE_URL = "https://[AlexFractalNode].github.io/[remote-job-radar]"

# FÜR DAS IMPRESSUM (Bitte ausfüllen)
IMPRESSUM_NAME = "Alexander Heinze"
IMPRESSUM_ADRESSE = "Am Fuchsgraben 28, 08056 Zwickau"
IMPRESSUM_EMAIL = "alexander.heinze.01@gmail.com"

# EINSTELLUNGEN
MAX_NEW_JOBS_LIMIT = 20
API_KEY = os.environ.get("GROQ_API")
MODEL_NAME = "llama-3.1-8b-instant"

# --- 1. DATEN HOLEN ---
print("📡 Rufe echte Job-Daten von Arbeitnow ab...")
try:
    response = requests.get("https://arbeitnow.com/api/job-board-api")
    jobs = response.json()['data']
    print(f"✅ {len(jobs)} Jobs geladen.")
except Exception as e:
    print(f"❌ API Fehler: {e}")
    jobs = []

# --- 2. CACHE LADEN ---
ai_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            ai_cache = json.load(f)
        print(f"💾 Cache geladen: {len(ai_cache)} Jobs bereits analysiert.")
    except:
        print("⚠️ Cache leer.")

# --- 3. KI-FUNKTION ---
def analyze_job_with_ai(job):
    if not API_KEY: return None
    slug = job['slug']
    if slug in ai_cache: return ai_cache[slug]

    print(f"🧠 Analysiere NEUEN Job: {job['title'][:30]}...")
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    
    prompt = f"""
    Analysiere als HR-Experte kurz:
    Titel: {job['title']}
    Firma: {job['company_name']}
    Beschreibung: {job['description'][:400]}...
    
    ANTWORTE NUR JSON:
    {{
      "salary_estimate": "Geschätzt in Euro (z.B. '50k-60k'). Sei realistisch.",
      "summary": "2 knackige Sätze warum man sich bewerben soll."
    }}
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                try: return json.loads(r.json()['choices'][0]['message']['content'])
                except: return None
            elif r.status_code == 429:
                wait = (attempt + 1) * 20
                print(f"   ⏳ Rate Limit... warte {wait}s")
                time.sleep(wait)
            else: return None
        except Exception as e: time.sleep(5)
    return None

# --- 4. JOBS VERARBEITEN ---
new_jobs_analyzed = 0
all_tags = [] 

for i, job in enumerate(jobs):
    slug = job['slug']
    
    # Tags sammeln 
    job_tags = job.get('tags', [])
    all_tags.extend(job_tags)
    
    # KI Analyse Logik
    if slug in ai_cache:
        analysis = ai_cache[slug]
    elif new_jobs_analyzed < MAX_NEW_JOBS_LIMIT:
        analysis = analyze_job_with_ai(job)
        if analysis:
            ai_cache[slug] = analysis
            new_jobs_analyzed += 1
            time.sleep(3) 
    else:
        analysis = None

    if analysis:
        raw_summary = analysis.get('summary', '')
        job['summary'] = " ".join(raw_summary) if isinstance(raw_summary, list) else str(raw_summary)
        job['salary_estimate'] = analysis.get('salary_estimate', 'k.A.')
    else:
        job['salary_estimate'] = "Auf Anfrage"
        job['summary'] = "KI-Analyse folgt..."

    if i % 5 == 0:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(ai_cache, f, ensure_ascii=False)

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(ai_cache, f, ensure_ascii=False)

# Top 12 Tags (etwas mehr, da sie jetzt kleiner sind)
top_tags = [tag for tag, count in Counter(all_tags).most_common(12)]

# --- 5. HTML GENERATOR ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

# CSS (OPTIMIERT FÜR KLEINE TAGS)
css_styles = """
<style>
    :root { --primary: #2563eb; --background: #f8fafc; --text: #1e293b; --border: #e2e8f0; }
    body { background: var(--background); color: var(--text); font-family: system-ui, -apple-system, sans-serif; }
    
    /* Navigation */
    nav { background: white; border-bottom: 1px solid var(--border); padding: 1rem 0; margin-bottom: 2rem; }
    .nav-container { display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; padding: 0 1rem; }
    .logo { font-weight: 800; font-size: 1.5rem; text-decoration: none; color: var(--primary); }
    .nav-links a { color: #64748b; text-decoration: none; margin-left: 1rem; font-size: 0.9rem; }
    
    /* --- NEUES FILTER DESIGN (CHIPS) --- */
    .filter-container {
        max-width: 800px; margin: 0 auto 2rem auto; text-align: center;
    }
    .filter-label {
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 0.5rem; display: block; font-weight: bold;
    }
    .filter-bar { 
        display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; 
    }
    .filter-btn { 
        background: white; 
        border: 1px solid #cbd5e1; 
        padding: 4px 12px;           /* Kleineres Padding */
        border-radius: 99px;         /* Pill Shape (ganz rund) */
        cursor: pointer; 
        font-size: 0.8rem;           /* Kleinere Schrift */
        color: #475569;
        transition: all 0.2s;
        font-weight: 500;
    }
    .filter-btn:hover { 
        border-color: var(--primary); color: var(--primary); transform: translateY(-1px);
    }
    .filter-btn.active { 
        background: var(--primary); color: white; border-color: var(--primary); 
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }

    /* Job Cards */
    .job-card { 
        background: white; border: 1px solid var(--border); padding: 1.5rem; margin-bottom: 1rem; 
        border-radius: 12px; text-decoration: none; color: inherit; display: block; 
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .job-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: var(--primary); }
    
    .badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; margin-right: 5px; }
    .badge-salary { background: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
    .badge-tag { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    
    .ai-summary { background: #f8fafc; padding: 0.8rem; border-radius: 8px; margin-top: 1rem; font-size: 0.9rem; color: #334155; border-left: 3px solid var(--primary); }
    
    /* Footer */
    footer { text-align: center; margin-top: 4rem; padding: 2rem; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); }
    footer a { color: #64748b; }
</style>
"""

# HTML TEMPLATE
job_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | {{ site_name }}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {{ css_styles }}
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="index.html" class="logo">📡 {{ site_name }}</a>
            <div class="nav-links">
                <a href="index.html">Jobs</a>
                <a href="impressum.html">Impressum</a>
            </div>
        </div>
    </nav>
    <main class="container">
        <article>
            <header>
                <small>{{ company }}</small>
                <h1>{{ title }}</h1>
                <div style="margin: 0.5rem 0;">
                    <span class="badge badge-salary">💰 {{ salary }}</span>
                    {{ tags_html }}
                </div>
                <div class="ai-summary">🤖 <strong>KI-Fazit:</strong> {{ summary }}</div>
            </header>
            <div style="margin: 2rem 0;">{{ description }}</div>
            <a href="{{ apply_url }}" target="_blank" role="button" style="width:100%; text-align:center;">Jetzt bewerben ↗</a>
            <small style="display:block; text-align:center; margin-top:1rem; color:#94a3b8;">Weiterleitung zur Firmenseite</small>
        </article>
    </main>
    <footer>
        <a href="impressum.html">Impressum</a> • <a href="datenschutz.html">Datenschutz</a>
    </footer>
</body>
</html>
"""

# 6. HTML GENERIEREN
index_cards = ""

for job in jobs:
    filename = f"{job['slug']}.html"
    
    tags_list = job.get('tags', [])
    tags_html = "".join([f'<span class="badge badge-tag">{t}</span>' for t in tags_list])
    
    # Filter-Klassen
    filter_classes = " ".join([t.lower().replace(' ', '-').replace('&', '').replace('/', '') for t in tags_list])

    # Detailseite
    html = job_template.replace("{{ title }}", job['title'])
    html = html.replace("{{ company }}", job['company_name'])
    html = html.replace("{{ site_name }}", SITE_NAME)
    html = html.replace("{{ salary }}", job.get('salary_estimate', ''))
    html = html.replace("{{ summary }}", job.get('summary', ''))
    html = html.replace("{{ description }}", job.get('description', ''))
    html = html.replace("{{ apply_url }}", job.get('url', '#'))
    html = html.replace("{{ css_styles }}", css_styles)
    html = html.replace("{{ tags_html }}", tags_html)
    
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html)

    # Index Karte
    index_cards += f"""
    <a href="{filename}" class="job-card {filter_classes}">
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <h3 style="margin:0; font-size:1.1rem; color:var(--primary);">{job['title']}</h3>
            <small style="color:#64748b;">{job['location']}</small>
        </div>
        <div style="margin:0.5rem 0; font-weight:600; color:#334155;">{job['company_name']}</div>
        <div style="margin-bottom:0.8rem;">
            <span class="badge badge-salary">💰 {job.get('salary_estimate', '')}</span>
            {tags_html}
        </div>
        <div style="font-size:0.9rem; color:#475569;">🤖 {job.get('summary', '')[:120]}...</div>
    </a>
    """

# 7. INDEX HTML
filter_buttons = '<button class="filter-btn active" onclick="filterSelection(\'all\')">Alle</button>'
for tag in top_tags:
    safe_tag = tag.lower().replace(' ', '-').replace('&', '').replace('/', '')
    filter_buttons += f'<button class="filter-btn" onclick="filterSelection(\'{safe_tag}\')">{tag}</button>'

index_html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <title>{SITE_NAME} - Jobs</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {css_styles}
    <script>
    function filterSelection(c) {{
        var x, i;
        x = document.getElementsByClassName("job-card");
        var btns = document.getElementsByClassName("filter-btn");
        
        // Active State setzen
        for (i = 0; i < btns.length; i++) {{
            // Einfacher Check: Wenn der Button-Text im angeklickten Tag enthalten ist
            if (btns[i].innerText.toLowerCase().replace(' ', '-') === c || (c === 'all' && btns[i].innerText === 'Alle')) {{
                btns[i].classList.add("active");
            }} else {{
                btns[i].classList.remove("active");
            }}
        }}

        if (c == "all") c = "";
        for (i = 0; i < x.length; i++) {{
            w3RemoveClass(x[i], "show");
            if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
        }}
    }}
    
    function w3AddClass(element, name) {{
        var i, arr1, arr2;
        arr1 = element.className.split(" ");
        arr2 = name.split(" ");
        for (i = 0; i < arr2.length; i++) {{
            if (arr1.indexOf(arr2[i]) == -1) {{element.className += " " + arr2[i];}}
        }}
    }}
    
    function w3RemoveClass(element, name) {{
        var i, arr1, arr2;
        arr1 = element.className.split(" ");
        arr2 = name.split(" ");
        for (i = 0; i < arr2.length; i++) {{
            while (arr1.indexOf(arr2[i]) > -1) {{
                arr1.splice(arr1.indexOf(arr2[i]), 1);     
            }}
        }}
        element.className = arr1.join(" ");
    }}
    window.onload = function() {{ filterSelection('all'); }};
    </script>
    <style>
    .job-card {{ display: none; }}
    .show {{ display: block; animation: fadeIn 0.4s; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="#" class="logo">📡 {SITE_NAME}</a>
            <div class="nav-links">
                <a href="impressum.html">Impressum</a>
            </div>
        </div>
    </nav>
    <main class="container">
        <div style="text-align:center; margin-bottom: 2rem;">
            <h1>Finde deinen nächsten Job.</h1>
            <p style="color:#64748b;">KI-analysiert. Gehalts-geschätzt. Handverlesen.</p>
        </div>
        
        <div class="filter-container">
            <span class="filter-label">Beliebte Themen:</span>
            <div class="filter-bar">
                {filter_buttons}
            </div>
        </div>

        <div id="job-grid">
            {index_cards}
        </div>
    </main>
    <footer>
        <a href="impressum.html">Impressum</a> • <a href="datenschutz.html">Datenschutz</a>
    </footer>
</body>
</html>
"""

# 8. RECHTSTEXTE
impressum_html = f"""
<!DOCTYPE html>
<html><head><title>Impressum</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">{css_styles}</head>
<body>
<main class="container" style="padding-top:2rem;">
<h1>Impressum</h1>
<p>Angaben gemäß § 5 TMG</p>
<p><strong>{IMPRESSUM_NAME}</strong><br>{IMPRESSUM_ADRESSE}</p>
<p><strong>Kontakt:</strong><br>E-Mail: {IMPRESSUM_EMAIL}</p>
<p><a href="index.html">⬅ Zurück zur Startseite</a></p>
</main></body></html>
"""

datenschutz_html = f"""
<!DOCTYPE html>
<html><head><title>Datenschutz</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">{css_styles}</head>
<body>
<main class="container" style="padding-top:2rem;">
<h1>Datenschutzerklärung</h1>
<p>Wir speichern keine persönlichen Daten. Diese Seite hostet keine Cookies.</p>
<p>Verantwortlich:<br>{IMPRESSUM_NAME}<br>{IMPRESSUM_ADRESSE}</p>
<p><a href="index.html">⬅ Zurück zur Startseite</a></p>
</main></body></html>
"""

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(index_html)
with open(os.path.join(OUTPUT_DIR, "impressum.html"), "w", encoding="utf-8") as f: f.write(impressum_html)
with open(os.path.join(OUTPUT_DIR, "datenschutz.html"), "w", encoding="utf-8") as f: f.write(datenschutz_html)

print("✅ Update fertig: Design optimiert (Chips) & Rechtstexte aktualisiert!")

