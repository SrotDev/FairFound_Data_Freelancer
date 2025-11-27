#!/usr/bin/env python
import argparse
import json
import os
from collections import Counter
from statistics import mean

from utils import read_jsonl


def main():
    ap = argparse.ArgumentParser(description="Compute aggregates for sentiment and benchmarks")
    ap.add_argument("--reviews", default="data/processed/sentiment_reviews.jsonl")
    ap.add_argument("--out", default="data/processed/aggregates/aggregates.json")
    args = ap.parse_args()

    rows = read_jsonl(args.reviews)
    labels = Counter(r.get("label", "unknown") for r in rows)
    scores = [float(r.get("score", 0)) for r in rows if "score" in r]
    cats = Counter(c for r in rows for c in r.get("categories", []))

    summary = {
        "positives": labels.get("positive", 0),
        "neutrals": labels.get("neutral", 0),
        "negatives": labels.get("negative", 0),
        "avg_score": round(mean(scores), 4) if scores else 0.0,
        "top_categories": [c for c, _ in cats.most_common(5)],
        "actionable_suggestions": [
            "Provide structured progress updates",
            "Ask for a brief quality score",
        ],
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Wrote aggregates -> {args.out}")


if __name__ == "__main__":
    main()
