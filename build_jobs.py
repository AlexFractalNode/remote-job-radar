import json
import os
import html

# --- KONFIGURATION ---
OUTPUT_DIR = 'job_board'
DATA_FILE = 'real_jobs.json'
SITE_NAME = "RemoteRadar 📡"

# --- CSS & DESIGN (Clean & Trustworthy) ---
css_styles = """
<style>
    :root { --primary: #2563eb; --background: #f8fafc; --card-bg: #ffffff; }
    body { background-color: var(--background); font-family: 'Segoe UI', sans-serif; }
    
    /* Header */
    nav { background: white; border-bottom: 1px solid #e2e8f0; padding: 1rem 0; }
    .nav-content { display: flex; justify-content: space-between; align-items: center; }
    .logo { font-weight: 800; font-size: 1.5rem; color: var(--primary); text-decoration: none; }
    
    /* Job Cards (Index) */
    .job-card {
        background: var(--card-bg);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
        display: block;
        text-decoration: none;
        color: inherit;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-color: var(--primary);
    }
    .job-title { font-size: 1.2rem; font-weight: 600; color: #1e293b; }
    .job-meta { color: #64748b; font-size: 0.9rem; margin-top: 0.5rem; display: flex; gap: 1rem; }
    
    /* Badges */
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
    .badge-remote { background: #dcfce7; color: #166534; }
    .badge-office { background: #f1f5f9; color: #475569; }
    
    /* Detail Page */
    .apply-btn {
        display: inline-block;
        background: var(--primary); color: white;
        padding: 12px 24px; border-radius: 6px;
        text-decoration: none; font-weight: bold;
        text-align: center; width: 100%;
    }
    .apply-btn:hover { background: #1d4ed8; }
    .job-description { line-height: 1.6; color: #334155; margin-top: 2rem; }
    .job-description h2 { margin-top: 1.5rem; font-size: 1.3rem; }
    .job-description ul { margin-left: 1.5rem; }
</style>
"""

# --- TEMPLATE: DETAILSEITE ---
job_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} bei {{ company }} | {{ site_name }}</title>
    <meta name="description" content="Jobangebot: {{ title }} in {{ location }}. Jetzt bewerben bei {{ company }}.">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {{ css_styles }}
    
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "JobPosting",
      "title": "{{ title }}",
      "description": "{{ description_clean }}",
      "hiringOrganization": {
        "@type": "Organization",
        "name": "{{ company }}"
      },
      "jobLocation": {
        "@type": "Place",
        "address": {
          "@type": "PostalAddress",
          "addressLocality": "{{ location }}",
          "addressCountry": "DE"
        }
      },
      "datePosted": "{{ date }}",
      "employmentType": "FULL_TIME"
    }
    </script>
</head>
<body>
    <nav class="container-fluid">
        <div class="container nav-content">
            <a href="index.html" class="logo">📡 RemoteRadar</a>
            <a href="index.html" role="button" class="outline">⬅ Zurück</a>
        </div>
    </nav>

    <main class="container">
        <article style="background: white; padding: 2rem; border-radius: 8px; border: 1px solid #e2e8f0;">
            <header>
                <small>{{ company }} sucht:</small>
                <h1 style="margin-top: 0.5rem;">{{ title }}</h1>
                <div class="job-meta">
                    <span>📍 {{ location }}</span>
                    {{ remote_badge }}
                </div>
            </header>

            <div class="grid">
                <div class="job-description">
                    {{ description_html }}
                </div>
                
                <aside>
                    <div style="position: sticky; top: 2rem; background: #f8fafc; padding: 1.5rem; border-radius: 8px;">
                        <h4>Interesse?</h4>
                        <p>Bewirb dich direkt beim Unternehmen.</p>
                        <a href="{{ apply_url }}" target="_blank" class="apply-btn">Jetzt bewerben ↗</a>
                        <small style="display:block; margin-top:1rem; text-align:center; color:#94a3b8;">
                            Du wirst zu {{ company }} weitergeleitet.
                        </small>
                    </div>
                </aside>
            </div>
        </article>
    </main>
</body>
</html>
"""

# --- LOGIK ---

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print(f"🏗️ Baue Job-Board '{SITE_NAME}'...")

# Daten laden
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
except FileNotFoundError:
    print("❌ FEHLER: Keine Daten gefunden. Führe erst Schritt 1 aus!")
    jobs = []

index_html_cards = ""
job_counter = 0

for job in jobs:
    # 1. Daten vorbereiten
    slug = job.get('slug', f"job-{job_counter}")
    filename = f"{slug}.html"
    title = job.get('title', 'Unbekannte Position')
    company = job.get('company_name', 'Unbekannt')
    location = job.get('location', 'Remote')
    is_remote = job.get('remote', False)
    desc_html = job.get('description', '<p>Keine Beschreibung verfügbar.</p>')
    # Für Schema.org muss der Text sauber sein (ohne HTML Tags grob entfernen für JSON)
    desc_clean = html.escape(desc_html[:200] + "...") 
    date_posted = job.get('created_at', '2025-01-01')
    apply_url = job.get('url', '#')

    # Remote Badge Logik
    if is_remote:
        remote_badge = '<span class="badge badge-remote">🌍 Remote möglich</span>'
        idx_badge = '<span style="background:#dcfce7; color:#166534; padding:2px 6px; border-radius:4px; font-size:0.8em; float:right;">Remote</span>'
    else:
        remote_badge = '<span class="badge badge-office">🏢 Vor Ort</span>'
        idx_badge = ''

    # 2. Detailseite erstellen
    page = job_template.replace("{{ title }}", title)
    page = page.replace("{{ company }}", company)
    page = page.replace("{{ site_name }}", SITE_NAME)
    page = page.replace("{{ location }}", location)
    page = page.replace("{{ description_clean }}", desc_clean)
    page = page.replace("{{ date }}", str(date_posted))
    page = page.replace("{{ css_styles }}", css_styles)
    page = page.replace("{{ remote_badge }}", remote_badge)
    page = page.replace("{{ description_html }}", desc_html)
    page = page.replace("{{ apply_url apply_url }}", apply_url) # Fallback
    page = page.replace("{{ apply_url }}", apply_url)

    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(page)
    
    # 3. Karte für Index erstellen
    index_html_cards += f"""
    <a href="{filename}" class="job-card">
        <div style="display:flex; justify-content:space-between;">
            <div class="job-title">{title}</div>
            {idx_badge}
        </div>
        <div class="job-meta">
            <span>🏢 {company}</span>
            <span>📍 {location}</span>
        </div>
    </a>
    """
    job_counter += 1

print(f"✅ {job_counter} Job-Seiten generiert.")

# --- INDEX.HTML ---
index_template = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_NAME} - Die besten Tech & Remote Jobs</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    {css_styles}
    <script>
    function filterJobs() {{
        var input = document.getElementById('search').value.toUpperCase();
        var cards = document.getElementsByClassName('job-card');
        for (var i = 0; i < cards.length; i++) {{
            var txt = cards[i].innerText;
            cards[i].style.display = txt.toUpperCase().indexOf(input) > -1 ? "block" : "none";
        }}
    }}
    </script>
</head>
<body>
    <nav class="container-fluid">
        <div class="container nav-content">
            <a href="#" class="logo">📡 RemoteRadar</a>
            <div>
                <a href="#" role="button" class="secondary outline">Für Arbeitgeber</a>
            </div>
        </div>
    </nav>

    <main class="container">
        <div style="text-align:center; padding: 3rem 0;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">Finde deinen Traumjob.</h1>
            <p style="color:#64748b;">Durchsuche hunderte aktuelle Stellenangebote aus Deutschland & Remote.</p>
            
            <input type="text" id="search" onkeyup="filterJobs()" placeholder="🔍 Suche nach 'Java', 'Marketing', 'Berlin'..." style="max-width: 600px; margin: 2rem auto; padding: 1rem; border-radius: 8px;">
        </div>

        <div id="job-list">
            {index_html_cards}
        </div>
        
        <footer style="text-align:center; margin-top:4rem; color:#94a3b8;">
            <small>&copy; 2025 RemoteRadar. Alle Jobs von Arbeitnow API.</small>
        </footer>
    </main>
</body>
</html>
"""

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_template)

print("🎉 Job-Board fertig! Öffne 'job_board/index.html'.")

# --- 4. SITEMAP GENERATOR (MIT FEHLER-SCHUTZ) ---
print("🗺️ Erstelle Sitemap für Google...")

# WICHTIG: Hier später deine echte URL eintragen (z.B. https://mein-jobboard.netlify.app)
BASE_URL = "https://dein-jobboard-name.netlify.app" 

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

# Startseite
sitemap_content += f'  <url><loc>{BASE_URL}/</loc><changefreq>daily</changefreq></url>\n'

# Alle Job-Seiten
for job in jobs:
    slug = job.get('slug', 'job')
    
    # DER FIX: Wir holen das Datum sicher!
    raw_date = job.get("created_at")
    
    # Wenn Datum existiert -> nutzen. Wenn nicht -> Fallback-Datum nehmen.
    if raw_date:
        clean_date = raw_date[:10]
    else:
        clean_date = "2025-01-01" # Fallback

    sitemap_content += f'  <url><loc>{BASE_URL}/{slug}.html</loc><lastmod>{clean_date}</lastmod><changefreq>daily</changefreq></url>\n'

sitemap_content += '</urlset>'

# Speichern
with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemap_content)

print("✅ sitemap.xml erfolgreich erstellt (trotz fehlender Daten).")