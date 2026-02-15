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
BASE_URL = "https://[AlexFractalNode].github.io/[remote-job-radar]"

# IMPRESSUM
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
        print(f"💾 Cache geladen: {len(ai_cache)} Jobs.")
    except:
        print("⚠️ Cache leer.")

# --- 3. KI-FUNKTION ---
def analyze_job_with_ai(job):
    if not API_KEY: return None
    slug = job['slug']
    if slug in ai_cache: return ai_cache[slug]

    print(f"🧠 Analysiere: {job['title'][:30]}...")
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
                time.sleep(wait)
            else: return None
        except Exception as e: time.sleep(5)
    return None

# --- 4. VERARBEITUNG & TAGS ---
new_jobs_analyzed = 0
all_tags_raw = []

for i, job in enumerate(jobs):
    slug = job['slug']
    job_tags = job.get('tags', [])
    all_tags_raw.extend(job_tags) # Sammeln für später
    
    # KI Logik
    if slug in ai_cache:
        analysis = ai_cache[slug]
    elif new_jobs_analyzed < MAX_NEW_JOBS_LIMIT:
        analysis = analyze_job_with_ai(job)
        if analysis:
            ai_cache[slug] = analysis
            new_jobs_analyzed += 1
            time.sleep(2) 
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

# Top Tags ermitteln (Cleaned)
top_tags = [tag for tag, count in Counter(all_tags_raw).most_common(15)]

# --- 5. SETUP HTML ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

# CSS Styles
css_styles = """
<style>
    :root { --primary: #2563eb; --background: #f8fafc; --text: #1e293b; --border: #e2e8f0; }
    body { background: var(--background); color: var(--text); font-family: system-ui, -apple-system, sans-serif; }
    nav { background: white; border-bottom: 1px solid var(--border); padding: 1rem 0; margin-bottom: 2rem; }
    .nav-container { display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto; padding: 0 1rem; }
    .logo { font-weight: 800; font-size: 1.5rem; text-decoration: none; color: var(--primary); }
    .nav-links a { color: #64748b; text-decoration: none; margin-left: 1rem; font-size: 0.9rem; }
    
    /* Chips */
    .filter-bar { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
    .filter-btn { 
        background: white; border: 1px solid #cbd5e1; padding: 4px 12px; border-radius: 99px; 
        text-decoration: none; font-size: 0.8rem; color: #475569; transition: all 0.2s; display:inline-block;
    }
    .filter-btn:hover, .filter-btn.active { border-color: var(--primary); color: var(--primary); background: #eff6ff; }

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
    
    footer { text-align: center; margin-top: 4rem; padding: 2rem; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); }
    footer a { color: #64748b; }
</style>
"""

# Template für Detailseiten
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
                <a href="index.html">Alle Jobs</a>
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
        </article>
    </main>
    <footer><a href="impressum.html">Impressum</a> • <a href="datenschutz.html">Datenschutz</a></footer>
</body>
</html>
"""

# Template für Landingpages (Index & Kategorien)
landing_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <title>{{ page_title }}</title>
    <meta name="description" content="{{ page_desc }}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {{ css_styles }}
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="index.html" class="logo">📡 {{ site_name }}</a>
            <div class="nav-links">
                <a href="impressum.html">Impressum</a>
            </div>
        </div>
    </nav>
    <main class="container">
        <div style="text-align:center; margin-bottom: 2rem;">
            <h1>{{ headline }}</h1>
            <p style="color:#64748b;">{{ subheadline }}</p>
        </div>
        
        <div class="filter-bar">
            <a href="index.html" class="filter-btn {{ active_all }}">Alle Jobs</a>
            {{ tag_buttons }}
        </div>

        <div id="job-grid">
            {{ job_cards }}
        </div>
    </main>
    <footer><a href="impressum.html">Impressum</a> • <a href="datenschutz.html">Datenschutz</a></footer>
</body>
</html>
"""

# --- 6. GENERIERUNG (Der Core) ---

# Hilfsfunktion: Job-Card HTML bauen
def build_card(job):
    tags_html = "".join([f'<span class="badge badge-tag">{t}</span>' for t in job.get('tags', [])])
    return f"""
    <a href="{job['slug']}.html" class="job-card">
        <div style="display:flex; justify-content:space-between;">
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

# A) Detailseiten bauen
for job in jobs:
    tags_html = "".join([f'<span class="badge badge-tag">{t}</span>' for t in job.get('tags', [])])
    html_content = job_template.replace("{{ title }}", job['title'])
    html_content = html_content.replace("{{ company }}", job['company_name'])
    html_content = html_content.replace("{{ site_name }}", SITE_NAME)
    html_content = html_content.replace("{{ salary }}", job.get('salary_estimate', ''))
    html_content = html_content.replace("{{ summary }}", job.get('summary', ''))
    html_content = html_content.replace("{{ description }}", job.get('description', ''))
    html_content = html_content.replace("{{ apply_url }}", job.get('url', '#'))
    html_content = html_content.replace("{{ css_styles }}", css_styles)
    html_content = html_content.replace("{{ tags_html }}", tags_html)
    
    with open(os.path.join(OUTPUT_DIR, f"{job['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

# B) Sitemap Vorbereitung
sitemap_urls = [f"{BASE_URL}/"]

# C) Landingpages bauen (Index + Tags)
# Wir erstellen eine Liste: "index" + alle Top Tags
pages_to_build = [{"tag": None, "filename": "index.html", "title": "Alle Jobs"}]
for t in top_tags:
    clean_filename = t.lower().replace(" ", "-").replace("/", "") + "-jobs.html"
    pages_to_build.append({"tag": t, "filename": clean_filename, "title": t})

for page in pages_to_build:
    current_tag = page['tag']
    filename = page['filename']
    
    # 1. Jobs filtern
    if current_tag:
        filtered_jobs = [j for j in jobs if current_tag in j.get('tags', [])]
        headline = f"{current_tag} Jobs"
        subheadline = f"Die besten {len(filtered_jobs)} offenen Stellen für {current_tag}."
        page_title = f"{current_tag} Jobs (Remote & Hybrid) | {SITE_NAME}"
        active_all = ""
    else:
        filtered_jobs = jobs # Alle
        headline = "Finde deinen Traumjob."
        subheadline = "KI-analysiert. Gehalts-geschätzt. Handverlesen."
        page_title = f"{SITE_NAME} - Die besten Tech & Remote Jobs"
        active_all = "active"

    # 2. Cards bauen
    cards_html = "".join([build_card(j) for j in filtered_jobs])
    
    # 3. Filter Buttons bauen (Diesmal sind es echte Links!)
    tag_btns_html = ""
    for t in top_tags:
        t_filename = t.lower().replace(" ", "-").replace("/", "") + "-jobs.html"
        is_active = "active" if t == current_tag else ""
        tag_btns_html += f'<a href="{t_filename}" class="filter-btn {is_active}">{t}</a> '

    # 4. HTML zusammenbauen
    html = landing_template.replace("{{ headline }}", headline)
    html = html.replace("{{ subheadline }}", subheadline)
    html = html.replace("{{ page_title }}", page_title)
    html = html.replace("{{ page_desc }}", f"Finde aktuelle {headline} bei {SITE_NAME}.")
    html = html.replace("{{ job_cards }}", cards_html)
    html = html.replace("{{ tag_buttons }}", tag_btns_html)
    html = html.replace("{{ active_all }}", active_all)
    html = html.replace("{{ site_name }}", SITE_NAME)
    html = html.replace("{{ css_styles }}", css_styles)

    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html)
    
    # Zur Sitemap hinzufügen
    sitemap_urls.append(f"{BASE_URL}/{filename}")

# D) Rechtstexte (Minimalversion)
for legal in ["impressum", "datenschutz"]:
    with open(os.path.join(OUTPUT_DIR, f"{legal}.html"), "w", encoding="utf-8") as f:
        f.write(f"<html><head><title>{legal}</title>{css_styles}</head><body><main class='container'><h1>{legal}</h1><p>{IMPRESSUM_NAME}<br>{IMPRESSUM_ADRESSE}</p><a href='index.html'>Zurück</a></main></body></html>")

# E) Sitemap generieren
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in sitemap_urls:
    sitemap_xml += f'  <url><loc>{url}</loc><changefreq>daily</changefreq></url>\n'
# Auch alle Detailseiten rein
for job in jobs:
    sitemap_xml += f'  <url><loc>{BASE_URL}/{job["slug"]}.html</loc><changefreq>daily</changefreq></url>\n'
sitemap_xml += '</urlset>'

with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

print(f"✅ Skalierung erfolgreich! {len(pages_to_build)} Landingpages generiert.")
