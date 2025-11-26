# FairFound Data Science Playbook (README_DATA)

Version: v1 (Initial)
Audience: Data Scientist (scraping, synthesis, modeling, seeding backend)

Goals:
- Provide realistic datasets (dummy + scraped) to power frontend features.
- Run local NLP to derive sentiment labels, categories, and actionable suggestions.
- Optionally use LLM APIs for higher-quality suggestions and summaries.
- Seed the Django REST API with clean, consistent payloads matching `README_API.md` / `api.http`.

---
## 1) What Data We Need (by Feature)

Map directly to frontend features and backend endpoints.

- User & Industry
  - Minimal user profile: `id`, `name`, `email`, `is_mentor`, `industry` (enum: Freelancer | E-commerce | Developer | Business).
  - Dataset: 20–100 demo users; 5–20 with `is_mentor=true`.

- Freelancer Metrics (mirrors `FreelancerProfile`)
  - Fields: `profile_completeness (0..100)`, `profile_views`, `proposal_success_rate (0..100)`, `job_invitations`, `hourly_rate`, `skills[]`, `portfolio_items`, `repeat_clients_rate (0..100)`.
  - Dataset: 200–1000 profiles (synthetic + scraped) for benchmarking and suggestions.

- Pseudo Ranking
  - Not stored directly; compute from profile + roadmap using the formula in README_API (service replicable locally for validation).

- Roadmap Milestones
  - Fields: `id`, `title`, `description`, `estimated_effort`, `order`, `completed`.
  - Dataset: 5–10 default milestone templates + per-user status (completed flags).

- Comparisons
  - Saved snapshots against either competitor profiles or top-avg aggregates.
  - Fields: `competitor_identifier`, `competitor_role`, `pseudo_ranking`, `snapshot{metrics...}`.
  - Dataset: 100–300 snapshots across roles (frontend/backend/full-stack/UI/UX, etc.).

- Sentiment Reviews (Client Feedback)
  - Raw field: `text` (100–400 chars ideal), derived: `score (-1..1)`, `label ∈ {positive, neutral, negative}`, `categories[]`, `suggestions[]`.
  - Dataset: 10–100 reviews per active user. Provide balanced distribution.

- Mentorship (Requests & Messages)
  - Requests fields: `topic`, `context`, `preferred_expertise[]`, `status`, `requester_id`, optional `mentor_id`.
  - Messages fields: `text`, `sender_id`, `created_at`.
  - Dataset: 50–200 requests; 0–20 per mentor; 1–10 messages per thread.

- Industries
  - Slugs: `freelancer`, `ecommerce`, `developer`, `business` with name/description and `features[]`.

- Suggestions (Competitors)
  - A small precomputed list per role with `identifier`, `role`, and rough metric summary.

---
## 2) What Can Be Web-Scraped (Ethics & Scope)

Only scrape publicly available data and respect site terms and robots.txt. Focus on:
- Freelance marketplaces: profile headlines, skills, hourly rates, number of projects, review snippets (no PII).
- Professional networks or portfolios where allowed (project counts, tags, public testimonials).
- Public tech job boards for general market rates (aggregate only, not individual resumes).

Guidelines:
- Rate limit (1–3 req/s). Add random jitter.
- Use rotating UA strings; back off on blocks.
- Store original URLs and fetch timestamps.
- Never scrape private pages or bypass access controls.
- Hash any incidental PII; store only derived aggregates.

Suggested stack:
- Python `requests` + `beautifulsoup4` for simple HTML.
- Playwright for dynamic pages.

Directory:
- `data/raw/` (raw HTML or JSON dumps)
- `data/processed/` (clean tables CSV/Parquet/JSONL)

---
## 3) Synthetic (Dummy) Data Generation

Use seeded RNG to ensure reproducibility.

- Profiles
  - Sample skills from a controlled vocabulary (React, TypeScript, Node.js, UI/UX Design, Next.js, GraphQL, Docker, etc.).
  - Draw numeric fields from realistic distributions:
    - `hourly_rate`: log-normal (median 45–65), clamp within [10, 200].
    - `profile_completeness`: normal around 70 ± 15, clamp [20, 100].
    - `proposal_success_rate`: beta-like (mode near 20–30%), clamp [0, 100].
    - `portfolio_items`: Poisson/neg-bin with mean 6–10.
    - `repeat_clients_rate`: normal around 25 ± 15, clamp [0, 100].
  - Ensure coherent relationships (higher completeness correlates with invitations).

- Sentiment Reviews
  - Author short realistic client comments (pos/neu/neg balanced).
  - Use template-based generation for categories: communication, quality, responsiveness, deadlines, scope, documentation.

- Mentorship
  - Create topics like “React performance patterns”, “Portfolio storytelling”, “Proposal strategy”.
  - Randomly assign mentors; create 1–5 messages per request.

Save as CSV or JSONL with the schemas in section 6.

---
## 4) Local Models To Run

Two tiers: lightweight offline first; optional upgrade to LLM APIs.

- Sentiment Classification
  - Option A (fast): VADER (NLTK) for quick score; map to label.
  - Option B (quality): Transformers (`cardiffnlp/twitter-roberta-base-sentiment-latest` or `distilroberta-finetuned-sst-2`) to get logits → score.

- Category Tagging (multi-label)
  - Zero-shot classification via `facebook/bart-large-mnli` with label set: [communication, quality, responsiveness, deadlines, scope, documentation].
  - Or rule-based keyword lists to bootstrap.

- Keyphrase Extraction (optional)
  - `keybert` or `yake` for surface-level phrases.

- Suggestion Generation
  - Rule-based: map categories+label to templated suggestions (e.g., negative+deadlines → “Share timeline upfront and add milestones”).
  - LLM enhancement (see section 5) to rewrite suggestions more naturally.

- Pseudo Ranking (Validation)
  - Re-implement the formula locally to verify backend parity (see README_API section 4.1). Output breakdown for QA.

Hardware: CPU is fine. For transformers, set small batch size (8–16). Torch optional with CPU backend.

---
## 5) LLM APIs (Optional Enhancements)

Preferred: Azure OpenAI (org-friendly) or OpenAI. Keep abstraction to toggle on/off.

Use cases:
- Polished suggestion rewriting from categories.
- Summarize sentiment aggregates into a friendly paragraph for UI cards.
- Generate realistic dummy feedback given profile context.

Environment:
```
# .env
OPENAI_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
MODEL_NAME=gpt-4o-mini
```

Prompting templates (few-shot):
- Input: category list, label, brief context.
- Output: 3 concise action-oriented suggestions.
- Constraints: <= 200 chars per suggestion; no PII.

Cost control:
- Cache model outputs by hash(text+labels).
- Rate limit and batch.

---
## 6) Data Schemas

- `users.csv`
  - id (uuid), name, email, is_mentor (bool), industry (enum), created_at (iso)

- `freelancer_profiles.csv`
  - user_id, profile_completeness, profile_views, proposal_success_rate, job_invitations,
    hourly_rate, skills (";"-sep), portfolio_items, repeat_clients_rate, updated_at

- `roadmap_milestones.csv`
  - id (uuid), user_id, title, description, estimated_effort, order, completed (bool), created_at

- `comparisons.jsonl`
  - { id, user_id, competitor_identifier, competitor_role, pseudo_ranking, snapshot{...}, created_at }

- `sentiment_reviews.jsonl`
  - { id, user_id, text, score, label, categories[], suggestions[], created_at }

- `mentorship_requests.jsonl`
  - { id, requester_id, mentor_id|null, topic, context, preferred_expertise[], status, created_at }

- `mentorship_messages.jsonl`
  - { id, request_id, sender_id, text, created_at }

- `industries.json`
  - [ { slug, name, description, features[] } ]

- `suggested_competitors.jsonl`
  - { role, identifier, hourly_rate, portfolio_items, pseudo_ranking }

---
## 7) Tooling & Setup

Create a dedicated environment and install dependencies.

```powershell
# Windows PowerShell
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install requests beautifulsoup4 pandas numpy scikit-learn python-dotenv
pip install playwright bs4 lxml
playwright install chromium
# NLP
pip install transformers torch sentencepiece
pip install keybert yake nltk
python -c "import nltk; nltk.download('vader_lexicon')"
```

Project dirs:
```
/data
  /raw
  /processed
/notebooks
/scripts
/models
```

---
## 8) Step-by-Step Workflow

1. Plan Targets (1–2h)
   - Choose 2–3 public sources for freelance-like profiles where scraping is allowed.
   - Define a 200–500 profile target and 2–5k review snippets.

2. Scrape (4–12h, iterative)
   - Write Playwright scripts to collect: display name (optional), headline, hourly rate, skills/tags, project counts, selected public review snippets.
   - Store raw HTML and parsed JSON to `data/raw/`.
   - Log failures and respect rate limits.

3. Clean & Normalize (2–6h)
   - Parse numbers, normalize currencies (USD), dedupe skills to canonical names.
   - Map to `freelancer_profiles.csv`. Fill missing with sensible defaults.
   - Export standardized reviews to `sentiment_reviews_raw.jsonl`.

4. Enrich via Models (4–8h)
   - Sentiment: run VADER or transformer → `score`, map to `label`.
   - Categories: zero-shot multi-label classification.
   - Suggestions: rule-based; optionally LLM rewrite pass.
   - Save to `sentiment_reviews.jsonl`.

5. Generate Synthetic Complements (2–4h)
   - Use RNG to add users/mentors, roadmap milestones, comparison snapshots.
   - Produce `users.csv`, `mentorship_requests.jsonl`, `mentorship_messages.jsonl`, and `comparisons.jsonl`.

6. Compute Aggregates (2–3h)
   - Top-category frequency, avg sentiment score, role-wise hourly benchmarks.
   - Export summary tables (`data/processed/aggregates/*.json`).

7. Prepare Seed Payloads (1–2h)
   - For each demo user, prepare API-ready payloads mapping to `README_API.md`.
   - Example: profile PATCH, feedback POSTs, roadmap POSTs, comparisons POSTs.

8. Seed Backend (1–2h)
   - Start API locally and use either `api.http` via VS Code REST Client or a Python script to POST.
   - Maintain a manifest of created IDs.

9. QA in Frontend (ongoing)
   - Verify dashboard and pages render plausible values.
   - Adjust distributions or text generation as needed.

---
## 9) Seeding the Backend (Examples)

Use the endpoints in `api.http`. Quick Python script skeleton:

```python
# scripts/seed_backend.py
import os, json, requests
BASE = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
TOKEN = os.getenv("AUTH_TOKEN")
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1) Update profile
requests.patch(f"{BASE}/freelancers/me/profile/", headers=H, json={
  "hourly_rate": 55,
  "portfolio_items": 9,
  "proposal_success_rate": 22,
  "repeat_clients_rate": 30,
  "skills": ["React","TypeScript","Node.js","UI/UX Design"]
}).raise_for_status()

# 2) Add feedback
for r in json.load(open("data/processed/sentiment_reviews_sample.json")):
    requests.post(f"{BASE}/freelancers/me/feedback/", headers=H, json={"text": r["text"]}).raise_for_status()
```

PowerShell one-liners (illustrative):
```powershell
$BASE="http://localhost:8000/api/v1"; $T="Bearer $env:AUTH_TOKEN";
$H=@{Authorization=$T; 'Content-Type'='application/json'}
Invoke-RestMethod -Method Patch -Uri "$BASE/freelancers/me/profile/" -Headers $H -Body '{"hourly_rate":60,"portfolio_items":10}'
```

---
## 10) Reproducibility & Versioning
- Commit only small samples (<= 5MB) into repo under `data/processed/samples/`.
- Store large corpora in object storage (SAS URL or S3) with checksums and version tags.
- Seed RNG with a fixed seed per generation run; record in `data/METADATA.md`.

---
## 11) Privacy, Legal, and Safety
- Respect robots.txt; comply with TOS; do not store PII.
- Strip names/emails from scraped reviews; keep only generalized text.
- Provide a takedown path for any reported content.
- Keep model prompts free of sensitive or personal data.

---
## 12) Deliverables Checklist
- [ ] `data/raw/` and `data/processed/` populated
- [ ] Working scraping scripts (or documented manual data import)
- [ ] Local sentiment/category inference scripts
- [ ] Seed script(s) or `api.http` collection with payloads
- [ ] Small sample dataset committed; larger dataset location documented
- [ ] README updates for any deviations from this plan

---
## 13) Nice-to-Haves (Future)
- Real-time websocket ingestion for mentorship messages.
- Light regression to recommend hourly_rate given metrics (with guardrails).
- Prompt library with evaluations (BLEU/ROUGE for suggestion quality not required but useful).

---
End of playbook.
