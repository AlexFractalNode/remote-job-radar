import requests
import json
import os
import time
from collections import Counter

# --- KONFIGURATION ---
OUTPUT_DIR = 'job_board'
CACHE_FILE = 'ai_cache.json'
SITE_NAME = "RemoteRadar 📡"
BASE_URL = "https://[AlexFractalNode].github.io/[remote-job-radar]"

# IMPRESSUM DATEN (Wird automatisch in die Rechtstexte eingefügt)
IMPRESSUM_NAME = "Alexander Heinze"
IMPRESSUM_ADRESSE = "Am Fuchsgraben 28, 08056 Zwickau"
IMPRESSUM_EMAIL = "alexander.heinze.01@gmail.com"
IMPRESSUM_TELEFON = "+49 15231751760" # Optional

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
                time.sleep((attempt + 1) * 20)
            else: return None
        except Exception as e: time.sleep(5)
    return None

# --- 4. VERARBEITUNG ---
new_jobs_analyzed = 0
all_tags_raw = []

for i, job in enumerate(jobs):
    slug = job['slug']
    job_tags = job.get('tags', [])
    all_tags_raw.extend(job_tags)
    
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

top_tags = [tag for tag, count in Counter(all_tags_raw).most_common(15)]

# --- 5. MODERNES DESIGN (CSS FIX) ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

css_styles = """
<style>
    :root { 
        --primary: #4f46e5; --bg: #f8fafc; --text-main: #0f172a; --text-muted: #64748b;
        --border: #e2e8f0; --card-bg: #ffffff;
    }
    body { background: var(--bg); color: var(--text-main); font-family: 'Inter', system-ui, sans-serif; line-height: 1.5; margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
    
    /* Nav */
    nav { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; padding: 1rem 0; }
    .nav-container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; display: flex; justify-content: space-between; align-items: center; }
    .logo { font-weight: 800; font-size: 1.4rem; text-decoration: none; color: var(--primary); }
    .nav-links a { color: var(--text-muted); text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; font-weight: 500; }
    .nav-links a:hover { color: var(--primary); }

    /* Hero */
    .hero { text-align: center; padding: 4rem 1rem 2rem 1rem; }
    .hero h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--text-main); letter-spacing: -1px; }
    .hero p { color: var(--text-muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto; }

    /* Chips */
    .filter-bar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin: 2rem auto; max-width: 900px; }
    .filter-btn { background: white; border: 1px solid var(--border); padding: 8px 18px; border-radius: 100px; text-decoration: none; font-size: 0.85rem; font-weight: 500; color: var(--text-muted); transition: all 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .filter-btn:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

    /* GRID FIX: Hier verhindern wir das Überlappen! */
    .container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; width: 100%; box-sizing: border-box; }
    #job-grid { 
        display: grid; 
        gap: 2rem; /* Mehr Platz zwischen den Boxen */
        /* Automatische Spalten, aber mindestens 320px breit -> Kein Quetschen mehr */
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
    }

    /* Card */
    .job-card { 
        background: var(--card-bg); 
        border: 1px solid var(--border); 
        padding: 1.5rem; 
        border-radius: 16px; 
        text-decoration: none; 
        color: inherit; 
        display: flex; 
        flex-direction: column; 
        height: 100%; /* Wichtig für gleiche Höhe */
        transition: all 0.2s; 
        position: relative;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .job-card:hover { transform: translateY(-5px); box-shadow: 0 12px 25px -5px rgba(0,0,0,0.1); border-color: var(--primary); }
    
    .job-title { margin: 0 0 0.5rem 0; font-size: 1.15rem; font-weight: 700; color: var(--text-main); line-height: 1.3; }
    .company-name { font-size: 0.9rem; color: var(--text-muted); font-weight: 500; margin-bottom: 1rem; display: flex; align-items: center; gap: 5px; }
    
    .ai-summary { background: #f8fafc; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-muted); border-left: 3px solid var(--primary); line-height: 1.5; }
    
    /* Footer & Meta */
    .meta-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: auto; /* Drückt Tags nach unten */ }
    
    .badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-salary { background: #ecfdf5; color: #047857; border: 1px solid #d1fae5; }
    .badge-tag { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }

    footer { text-align: center; margin-top: auto; padding: 4rem 0; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); background: white; }
    footer a { color: #64748b; margin: 0 10px; text-decoration: none; }
    footer a:hover { color: var(--primary); }
    
    /* Legal Pages */
    .legal-content h1 { margin-bottom: 2rem; }
    .legal-content h2 { margin-top: 2rem; font-size: 1.2rem; }
    .legal-content p { margin-bottom: 1rem; color: #475569; }
    
    /* Detail Page */
    article { background: white; padding: 2.5rem; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .apply-btn { background: var(--primary); color: white; border: none; padding: 14px 24px; border-radius: 12px; font-weight: 600; width: 100%; display: block; text-align: center; text-decoration: none; margin-top: 2rem; transition: background 0.2s; }
    .apply-btn:hover { background: #4338ca; }
</style>
"""

# --- 6. TEMPLATES & BUILD ---

job_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | {{ site_name }}</title>
    {{ css_styles }}
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="index.html" class="logo">📡 {{ site_name }}</a>
            <div class="nav-links"><a href="index.html">← Zur Übersicht</a></div>
        </div>
    </nav>
    <main class="container" style="margin-top: 2rem; margin-bottom: 2rem;">
        <article>
            <header>
                <div style="color:var(--text-muted); font-weight:600; margin-bottom: 0.5rem;">{{ company }} sucht:</div>
                <h1 style="font-size:2rem; margin:0 0 1rem 0;">{{ title }}</h1>
                <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 1.5rem;">
                    <span class="badge badge-salary">💰 {{ salary }}</span>
                    {{ tags_html }}
                </div>
                <div class="ai-summary"><strong>🤖 KI-Einschätzung:</strong><br>{{ summary }}</div>
            </header>
            <hr style="border:0; border-top:1px solid #eee; margin:2rem 0;">
            <div style="line-height: 1.8; color: #334155;">{{ description }}</div>
            <a href="{{ apply_url }}" target="_blank" class="apply-btn">Jetzt bewerben ↗</a>
        </article>
    </main>
    <footer><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></footer>
</body>
</html>
"""

landing_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <title>{{ page_title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {{ css_styles }}
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="index.html" class="logo">📡 {{ site_name }}</a>
            <div class="nav-links"><a href="impressum.html">Rechtliches</a></div>
        </div>
    </nav>
    <div class="hero">
        <h1>{{ headline }}</h1>
        <p>{{ subheadline }}</p>
    </div>
    <main class="container">
        <div class="filter-bar">
            <a href="index.html" class="filter-btn {{ active_all }}">Alle Jobs</a>
            {{ tag_buttons }}
        </div>
        <div id="job-grid">{{ job_cards }}</div>
    </main>
    <footer><p>&copy; 2025 {{ site_name }}</p><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></footer>
</body>
</html>
"""

def build_card(job):
    tags = job.get('tags', [])[:3]
    tags_html = "".join([f'<span class="badge badge-tag">{t}</span>' for t in tags])
    return f"""
    <a href="{job['slug']}.html" class="job-card">
        <div style="margin-bottom:1rem;">
            <h3 class="job-title">{job['title']}</h3>
            <div class="company-name">🏢 {job['company_name']} • 📍 {job['location']}</div>
        </div>
        <div class="ai-summary" style="margin-top:0; font-size:0.85rem;">"{job.get('summary', '')[:90]}..."</div>
        <div class="meta-tags">
            <span class="badge badge-salary">💰 {job.get('salary_estimate', 'k.A.')}</span>
            {tags_html}
        </div>
    </a>
    """

# Build Process
for job in jobs:
    tags_html = "".join([f'<span class="badge badge-tag">{t}</span>' for t in job.get('tags', [])])
    html = job_template.replace("{{ title }}", job['title']) \
        .replace("{{ company }}", job['company_name']) \
        .replace("{{ site_name }}", SITE_NAME) \
        .replace("{{ salary }}", job.get('salary_estimate', '')) \
        .replace("{{ summary }}", job.get('summary', '')) \
        .replace("{{ description }}", job.get('description', '')) \
        .replace("{{ apply_url }}", job.get('url', '#')) \
        .replace("{{ css_styles }}", css_styles) \
        .replace("{{ tags_html }}", tags_html)
    with open(os.path.join(OUTPUT_DIR, f"{job['slug']}.html"), "w", encoding="utf-8") as f: f.write(html)

pages_to_build = [{"tag": None, "filename": "index.html", "title": "Alle Jobs"}]
for t in top_tags:
    clean_filename = t.lower().replace(" ", "-").replace("/", "") + "-jobs.html"
    pages_to_build.append({"tag": t, "filename": clean_filename, "title": t})

sitemap_urls = [f"{BASE_URL}/"]

for page in pages_to_build:
    current_tag = page['tag']
    if current_tag:
        filtered_jobs = [j for j in jobs if current_tag in j.get('tags', [])]
        headline, subheadline = f"{current_tag} Jobs", f"Die besten {len(filtered_jobs)} Stellen für {current_tag}."
        page_title, active_all = f"{current_tag} Jobs | {SITE_NAME}", ""
    else:
        filtered_jobs, headline = jobs, "Finde deinen Traumjob."
        subheadline = "KI-analysiert. Gehalts-geschätzt. Handverlesen.",
        page_title, active_all = f"{SITE_NAME} - Remote & Tech Jobs", "active"
        if isinstance(subheadline, tuple): subheadline = subheadline[0]

    cards_html = "".join([build_card(j) for j in filtered_jobs])
    tag_btns_html = ""
    for t in top_tags:
        t_filename = t.lower().replace(" ", "-").replace("/", "") + "-jobs.html"
        is_active = "active" if t == current_tag else ""
        tag_btns_html += f'<a href="{t_filename}" class="filter-btn {is_active}">{t}</a> '

    html = landing_template.replace("{{ headline }}", headline) \
        .replace("{{ subheadline }}", subheadline) \
        .replace("{{ page_title }}", page_title) \
        .replace("{{ job_cards }}", cards_html) \
        .replace("{{ tag_buttons }}", tag_btns_html) \
        .replace("{{ active_all }}", active_all) \
        .replace("{{ site_name }}", SITE_NAME) \
        .replace("{{ css_styles }}", css_styles)
    
    with open(os.path.join(OUTPUT_DIR, page['filename']), "w", encoding="utf-8") as f: f.write(html)
    sitemap_urls.append(f"{BASE_URL}/{page['filename']}")

# --- RECHTSTEXTE (Ausführlicher Generator) ---
impressum_content = f"""
<h1>Impressum</h1>
<p>Angaben gemäß § 5 TMG</p>
<p><strong>{IMPRESSUM_NAME}</strong><br>{IMPRESSUM_ADRESSE}</p>
<p><strong>Kontakt:</strong><br>E-Mail: {IMPRESSUM_EMAIL}<br>Telefon: {IMPRESSUM_TELEFON}</p>
<p><strong>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:</strong><br>{IMPRESSUM_NAME}<br>{IMPRESSUM_ADRESSE}</p>
<p><strong>Haftungsausschluss:</strong><br>Die Inhalte dieser Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen.</p>
"""

datenschutz_content = f"""
<h1>Datenschutzerklärung</h1>
<h2>1. Datenschutz auf einen Blick</h2>
<p><strong>Allgemeine Hinweise</strong><br>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.</p>
<p><strong>Verantwortliche Stelle:</strong><br>{IMPRESSUM_NAME}<br>{IMPRESSUM_ADRESSE}<br>{IMPRESSUM_EMAIL}</p>

<h2>2. Datenerfassung auf unserer Website</h2>
<p><strong>Server-Log-Dateien</strong><br>Der Provider der Seiten (GitHub Pages) erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, die Ihr Browser automatisch an uns übermittelt. Dies sind: Browsertyp, Betriebssystem, Referrer URL, Hostname des zugreifenden Rechners, Uhrzeit der Serveranfrage, IP-Adresse.</p>
<p>Eine Zusammenführung dieser Daten mit anderen Datenquellen wird nicht vorgenommen. Grundlage für die Datenverarbeitung ist Art. 6 Abs. 1 lit. f DSGVO.</p>

<h2>3. Externe Links</h2>
<p>Diese Webseite verlinkt auf externe Jobangebote. Wenn Sie auf "Jetzt bewerben" klicken, verlassen Sie unser Angebot. Wir haben keinen Einfluss auf die Einhaltung der Datenschutzbestimmungen durch den fremden Anbieter.</p>
"""

# HTML Wrapper für Rechtstexte
def build_legal_page(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="de">
    <head><title>{title} | {SITE_NAME}</title><meta name="viewport" content="width=device-width, initial-scale=1">{css_styles}</head>
    <body>
        <nav><div class="nav-container"><a href="index.html" class="logo">📡 {SITE_NAME}</a></div></nav>
        <main class="container legal-content" style="margin-top:3rem; max-width:800px;">
            {content}
            <div style="margin-top:3rem;"><a href="index.html" class="filter-btn">← Zurück zur Startseite</a></div>
        </main>
        <footer><p>&copy; 2025 {SITE_NAME}</p><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></footer>
    </body>
    </html>
    """

with open(os.path.join(OUTPUT_DIR, "impressum.html"), "w", encoding="utf-8") as f: f.write(build_legal_page("Impressum", impressum_content))
with open(os.path.join(OUTPUT_DIR, "datenschutz.html"), "w", encoding="utf-8") as f: f.write(build_legal_page("Datenschutz", datenschutz_content))

# Sitemap Final
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in sitemap_urls: sitemap_xml += f'  <url><loc>{url}</loc><changefreq>daily</changefreq></url>\n'
for job in jobs: sitemap_xml += f'  <url><loc>{BASE_URL}/{job["slug"]}.html</loc><changefreq>daily</changefreq></url>\n'
sitemap_xml += '</urlset>'
with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f: f.write(sitemap_xml)

print(f"✅ Update fertig! Grid repariert & Rechtstexte erweitert.")
