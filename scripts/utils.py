import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

import numpy as np

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
except Exception:  # pragma: no cover - optional at runtime
    nltk = None
    SentimentIntensityAnalyzer = None


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def clamp(x: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, x)))


def compute_pseudo_ranking(profile: Dict, milestone_count: int, total_milestones: int) -> Tuple[int, Dict[str, float]]:
    """Mirror README_API 4.1 formula.
    score = clamp( profile.profile_completeness * 0.25
                 + min(profile.proposal_success_rate * 2, 30)
                 + min(profile.portfolio_items * 3, 20)
                 + min(profile.repeat_clients_rate, 15)
                 + (milestone_count/total_milestones)*15 ) to 0..100
    """
    pc = float(profile.get("profile_completeness", 0))
    ps = float(profile.get("proposal_success_rate", 0))
    pf = float(profile.get("portfolio_items", 0))
    rr = float(profile.get("repeat_clients_rate", 0))
    total = max(1, int(total_milestones))
    done = clamp(float(milestone_count), 0, total)
    breakdown = {
        "profile_completeness": pc * 0.25,
        "proposal_success": min(ps * 2.0, 30.0),
        "portfolio": min(pf * 3.0, 20.0),
        "repeat_clients": min(rr, 15.0),
        "milestone_bonus": (done / total) * 15.0,
    }
    score = clamp(sum(breakdown.values()), 0.0, 100.0)
    return int(round(score)), breakdown


def ensure_vader() -> None:
    """Ensure VADER lexicon is available for NLTK sentiment."""
    if nltk is None:
        return
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon')


def vader_score(text: str) -> float:
    """Return compound score in [-1, 1] using VADER; fallback to 0 for missing deps."""
    if nltk is None or SentimentIntensityAnalyzer is None:
        return 0.0
    ensure_vader()
    sia = SentimentIntensityAnalyzer()
    return float(sia.polarity_scores(text).get("compound", 0.0))


def label_from_score(score: float) -> str:
    if score >= 0.2:
        return "positive"
    if score <= -0.2:
        return "negative"
    return "neutral"


def write_jsonl(path: str, rows: Iterable[Dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def new_uuid() -> str:
    return str(uuid.uuid4())
