#!/usr/bin/env python
"""
Generate actionable suggestions for each sentiment review based on label and categories.
Usage:
  python scripts/generate_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_suggested.jsonl
"""
import argparse
import os
from utils import read_jsonl, write_jsonl

def suggest(label, categories):
    cats = set(categories)
    if label == "negative":
        if "deadlines" in cats:
            return ["Share a timeline upfront and add milestones"]
        if "communication" in cats:
            return ["Send structured progress updates twice a week"]
        return ["Clarify expectations early and confirm acceptance"]
    elif label == "neutral":
        return ["Ask for a brief quality score to improve"]
    else:  # positive
        return ["Keep doing structured updates and capture testimonials"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="data/processed/sentiment_reviews_tagged.jsonl")
    ap.add_argument("--out", dest="out_path", default="data/processed/sentiment_reviews_suggested.jsonl")
    args = ap.parse_args()

    rows = read_jsonl(args.in_path)
    for r in rows:
        label = r.get("label", "neutral")
        categories = r.get("categories", [])
        r["suggestions"] = suggest(label, categories)
    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    write_jsonl(args.out_path, rows)
    print(f"Suggestions written to {args.out_path}")

if __name__ == "__main__":
    main()
