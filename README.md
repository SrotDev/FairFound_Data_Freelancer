# FairFound Data Science Repository

## Overview
This repository contains all data science workflows, scripts, and sample data for the FairFound platform. It is designed to generate, enrich, and prepare realistic user, profile, and review data for backend and frontend integration. Backend developers can use these scripts and outputs to seed and serve data via the Django REST Framework (DRF) API.

---

## Repository Structure

```
├── data/
│   ├── raw/                # Raw scraped or synthetic data
│   ├── processed/          # Enriched, tagged, and aggregated data
│   └── METADATA.md         # Data documentation, reproducibility, checksums
├── notebooks/
│   └── eda_sentiment_qa.ipynb  # EDA and QA notebook for data quality
├── scripts/
│   ├── generate_synthetic_data.py      # Generates synthetic user/profile/review data
│   ├── enrich_sentiment.py             # Adds sentiment scores to reviews
│   ├── tag_categories_zeroshot.py      # Tags reviews with categories (zero-shot)
│   ├── generate_suggestions.py         # Generates suggestions for users/profiles
│   ├── llm_suggestions.py              # Rewrites suggestions using Gemini LLM
│   ├── compute_aggregates.py           # Computes aggregate stats (sentiment, categories)
│   ├── seed_backend.py                 # Seeds backend API with processed data
│   └── scrape_stub.py                  # Scraping scaffold (demo only)
│   └── README.md                       # Script usage documentation
├── .env.example            # Example environment variables for API keys
├── README_DATA.md          # Data science workflow and instructions
├── README_API.md           # Backend API documentation
├── README_FRONTEND.md      # Frontend integration documentation
```

---

## File/Script Descriptions

- **data/raw/**: Contains raw synthetic or scraped data (JSONL/CSV).
- **data/processed/**: Contains processed, enriched, and aggregated data ready for backend seeding.
- **data/METADATA.md**: Documents data sources, schema, reproducibility, and large dataset locations.
- **notebooks/eda_sentiment_qa.ipynb**: Jupyter notebook for EDA and QA of generated/enriched data.
- **scripts/generate_synthetic_data.py**: Generates realistic synthetic data for users, profiles, and reviews.
- **scripts/enrich_sentiment.py**: Adds sentiment scores to reviews using Hugging Face models.
- **scripts/tag_categories_zeroshot.py**: Tags reviews with categories using zero-shot classification.
- **scripts/generate_suggestions.py**: Generates suggestions for users/profiles based on data.
- **scripts/llm_suggestions.py**: Uses Gemini LLM to rewrite suggestions for realism.
- **scripts/compute_aggregates.py**: Computes aggregate statistics (e.g., average sentiment per user).
- **scripts/seed_backend.py**: Seeds the Django REST Framework backend API with processed data.
- **scripts/scrape_stub.py**: Demo script for ethical scraping (rate-limited, Playwright-based).
- **.env.example**: Template for required API keys (Gemini, Hugging Face).

---

## How Scripts Are Connected

1. **Data Generation**: `generate_synthetic_data.py` creates initial data in `data/raw/`.
2. **Enrichment**: `enrich_sentiment.py` and `tag_categories_zeroshot.py` process raw data, outputting to `data/processed/`.
3. **Suggestion Generation**: `generate_suggestions.py` and `llm_suggestions.py` create and rewrite suggestions.
4. **Aggregation**: `compute_aggregates.py` summarizes data for analytics.
5. **Backend Seeding**: `seed_backend.py` uploads processed data to the Django backend via API.
6. **EDA/QA**: `eda_sentiment_qa.ipynb` helps verify data quality and variety.

---

## Commands to Run Each Step

```powershell
# 1. Generate synthetic data
python scripts/generate_synthetic_data.py --out data/raw/synthetic_data.jsonl

# 2. Enrich with sentiment
python scripts/enrich_sentiment.py --in data/raw/synthetic_data.jsonl --out data/processed/sentiment_reviews.jsonl

# 3. Tag categories (zero-shot)
python scripts/tag_categories_zeroshot.py --in data/processed/sentiment_reviews.jsonl --out data/processed/sentiment_reviews_tagged.jsonl

# 4. Generate suggestions
python scripts/generate_suggestions.py --in data/processed/sentiment_reviews_tagged.jsonl --out data/processed/suggestions.jsonl

# 5. Rewrite suggestions with Gemini LLM
python scripts/llm_suggestions.py --in data/processed/suggestions.jsonl --out data/processed/suggestions_llm.jsonl

# 6. Compute aggregates
python scripts/compute_aggregates.py --reviews data/processed/sentiment_reviews_tagged.jsonl --out data/processed/aggregates/aggregates.json

# 7. Seed backend (requires JWT and API endpoint)
python scripts/seed_backend.py --data data/processed/sentiment_reviews_tagged.jsonl --jwt <YOUR_JWT_TOKEN> --api <API_ENDPOINT>
```

---

## Integration with Django REST Framework Backend

- The backend developer should:
  1. Ensure the Django REST Framework API is running and accessible.
  2. Obtain a valid JWT token for authentication.
  3. Use `seed_backend.py` to POST processed data to the backend endpoints (users, profiles, reviews, etc.).
  4. Verify data is correctly ingested by checking API endpoints and frontend displays.

---

## Step-by-Step Guidelines for Backend Developer

1. **Setup**
   - Clone this repository.
   - Install Python dependencies: `pip install -r requirements.txt`
   - Set up `.env` with required API keys (see `.env.example`).

2. **Run Data Pipeline**
   - Execute each script in order (see commands above) to generate and process data.
   - Review outputs in `data/processed/` and validate with the EDA notebook.

3. **Prepare Backend**
   - Start the Django REST Framework backend server.
   - Obtain a JWT token for API authentication.

4. **Seed Backend**
   - Run `seed_backend.py` with processed data, JWT, and API endpoint:
     ```powershell
     python scripts/seed_backend.py --data data/processed/sentiment_reviews_tagged.jsonl --jwt <YOUR_JWT_TOKEN> --api <API_ENDPOINT>
     ```
   - Confirm successful upload by checking backend API endpoints (e.g., `/api/users/`, `/api/reviews/`).

5. **Verify Integration**
   - Ensure frontend displays correct data from backend.
   - Use the EDA notebook to cross-check data quality and variety.

6. **Troubleshooting**
   - If errors occur, check logs, validate JWT/API endpoint, and review script outputs.
   - Refer to `README_API.md` for backend API details and endpoint formats.

---

## Additional Notes
- All scripts are modular and can be adapted for new schemas or endpoints.
- Data files are in JSONL format for easy streaming and ingestion.
- For large datasets, see `data/METADATA.md` for download links and checksums.
- Ethical scraping is demonstrated in `scrape_stub.py` (do not use for production scraping without permission).

---

For further questions, see individual README files or contact the data science team.
