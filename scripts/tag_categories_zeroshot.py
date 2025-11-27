#!/usr/bin/env python
"""
Zero-shot multi-label category tagging for sentiment reviews using transformers.
Labels: communication, quality, responsiveness, deadlines, scope, documentation.

Usage:
  python scripts/tag_categories_zeroshot.py --in data/processed/sentiment_reviews.jsonl --out data/processed/sentiment_reviews_tagged.jsonl

Requires: transformers, torch, sentencepiece
Model: facebook/bart-large-mnli (default) – CPU OK, small batch.
"""
import argparse
import os

from transformers import pipeline

from utils import read_jsonl, write_jsonl

LABELS = [
    "communication", "quality", "responsiveness", "deadlines", "scope", "documentation"
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="data/processed/sentiment_reviews.jsonl")
    ap.add_argument("--out", dest="out_path", default="data/processed/sentiment_reviews.jsonl")
    ap.add_argument("--model", default="facebook/bart-large-mnli")
    ap.add_argument("--threshold", type=float, default=0.4)
    args = ap.parse_args()

    rows = read_jsonl(args.in_path)
    nlp = pipeline("zero-shot-classification", model=args.model, device=-1)

    out = []
    for r in rows:
        text = r.get("text", "")[:1000]
        res = nlp(text, LABELS, multi_label=True)
        keep = [lbl for lbl, score in zip(res["labels"], res["scores"]) if score >= args.threshold]
        merged = sorted(set(r.get("categories", []) + keep))
        r["categories"] = merged
        out.append(r)

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    write_jsonl(args.out_path, out)
    print(f"Tagged {len(out)} reviews -> {args.out_path}")


if __name__ == "__main__":
    main()
