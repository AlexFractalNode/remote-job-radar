import requests
import json
import os
import time
import html

# --- KONFIGURATION ---
OUTPUT_DIR = 'job_board'
CACHE_FILE = 'ai_cache.json' # Hier merkt sich der Bot die Analysen
SITE_NAME = "RemoteRadar 📡"
BASE_URL = "https://dein-jobboard-name.netlify.app" # URL ANPASSEN!

# API Key sicher laden (Lokal oder von GitHub)
API_KEY = os.environ.get("GROQ_API")
MODEL_NAME = "llama-3.1-8b-instant"

# --- 1. DATEN HOLEN (ARBEITNOW) ---
print("📡 Rufe echte Job-Daten von Arbeitnow ab...")
try:
    response = requests.get("https://arbeitnow.com/api/job-board-api")
    jobs = response.json()['data']
    print(f"✅ {len(jobs)} Jobs geladen.")
except Exception as e:
    print(f"❌ API Fehler: {e}")
    jobs = []

# --- 2. SMART CACHE LADEN ---
ai_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            ai_cache = json.load(f)
        print(f"💾 Cache geladen: {len(ai_cache)} Jobs bereits analysiert.")
    except:
        print("⚠️ Cache war leer oder defekt.")

# --- 3. KI-FUNKTION (MIT RETRY) ---
def analyze_job_with_ai(job):
    if not API_KEY: return None # Ohne Key keine Analyse
    
    slug = job['slug']
    
    # CHECK: Haben wir den schon?
    if slug in ai_cache:
        return ai_cache[slug]

    print(f"🧠 Analysiere NEUEN Job: {job['title'][:30]}...")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"""
    Du bist ein HR-Experte für den deutschen Arbeitsmarkt.
    Analysiere diese Stellenanzeige:
    Titel: {job['title']}
    Firma: {job['company_name']}
    Ort: {job['location']}
    Beschreibung (Auszug): {job['description'][:500]}...
    
    AUFGABE:
    Antworte NUR mit JSON:
    {{
      "salary_estimate": "Geschätztes Jahresgehalt (z.B. '45.000€ - 60.000€' oder 'Marktüblich'). Sei realistisch für Deutschland.",
      "summary": "2 knackige Sätze, warum dieser Job spannend ist (Du-Form)."
    }}
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    # Retry Loop für 429 Errors
    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                content = r.json()['choices'][0]['message']['content']
                result = json.loads(content)
                
                # Speichern im Cache
                ai_cache[slug] = result
                return result
            elif r.status_code == 429:
                print("   ⏳ Rate Limit... warte 10s")
                time.sleep(10)
            else:
                print(f"   ❌ Fehler {r.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            time.sleep(2)
            
    return None

# --- 4. JOBS VERARBEITEN ---
processed_jobs_count = 0
for job in jobs:
    # Nur analysieren, wenn Key da ist
    analysis = analyze_job_with_ai(job)
    
    # Daten anreichern
    if analysis:
        job['salary_estimate'] = analysis.get('salary_estimate', 'Keine Angabe')
        job['summary'] = analysis.get('summary', '')
    else:
        job['salary_estimate'] = "Auf Anfrage"
        job['summary'] = "Klicke für mehr Details."
        
    # Cache zwischendurch speichern (falls Skript abstürzt)
    if processed_jobs_count % 5 == 0:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(ai_cache, f, ensure_ascii=False)
            
    # WICHTIG: Kleine Pause, um API zu schonen
    if job['slug'] not in ai_cache: # Nur warten, wenn wir die API wirklich genutzt haben
        time.sleep(2)

# Final Cache Save
with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(ai_cache, f, ensure_ascii=False)

# --- 5. HTML GENERIEREN (MIT NEUEN FELDERN) ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

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
    
print("🎉 Fertig! Gehaltsschätzungen eingebaut.")
