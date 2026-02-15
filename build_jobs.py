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

# IMPRESSUM DATEN
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

# --- 5. MODERNES DESIGN (CSS) ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

css_styles = """
<style>
    :root { 
        --primary: #4f46e5; --bg: #f8fafc; --text-main: #0f172a; --text-muted: #64748b;
        --border: #e2e8f0; --card-bg: #ffffff;
    }
    body { background: var(--bg); color: var(--text-main); font-family: 'Inter', system-ui, sans-serif; line-height: 1.5; margin: 0; }
    
    /* Nav */
    nav { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; padding: 1rem 0; }
    .nav-container { max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; display: flex; justify-content: space-between; align-items: center; }
    .logo { font-weight: 800; font-size: 1.25rem; text-decoration: none; color: var(--primary); }
    .nav-links a { color: var(--text-muted); text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; font-weight: 500; }
    .nav-links a:hover { color: var(--text-main); }

    /* Hero */
    .hero { text-align: center; padding: 4rem 1rem 2rem 1rem; }
    .hero h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--text-main); }
    .hero p { color: var(--text-muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto; }

    /* Chips */
    .filter-bar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin: 2rem auto; max-width: 800px; }
    .filter-btn { background: white; border: 1px solid var(--border); padding: 6px 16px; border-radius: 100px; text-decoration: none; font-size: 0.85rem; font-weight: 500; color: var(--text-muted); transition: all 0.2s; }
    .filter-btn:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-1px); }
    .filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

    /* Grid */
    .container { max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; }
    #job-grid { display: grid; gap: 1.5rem; grid-template-columns: 1fr; }
    @media (min-width: 768px) { #job-grid { grid-template-columns: repeat(auto-fill, minmax(45%, 1fr)); } }

    /* Card */
    .job-card { background: var(--card-bg); border: 1px solid var(--border); padding: 1.5rem; border-radius: 16px; text-decoration: none; color: inherit; display: flex; flex-direction: column; height: 100%; transition: all 0.2s; position: relative; }
    .job-card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border-color: var(--primary); }
    .job-title { margin: 0 0 0.5rem 0; font-size: 1.15rem; font-weight: 700; color: var(--text-main); }
    .company-name { font-size: 0.9rem; color: var(--text-muted); font-weight: 500; margin-bottom: 1rem; }
    .meta-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; }
    
    /* Badges */
    .badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 600; }
    .badge-salary { background: #ecfdf5; color: #047857; border: 1px solid #d1fae5; }
    .badge-tag { background: #f1f5f9; color: #64748b; }
    .ai-summary { background: #f8fafc; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-muted); border-left: 3px solid var(--primary); }

    /* Footer */
    footer { text-align: center; margin-top: 4rem; padding: 3rem 0; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); }
    footer a { color: #64748b; margin: 0 10px; }
    
    /* Detail Page */
    article { background: white; padding: 2.5rem; border-radius: 16px; border: 1px solid var(--border); }
    .apply-btn { background: var(--primary); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; width: 100%; display: block; text-align: center; text-decoration: none; margin-top: 2rem; }
    .apply-btn:hover { opacity: 0.9; }
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
    <main class="container" style="margin-top: 2rem;">
        <article>
            <header>
                <div style="color:var(--text-muted); font-weight:600;">{{ company }} sucht:</div>
                <h1 style="font-size:2rem; margin:0.5rem 0;">{{ title }}</h1>
                <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 1.5rem;">
                    <span class="badge badge-salary">💰 {{ salary }}</span>
                    {{ tags_html }}
                </div>
                <div class="ai-summary"><strong>🤖 KI-Einschätzung:</strong><br>{{ summary }}</div>
            </header>
            <hr style="border:0; border-top:1px solid #eee; margin:2rem 0;">
            <div style="line-height: 1.7;">{{ description }}</div>
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
        <div class="ai-summary" style="margin-top:0; font-size:0.8rem;">"{job.get('summary', '')[:90]}..."</div>
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
        headline, subheadline = f"{current_tag} Jobs", f"Die besten {len(filtered_jobs)} Stellen."
        page_title, active_all = f"{current_tag} Jobs | {SITE_NAME}", ""
    else:
        filtered_jobs, headline = jobs, "Finde deinen Traumjob."
        subheadline = "KI-analysiert. Gehalts-geschätzt. Handverlesen."
        page_title, active_all = f"{SITE_NAME} - Remote & Tech Jobs", "active"

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

# Legal & Sitemap
for legal in ["impressum", "datenschutz"]:
    with open(os.path.join(OUTPUT_DIR, f"{legal}.html"), "w", encoding="utf-8") as f:
        f.write(f"<html><head><title>{legal}</title>{css_styles}</head><body><nav><div class='nav-container'><a href='index.html' class='logo'>📡</a></div></nav><main class='container' style='margin-top:2rem'><h1>{legal}</h1><p>{IMPRESSUM_NAME}<br>{IMPRESSUM_ADRESSE}</p><a href='index.html'>← Zurück</a></main></body></html>")

sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in sitemap_urls: sitemap_xml += f'  <url><loc>{url}</loc><changefreq>daily</changefreq></url>\n'
for job in jobs: sitemap_xml += f'  <url><loc>{BASE_URL}/{job["slug"]}.html</loc><changefreq>daily</changefreq></url>\n'
sitemap_xml += '</urlset>'

with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f: f.write(sitemap_xml)

print(f"✅ Design Upgrade fertig! {len(pages_to_build)} Seiten generiert.")
