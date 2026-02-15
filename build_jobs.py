import requests
import json
import os
import time
import html

# --- KONFIGURATION ---
OUTPUT_DIR = 'job_board'
CACHE_FILE = 'ai_cache.json'
SITE_NAME = "RemoteRadar 📡"
BASE_URL = "https://dein-jobboard-name.netlify.app" 

# SICHERHEIT: Max. 20 KI-Analysen pro Lauf
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
    
    if slug in ai_cache:
        return ai_cache[slug]

    print(f"🧠 Analysiere NEUEN Job: {job['title'][:30]}...")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Prompt
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
    
    # Retry Loop
    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                try:
                    return json.loads(r.json()['choices'][0]['message']['content'])
                except:
                    return None # Falls JSON kaputt ist
            elif r.status_code == 429:
                wait = (attempt + 1) * 20 
                print(f"   ⏳ Rate Limit... warte {wait}s")
                time.sleep(wait)
            else:
                return None
        except Exception as e:
            time.sleep(5)
    return None

# --- 4. JOBS VERARBEITEN ---
new_jobs_analyzed = 0

for i, job in enumerate(jobs):
    slug = job['slug']
    
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
        # Hier stellen wir sicher, dass summary ein String ist (DER FIX)
        raw_summary = analysis.get('summary', '')
        if isinstance(raw_summary, list):
            job['summary'] = " ".join(raw_summary)
        else:
            job['summary'] = str(raw_summary)
            
        job['salary_estimate'] = analysis.get('salary_estimate', 'k.A.')
    else:
        job['salary_estimate'] = "Auf Anfrage"
        job['summary'] = "KI-Analyse folgt..."

    if i % 5 == 0:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(ai_cache, f, ensure_ascii=False)

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(ai_cache, f, ensure_ascii=False)

print(f"🏁 Fertig. Heute {new_jobs_analyzed} neue Jobs analysiert.")

# --- 5. HTML GENERIEREN ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

# CSS TEMPLATE
css_styles = """
<style>
    :root { --primary: #2563eb; --background: #f8fafc; }
    body { background: var(--background); font-family: sans-serif; }
    .job-card { background: white; border: 1px solid #e2e8f0; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; text-decoration: none; color: inherit; display: block; transition: transform 0.2s; }
    .job-card:hover { transform: translateY(-3px); border-color: var(--primary); }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
    .badge-salary { background: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
    .ai-summary { font-style: italic; color: #64748b; margin-top: 0.5rem; font-size: 0.9rem; border-left: 3px solid #cbd5e1; padding-left: 10px; }
</style>
"""

# HTML JOB TEMPLATE (Das fehlte vorhin!)
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
    <nav class="container-fluid">
        <ul><li><strong><a href="index.html">📡 RemoteRadar</a></strong></li></ul>
    </nav>
    <main class="container">
        <article>
            <header>
                <small>{{ company }}</small>
                <h1>{{ title }}</h1>
                <p>📍 {{ location }} <span class="badge badge-salary">💰 {{ salary }}</span></p>
                <div class="ai-summary">🤖 KI-Fazit: {{ summary }}</div>
            </header>
            <div style="margin: 2rem 0;">{{ description }}</div>
            <a href="{{ apply_url }}" target="_blank" role="button">Jetzt bewerben ↗</a>
        </article>
    </main>
</body>
</html>
"""

index_cards = ""
for job in jobs:
    filename = f"{job['slug']}.html"
    
    # HTML Detailseite
    html_content = job_template.replace("{{ title }}", job['title'])
    html_content = html_content.replace("{{ company }}", job['company_name'])
    html_content = html_content.replace("{{ location }}", job['location'])
    html_content = html_content.replace("{{ site_name }}", SITE_NAME)
    html_content = html_content.replace("{{ salary }}", job.get('salary_estimate', ''))
    html_content = html_content.replace("{{ summary }}", job.get('summary', ''))
    html_content = html_content.replace("{{ description }}", job.get('description', ''))
    html_content = html_content.replace("{{ apply_url }}", job.get('url', '#'))
    html_content = html_content.replace("{{ css_styles }}", css_styles)
    
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # Index Karte
    salary_badge = f'<span class="badge badge-salary">💰 {job.get("salary_estimate", "")}</span>'
    index_cards += f"""
    <a href="{filename}" class="job-card">
        <h3 style="margin:0; font-size:1.2rem;">{job['title']}</h3>
        <div style="color:#64748b; margin:0.5rem 0;">{job['company_name']} • {job['location']}</div>
        <div style="margin-top:0.5rem;">{salary_badge}</div>
        <div class="ai-summary">{job.get('summary', '')}</div>
    </a>
    """

# Index HTML
index_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{SITE_NAME}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {css_styles}
</head>
<body>
    <main class="container">
        <h1 style="text-align:center; margin:3rem 0;">📡 RemoteRadar <br><small>KI-Powered Job Board</small></h1>
        {index_cards}
    </main>
</body>
</html>
"""

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
