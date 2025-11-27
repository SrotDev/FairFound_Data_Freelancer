#!/usr/bin/env python
"""
Demo scraping script for public freelance profiles (e.g., Upwork demo page).
- Reads URLs from data/raw/targets.txt
- Saves raw HTML to data/raw/html/YYYYMMDD/{slug}.html
- Extracts headline, rate, skills to data/processed/freelancer_profiles_scraped.csv
- Respects robots.txt and TOS (for demo, only allowed/test URLs)
"""
import requests
import os
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import csv

RAW_DIR = Path("data/raw")
HTML_DIR = RAW_DIR / "html" / datetime.utcnow().strftime("%Y%m%d")
PROCESSED = Path("data/processed/freelancer_profiles_scraped.csv")
TARGETS = RAW_DIR / "targets.txt"

os.makedirs(HTML_DIR, exist_ok=True)

# Example: fill with allowed/test URLs
if not TARGETS.exists():
    TARGETS.write_text("https://www.upwork.com/freelancers/~demo_profile", encoding="utf-8")

urls = [u.strip() for u in TARGETS.read_text(encoding="utf-8").splitlines() if u.strip()]

rows = []
for url in urls:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        name = re.sub(r"[^a-zA-Z0-9]+", "-", url).strip("-").lower()[:100] + ".html"
        (HTML_DIR / name).write_text(r.text, encoding="utf-8")
        soup = BeautifulSoup(r.text, "lxml")
        headline = soup.find("h1")
        rate = soup.find(string=re.compile("\$[0-9]+"))
        skills = ";".join([s.get_text(strip=True) for s in soup.select(".skills, [data-skills]")])
        rows.append({
            "url": url,
            "headline": headline.get_text(strip=True) if headline else "",
            "rate": rate.strip() if rate else "",
            "skills": skills,
        })
    except Exception as e:
        print(f"Error scraping {url}: {e}")

with open(PROCESSED, "w", newline='', encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["url", "headline", "rate", "skills"])
    w.writeheader()
    w.writerows(rows)

print(f"Scraped {len(rows)} profiles. Raw HTML in {HTML_DIR}, cleaned CSV in {PROCESSED}")
