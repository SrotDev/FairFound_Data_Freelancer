#!/usr/bin/env python
import os
from dotenv import load_dotenv
import json
import sys
from typing import Dict

import requests


# Load environment variables from .env file
load_dotenv()
BASE = os.getenv("BASE_URL", "http://localhost:8000/api/")
TOKEN = os.getenv("AUTH_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def require_token():
    if not TOKEN:
        print("ERROR: AUTH_TOKEN env var is empty. Export a valid JWT.")
        sys.exit(1)


def patch_my_profile(payload: Dict):
    url = f"{BASE}/freelancers/me/profile/"
    r = requests.patch(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json() if r.content else {}


def post_feedback(text: str):
    url = f"{BASE}/freelancers/me/feedback/"
    r = requests.post(url, headers=HEADERS, json={"text": text})
    r.raise_for_status()
    return r.json() if r.content else {}


def main():
    require_token()
    # 1) Update a few profile fields
    print("Patching profile...")
    patch_my_profile({
        "hourly_rate": 55,
        "portfolio_items": 9,
        "proposal_success_rate": 22,
        "repeat_clients_rate": 30,
        "skills": ["React", "TypeScript", "Node.js", "UI/UX Design"],
    })

    # 2) Seed some sentiment
    sample_path = os.path.join("data", "processed", "samples", "sentiment_reviews_sample.json")
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample = json.load(f)
        print(f"Posting {len(sample)} feedback samples...")
        for r in sample:
            post_feedback(r.get("text", "Thanks!"))
    else:
        print(f"Sample not found at {sample_path}. Skipping feedback seeding.")

    print("Done seeding.")


if __name__ == "__main__":
    main()
