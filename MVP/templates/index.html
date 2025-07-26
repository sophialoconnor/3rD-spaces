import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin

SITES = [
    "https://lovin.ie/",
    "https://www.alternativedublincity.com/",
    "https://charfoodguide.com/category/dublins-food-and-drink-culture-explored/",
    "https://www.totallydublin.ie/",
    "https://districtmagazine.ie/",
    "https://www.bordgaisenergytheatre.ie/",
    "https://www.olympia.ie/",  # corrected
    "https://www.theacademydublin.com/",
    "https://www.whelanslive.com/events/",
    "https://imma.ie/",
    "https://www.nationalgallery.ie/art-and-artists/exhibitions/"
]

DB = "events.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            summary TEXT
        )
    """)
    conn.commit()
    conn.close()

def scrape_site(site):
    try:
        resp = requests.get(site, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {site}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=True):
        url = urljoin(site, a['href'])
        text = a.get_text(strip=True)
        if text and len(text) > 15:
            items.append((text, url, ""))
    return items

def save_items(items):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for title, url, summary in items:
        try:
            c.execute("INSERT OR IGNORE INTO events (title, url, summary) VALUES (?, ?, ?)",
                      (title, url, summary))
        except Exception:
            continue
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    for site in SITES:
        print("Scraping", site)
        items = scrape_site(site)
        save_items(items)
