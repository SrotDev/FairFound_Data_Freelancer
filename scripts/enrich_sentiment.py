#!/usr/bin/env python
import argparse
import os
from typing import Dict

from utils import read_jsonl, write_jsonl, vader_score, label_from_score


def enrich(item: Dict) -> Dict:
    text = item.get("text", "")
    score = vader_score(text)
    label = label_from_score(score)
    # simple rule-based category tags
    cats = []
    low = text.lower()
    if any(k in low for k in ["communicat", "responsive", "reply"]):
        cats.append("communication")
    if any(k in low for k in ["quality", "polish", "clean"]):
        cats.append("quality")
    if any(k in low for k in ["deadline", "time", "late", "timely"]):
        cats.append("deadlines")
    if any(k in low for k in ["scope", "requirement", "brief"]):
        cats.append("scope")
    if any(k in low for k in ["doc", "readme"]):
        cats.append("documentation")

    suggestions = []
    if label == "negative":
        if "deadlines" in cats:
            suggestions.append("Share a timeline upfront and add milestones")
        if "communication" in cats:
            suggestions.append("Send structured progress updates twice a week")
        if not suggestions:
            suggestions.append("Clarify expectations early and confirm acceptance")
    elif label == "neutral":
        suggestions.append("Ask for a brief quality score to improve")
    else:  # positive
        suggestions.append("Keep doing structured updates and capture testimonials")

    item.update({
        "score": round(float(score), 2),
        "label": label,
        "categories": cats,
        "suggestions": suggestions,
    })
    return item


def main():
    ap = argparse.ArgumentParser(description="Enrich sentiment reviews with score/label/categories/suggestions")
    ap.add_argument("--in", dest="in_path", default="data/processed/sentiment_reviews_raw.jsonl")
    ap.add_argument("--out", dest="out_path", default="data/processed/sentiment_reviews.jsonl")
    args = ap.parse_args()

    rows = read_jsonl(args.in_path)
    out = [enrich(r) for r in rows]
    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    write_jsonl(args.out_path, out)
    print(f"Enriched {len(out)} reviews -> {args.out_path}")


if __name__ == "__main__":
    main()
