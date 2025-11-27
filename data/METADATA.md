
# Data Generation Metadata

- RNG seed: default 42 (override with --seed)
- Generator script: `scripts/generate_synthetic_data.py`
- Generated at: please record run datetime when executing locally
- Schemas: see README_DATA section 6

## Large Dataset Location

- S3 bucket: s3://fairfound-datasets/v1/
- SAS URL: https://storage.example.com/fairfound/v1/?sig=...
- Checksum (SHA256): 7a8c... (see `data/processed/large_corpus.sha256`)
- Version: v1.0, generated 2025-11-27

## Reproducibility

- All synthetic data generated with fixed seed for each run.
- For large corpora, record generation script, seed, and timestamp.

## Suggested commands (PowerShell):

```
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
# Optional: playwright browsers for scraping
# python -m playwright install chromium

# Generate datasets (lightweight defaults)
python scripts/generate_synthetic_data.py --users 50 --seed 42 --out data/processed

# Enrich any raw sentiment file (if using a raw input)
# python scripts/enrich_sentiment.py --in data/processed/sentiment_reviews_raw.jsonl --out data/processed/sentiment_reviews.jsonl

# Compute aggregates
python scripts/compute_aggregates.py --reviews data/processed/sentiment_reviews.jsonl --out data/processed/aggregates/aggregates.json
```
