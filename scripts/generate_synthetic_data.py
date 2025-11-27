#!/usr/bin/env python
import argparse
import csv
import json
import os
from datetime import datetime, timezone
from typing import List, Dict

import numpy as np

from utils import now_iso, clamp, compute_pseudo_ranking, new_uuid

INDUSTRIES = ["Freelancer", "E-commerce", "Developer", "Business"]
SKILL_VOCAB = [
    "React", "TypeScript", "Node.js", "Python", "Django", "FastAPI", "Next.js", "GraphQL",
    "TailwindCSS", "UI/UX Design", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS",
]

DEFAULT_MILESTONES = [
    ("Fix Profile Basics", "Complete headline, overview, and add 3 portfolio items", "2-3 days"),
    ("Enhance Portfolio", "Add case studies with outcomes", "3-5 days"),
    ("Client Outreach", "Draft 5 tailored proposals", "2 days"),
    ("Referrals", "Ask 3 prior clients for testimonials", "1-2 days"),
    ("Skill Upgrade", "Finish an advanced course", "5-7 days"),
]


def rand_skills(rng: np.random.Generator) -> List[str]:
    k = rng.integers(3, 9)
    vocab = SKILL_VOCAB + [
        "Vue.js", "Angular", "Flask", "Spring Boot", "MongoDB", "MySQL", "Figma", "Jira", "CI/CD", "REST APIs", "GraphQL", "SASS", "Webpack", "GCP", "Azure", "Firebase", "ElasticSearch", "RabbitMQ", "Microservices", "Testing", "PyTorch", "TensorFlow", "Keras", "Pandas", "Matplotlib", "Seaborn", "Scrum", "Agile", "Leadership", "Communication", "Problem Solving"
    ]
    return sorted(list(rng.choice(vocab, size=k, replace=False)))


def gen_users(rng: np.random.Generator, n_users: int) -> List[Dict]:
    rows = []
    mentors = set(rng.choice(np.arange(n_users), size=max(1, n_users // 5), replace=False))
    for i in range(n_users):
        uid = new_uuid()
        rows.append({
            "id": uid,
            "name": f"User {i+1}",
            "email": f"user{i+1}@example.com",
            "is_mentor": bool(i in mentors),
            "industry": str(rng.choice(INDUSTRIES)),
            "created_at": now_iso(),
        })
    return rows


def gen_profiles(rng: np.random.Generator, users: List[Dict]) -> List[Dict]:
    rows = []
    for u in users:
        profile_completeness = float(clamp(rng.normal(rng.integers(60, 90), rng.integers(8, 20)), 20, 100))
        proposal_success_rate = float(clamp(rng.normal(rng.integers(10, 40), rng.integers(5, 15)), 0, 100))
        portfolio_items = int(max(0, rng.poisson(rng.integers(3, 15))))
        repeat_clients_rate = float(clamp(rng.normal(rng.integers(10, 50), rng.integers(5, 20)), 0, 100))
        hourly_rate = int(clamp(np.exp(rng.normal(np.log(rng.integers(20, 120)), rng.uniform(0.2, 0.6))), 10, 200))
        profile_views = int(max(0, rng.normal(rng.integers(100, 2000), rng.integers(50, 400))))
        job_invitations = int(max(0, rng.normal(rng.integers(1, 15), rng.integers(1, 5))))

        rows.append({
            "user_id": u["id"],
            "profile_completeness": int(round(profile_completeness)),
            "profile_views": profile_views,
            "proposal_success_rate": int(round(proposal_success_rate)),
            "job_invitations": job_invitations,
            "hourly_rate": hourly_rate,
            "skills": ";".join(rand_skills(rng)),
            "portfolio_items": portfolio_items,
            "repeat_clients_rate": int(round(repeat_clients_rate)),
            "updated_at": now_iso(),
        })
    return rows


def gen_milestones(rng: np.random.Generator, users: List[Dict]) -> List[Dict]:
    rows = []
    for u in users:
        for order, (title, desc, effort) in enumerate(DEFAULT_MILESTONES, start=1):
            rows.append({
                "id": new_uuid(),
                "user_id": u["id"],
                "title": title,
                "description": desc,
                "estimated_effort": effort,
                "order": order,
                "completed": bool(rng.random() < 0.4),
                "created_at": now_iso(),
            })
    return rows


def gen_sentiment_reviews(rng: np.random.Generator, users: List[Dict]) -> List[Dict]:
    templates = [
        ("positive", 0.7, "Great communication and timely delivery. Would hire again."),
        ("positive", 0.6, "Solid work, clear updates, responsive to feedback."),
        ("neutral", 0.0, "Work met expectations, a few revisions needed but acceptable."),
        ("negative", -0.6, "Missed a deadline and final polish needed more attention."),
        ("positive", 0.8, "Outstanding quality and proactive suggestions on scope."),
        ("neutral", -0.1, "Communication could be faster but overall fine."),
        ("negative", -0.7, "Project scope was unclear and deadlines were missed."),
        ("positive", 0.9, "Exceptional technical skills and leadership throughout the project."),
        ("neutral", 0.1, "Average experience, some communication gaps but work delivered."),
        ("negative", -0.5, "Quality did not meet expectations, required multiple revisions."),
        ("positive", 0.75, "Very proactive, provided valuable suggestions and improvements."),
        ("neutral", 0.05, "Work was completed, but documentation was lacking."),
        ("negative", -0.4, "Responsiveness was slow, and updates were infrequent."),
        ("positive", 0.85, "Delivered ahead of schedule, excellent attention to detail."),
        ("neutral", -0.05, "Some minor issues, but overall satisfactory performance."),
    ]
    rows = []
    per_user = rng.integers(3, 10)
    use_users = users[: min(len(users), 20)]
    for u in use_users:
        for _ in range(per_user):
            label, score, text = templates[int(rng.integers(0, len(templates)))]
            # Add randomization to text
            text = text.replace("communication", rng.choice(["communication", "collaboration", "teamwork", "client interaction"]))
            text = text.replace("quality", rng.choice(["quality", "output", "results", "deliverables"]))
            text = text.replace("deadline", rng.choice(["deadline", "timeline", "due date", "milestone"]))
            text = text.replace("project", rng.choice(["project", "assignment", "task", "engagement"]))
            text = text.replace("feedback", rng.choice(["feedback", "input", "comments", "suggestions"]))
            rows.append({
                "id": new_uuid(),
                "user_id": u["id"],
                "text": text,
                "score": round(float(score + rng.normal(0, 0.1)), 2),
                "label": label,
                "categories": [],
                "suggestions": [],
                "created_at": now_iso(),
            })
    return rows


def gen_comparisons(rng: np.random.Generator, profiles: List[Dict], users: List[Dict]) -> List[Dict]:
    # Use ranking formula to snapshot pseudo-ranking against a pseudo competitor
    rows = []
    prof_by_user = {p["user_id"]: p for p in profiles}
    for u in users[: min(15, len(users))]:
        p = prof_by_user[u["id"]]
        # assume 5 milestones total, count completed from generated milestones later (approximate here)
        score, _ = compute_pseudo_ranking(p, milestone_count=2, total_milestones=5)
        rows.append({
            "id": new_uuid(),
            "user_id": u["id"],
            "competitor_identifier": f"competitor:{u['id'][:8]}",
            "competitor_role": "frontend",
            "pseudo_ranking": score,
            "snapshot": {
                "profile_completeness": p["profile_completeness"],
                "proposal_success_rate": p["proposal_success_rate"],
                "portfolio_items": p["portfolio_items"],
                "hourly_rate": p["hourly_rate"],
                "repeat_clients_rate": p["repeat_clients_rate"],
            },
            "created_at": now_iso(),
        })
    return rows


def gen_mentorship(rng: np.random.Generator, users: List[Dict]):
    requests_rows = []
    messages_rows = []
    topics = [
        "Improve React performance patterns",
        "Portfolio storytelling",
        "Proposal strategy",
        "Scaling backend APIs",
    ]
    requesters = users[: min(10, len(users))]
    mentors = [u for u in users if u["is_mentor"]]
    for i, u in enumerate(requesters):
        req_id = new_uuid()
        mentor_id = mentors[i % max(1, len(mentors))]["id"] if mentors else None
        requests_rows.append({
            "id": req_id,
            "requester_id": u["id"],
            "mentor_id": mentor_id,
            "topic": topics[i % len(topics)],
            "context": "Looking for guidance and code review on recent work.",
            "preferred_expertise": ["Senior Frontend", "Performance"],
            "status": "pending",
            "created_at": now_iso(),
        })
        messages_rows.append({
            "id": new_uuid(),
            "request_id": req_id,
            "sender_id": u["id"],
            "text": "Hi! Can you review my memo?",
            "created_at": now_iso(),
        })
    return requests_rows, messages_rows


def write_csv(path: str, rows: List[Dict], headers: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic datasets for FairFound.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--users", type=int, default=50)
    ap.add_argument("--out", type=str, default="data/processed")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    users = gen_users(rng, args.users)
    profiles = gen_profiles(rng, users)
    milestones = gen_milestones(rng, users)
    reviews = gen_sentiment_reviews(rng, users)
    comparisons = gen_comparisons(rng, profiles, users)
    m_requests, m_messages = gen_mentorship(rng, users)

    # Industries static
    industries = [
        {"slug": "freelancer", "name": "Freelancer", "description": "Freelance professionals", "features": ["profiles", "roadmap", "sentiment"]},
        {"slug": "ecommerce", "name": "E-commerce", "description": "Online stores and sellers", "features": ["catalog", "conversion"]},
        {"slug": "developer", "name": "Developer", "description": "Software engineers and teams", "features": ["repos", "pipelines"]},
        {"slug": "business", "name": "Business", "description": "General business profiles", "features": ["metrics", "insights"]},
    ]

    # Write outputs
    out = args.out
    write_csv(
        os.path.join(out, "users.csv"), users,
        ["id", "name", "email", "is_mentor", "industry", "created_at"],
    )
    write_csv(
        os.path.join(out, "freelancer_profiles.csv"), profiles,
        [
            "user_id", "profile_completeness", "profile_views", "proposal_success_rate",
            "job_invitations", "hourly_rate", "skills", "portfolio_items", "repeat_clients_rate", "updated_at"
        ],
    )
    write_csv(
        os.path.join(out, "roadmap_milestones.csv"), milestones,
        ["id", "user_id", "title", "description", "estimated_effort", "order", "completed", "created_at"],
    )

    # JSON/JSONL
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "industries.json"), 'w', encoding='utf-8') as f:
        json.dump(industries, f, ensure_ascii=False, indent=2)

    def write_jsonl(path: str, rows: List[Dict]):
        with open(path, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    write_jsonl(os.path.join(out, "comparisons.jsonl"), comparisons)
    write_jsonl(os.path.join(out, "sentiment_reviews.jsonl"), reviews)
    write_jsonl(os.path.join(out, "mentorship_requests.jsonl"), m_requests)
    write_jsonl(os.path.join(out, "mentorship_messages.jsonl"), m_messages)

    print(f"Generated datasets under {out}")


if __name__ == "__main__":
    main()
