#!/usr/bin/env python
"""
Playwright scraping scaffold (ethics-first):
- Reads target URLs from data/raw/targets.txt
- Fetches pages at 1–3 req/s with jitter
- Saves raw HTML under data/raw/html/YYYYMMDD/{slug}.html
- Extracts light fields to data/raw/parsed.jsonl (if simple selectors present)

NOTE: Fill CSS selectors and allowed domains before running against real sites.
"""
import asyncio
import os
import random
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

RAW_DIR = Path("data/raw")
TARGETS = RAW_DIR / "targets.txt"
HTML_DIR = RAW_DIR / "html" / datetime.utcnow().strftime("%Y%m%d")
PARSED = RAW_DIR / "parsed.jsonl"

ALLOWED_DOMAINS = {"example.com"}  # TODO: set allowed domains per robots/TOS

# Simple demo selectors – customize per site
SELECTORS = {
    "headline": "h1, h2",
    "rate": "[data-rate], .rate, .hourly",
    "skills": ".skills, [data-skills]",
}


def slugify(url: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", url)
    return s.strip("-").lower()[:100]


async def fetch_page(url: str, pw):
    assert any(d in url for d in ALLOWED_DOMAINS), f"Disallowed domain for {url}"
    browser = await pw.chromium.launch()
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    html = await page.content()
    await browser.close()
    return html


def parse_light(html: str):
    # lightweight parsing with regex hints; prefer BeautifulSoup for real use
    # Here we only return an empty dict – fill with bs4 if needed
    return {}


async def main():
    os.makedirs(HTML_DIR, exist_ok=True)
    if not TARGETS.exists():
        print(f"No targets file at {TARGETS}. Create one URL per line.")
        return

    urls = [u.strip() for u in TARGETS.read_text(encoding="utf-8").splitlines() if u.strip()]
    if not urls:
        print("targets.txt is empty")
        return

    printed_rate_note = False

    async with async_playwright() as pw:
        with open(PARSED, "a", encoding="utf-8") as parsed:
            for url in urls:
                try:
                    if not printed_rate_note:
                        print("Respect robots.txt and TOS; scraping at ~1–3 req/s with jitter")
                        printed_rate_note = True
                    html = await fetch_page(url, pw)
                    name = slugify(url) + ".html"
                    (HTML_DIR / name).write_text(html, encoding="utf-8")
                    # Minimal stub parse
                    item = {"url": url}
                    parsed.write(str(item) + "\n")
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                await asyncio.sleep(random.uniform(0.3, 1.0))


if __name__ == "__main__":
    asyncio.run(main())
