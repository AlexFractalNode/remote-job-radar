import requests
import json
import os
import time
import html
from collections import Counter

# --- KONFIGURATION (DEINE DATEN) ---
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

# Top 15 Tags
top_tags = [tag for tag, count in Counter(all_tags_raw).most_common(15)]

# --- 5. MODERNES DESIGN (CSS) ---
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

css_styles = """
<style>
    :root { 
        --primary: #4f46e5; /* Modernes Indigo */
        --primary-hover: #4338ca;
        --bg: #f8fafc; 
        --text-main: #0f172a; 
        --text-muted: #64748b;
        --border: #e2e8f0;
        --card-bg: #ffffff;
    }
    
    body { 
        background: var(--bg); 
        color: var(--text-main); 
        font-family: 'Inter', system-ui, -apple-system, sans-serif; 
        line-height: 1.5;
        margin: 0;
    }

    /* Navbar */
    nav { 
        background: rgba(255, 255, 255, 0.8); 
        backdrop-filter: blur(10px); /* Glassmorphism Effekt */
        border-bottom: 1px solid var(--border); 
        position: sticky; 
        top: 0; 
        z-index: 100;
        padding: 1rem 0;
    }
    .nav-container { 
        max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; 
        display: flex; justify-content: space-between; align-items: center; 
    }
    .logo { font-weight: 800; font-size: 1.25rem; text-decoration: none; color: var(--primary); letter-spacing: -0.5px; }
    .nav-links a { color: var(--text-muted); text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; font-weight: 500; transition: color 0.2s;}
    .nav-links a:hover { color: var(--text-main); }

    /* Hero Section */
    .hero { text-align: center; padding: 4rem 1rem 2rem 1rem; }
    .hero h1 { font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0.5rem; color: var(--text-main); }
    .hero p { color: var(--text-muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto; }

    /* Filter Chips (Modern Pills) */
    .filter-bar { 
        display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; 
        margin: 2rem auto; max-width: 800px; 
    }
    .filter-btn { 
        background: white; 
        border: 1px solid var(--border); 
        padding: 6px 16px; 
        border-radius: 100px; /* Pill Shape */
        text-decoration: none; 
        font-size: 0.85rem; 
        font-weight: 500;
        color: var(--text-muted); 
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .filter-btn:hover { 
        transform: translateY(-1px); 
        border-color: var(--primary); 
        color: var(--primary); 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .filter-btn.active { 
        background: var(--primary); 
        color: white; 
        border-color: var(--primary); 
    }

    /* Grid Layout */
    .container { max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; }
    #job-grid { display: grid; gap: 1.5rem; grid-template-columns: 1fr; }
    @media (min-width: 768px) { #job-grid { grid-template-columns: repeat(auto-fill, minmax(45%, 1fr)); } }

    /* Job Card (Modern) */
    .job-card { 
        background: var(--card-bg); 
        border: 1px solid var(--border); 
        padding: 1.5rem; 
        border-radius: 16px; /* Mehr Rundung */
        text-decoration: none; 
        color: inherit; 
        display: flex; flex-direction: column; height: 100%;
        transition: all 0.2s ease;
        position: relative;
    }
    .job-card:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: var(--primary);
    }
    
    .card-header { margin-bottom: 1rem; }
    .job-title { margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-main); line-height: 1.3; }
    .company-name { font-size: 0.9rem; color: var(--text-muted); font-weight: 500; margin-top: 4px; display: flex; align-items: center; gap: 6px;}
    
    .meta-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; padding-top: 1rem; }
    
    /* Badges in der Karte (Kleiner & Dezenter) */
    .badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-
