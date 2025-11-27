# Scripts Quickstart

- `generate_synthetic_data.py`: produces CSV/JSONL datasets under `data/processed` matching README_DATA schemas.
- `enrich_sentiment.py`: adds score/label/categories/suggestions to a raw reviews JSONL using VADER.
- `tag_categories_zeroshot.py`: tags categories using Hugging Face zero-shot model (downloads on first run).
- `generate_suggestions.py`: fills actionable suggestions for each review based on label/categories.
- `llm_suggestions.py`: generates suggestions and summaries using OpenAI, Azure, or Gemini LLMs. Set provider and API keys in `.env`.
- `scrape_freelance_demo.py`: scrapes public freelance profiles (demo/test URLs only) and outputs raw HTML and cleaned CSV.
- `compute_aggregates.py`: summarizes reviews to a compact JSON for UI cards.
- `seed_backend.py`: patches profile and posts sample feedback to the Django API.

## Scraping

- Add allowed/test URLs to `data/raw/targets.txt`.
- Run `python scripts/scrape_freelance_demo.py` to save raw HTML and cleaned profile CSV.

## LLM Suggestions

- Set API keys in `.env` (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.).
- Run `python scripts/llm_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_llm.jsonl --provider openai` (or `gemini`/`azure`).

## EDA & QA

- Open `notebooks/eda_sentiment_qa.ipynb` to explore distributions, tags, and sample outputs.


## Full Pipeline

```powershell
# Generate synthetic data
python scripts/generate_synthetic_data.py --users 50 --seed 42 --out data/processed

# Scrape demo/test profiles
python scripts/scrape_freelance_demo.py

# Enrich sentiment
python scripts/enrich_sentiment.py --in data/processed/sentiment_reviews.jsonl --out data/processed/sentiment_reviews_tagged.jsonl

# Tag categories (zero-shot)
python scripts/tag_categories_zeroshot.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_tagged.jsonl

# Generate suggestions
python scripts/generate_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_suggested.jsonl

# LLM suggestions/summaries
python scripts/llm_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/sentiment_reviews_llm.jsonl --provider gemini

# Compute aggregates
python scripts/compute_aggregates.py --reviews data/processed/sentiment_reviews_suggested.jsonl --out data/processed/aggregates/aggregates.json

# Seed backend
$env:BASE_URL = "http://localhost:8000/api/v1"
$env:AUTH_TOKEN = "<your JWT>"
python scripts/seed_backend.py
```

## Frontend QA

- Open the frontend app and verify dashboard, profile, and sentiment pages show realistic, varied data.
- Use the EDA notebook (`notebooks/eda_sentiment_qa.ipynb`) to check for duplicates, skill diversity, and sample reviews.
- Adjust data generation parameters if the UI looks too uniform or unrealistic.

## Notes
- All scripts are modular and can be run independently.
- LLM usage is toggleable via provider argument and API keys.
- Scraping is demo-only; update selectors and allowed domains for real use.
- See `data/METADATA.md` for RNG seed and reproducibility info.
