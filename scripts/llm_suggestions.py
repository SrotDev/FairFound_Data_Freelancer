#!/usr/bin/env python
"""
LLM-powered suggestion/summary generator for sentiment reviews.
Supports OpenAI (default), Azure OpenAI, or Gemini (Google Vertex).

Usage:
  python scripts/llm_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_llm.jsonl --provider openai

.env keys required:
  OPENAI_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, MODEL_NAME, GEMINI_API_KEY
"""
import argparse
import os
import json
from utils import read_jsonl, write_jsonl

PROVIDERS = ["openai", "azure", "gemini"]

# Example prompt template
PROMPT = """
Given the following review text and categories, generate 2 actionable suggestions (max 200 chars each) and a friendly summary for the freelancer.\nText: {text}\nCategories: {categories}\nLabel: {label}\nSuggestions:
"""

def call_llm_openai(prompt, api_key, model):
    import openai
    openai.api_key = api_key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def call_llm_gemini(prompt, api_key):
    import google.generativeai as genai
    model_id = os.getenv("GOOGLE_MODEL_ID", "gemini-pro")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    resp = model.generate_content(prompt)
    return resp.text.strip()

def call_llm_azure(prompt, api_key, endpoint, model):
    import openai
    openai.api_type = "azure"
    openai.api_key = api_key
    openai.api_base = endpoint
    openai.api_version = "2023-05-15"
    resp = openai.ChatCompletion.create(
        engine=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="data/processed/sentiment_reviews_tagged.jsonl")
    ap.add_argument("--out", dest="out_path", default="data/processed/sentiment_reviews_llm.jsonl")
    ap.add_argument("--provider", choices=PROVIDERS, default="gemini")
    ap.add_argument("--model", default=os.getenv("GOOGLE_MODEL_ID", "gemini-pro"))
    args = ap.parse_args()

    rows = read_jsonl(args.in_path)
    out = []
    for r in rows:
        prompt = PROMPT.format(text=r.get("text", ""), categories=", ".join(r.get("categories", [])), label=r.get("label", ""))
        try:
            if args.provider == "gemini":
                api_key = os.getenv("GOOGLE_API_KEY")
                result = call_llm_gemini(prompt, api_key)
            elif args.provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                model = args.model
                result = call_llm_openai(prompt, api_key, model)
            elif args.provider == "azure":
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                model = args.model
                result = call_llm_azure(prompt, api_key, endpoint, model)
            else:
                result = ""
            # Parse result: expect suggestions and summary separated by newlines
            suggestions = []
            summary = ""
            for line in result.splitlines():
                if line.strip().startswith("-") or line.strip().startswith("1."):
                    suggestions.append(line.strip("- ").strip())
                elif not summary and line.strip():
                    summary = line.strip()
            r["llm_suggestions"] = suggestions[:2]
            r["llm_summary"] = summary
        except Exception as e:
            r["llm_suggestions"] = []
            r["llm_summary"] = f"LLM error: {e}"
        out.append(r)
    write_jsonl(args.out_path, out)
    print(f"LLM suggestions and summaries written to {args.out_path}")

if __name__ == "__main__":
    main()
