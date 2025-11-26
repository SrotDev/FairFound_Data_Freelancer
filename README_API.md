# FairFound Backend API Specification & Django Architecture Guide

---
## 1. Domain Overview
 - `PATCH /users/me/industry/` (set selected industry enum)
Core Entities:
- User (accounts)
 - `DELETE /freelancers/me/comparisons/` (bulk clear all for user)
- SentimentReview (analyzed client feedback items)
- MentorshipRequest + MentorshipMessage (conversation thread)
 - `DELETE /freelancers/me/feedback/` (bulk clear all for user)

---
## 2. Django App Structure
Suggested project layout:
```
fairfound/
  manage.py
  fairfound/settings.py
  fairfound/urls.py
  fairfound/asgi.py
  fairfound/wsgi.py

  apps/

### 9.1.1 Selected Industry Update Request
```
{
  "industry": "Freelancer"  // Enum: Freelancer | E-commerce | Developer | Business
}
```
    accounts/          # Custom User, registration, profile endpoints
    freelancers/       # FreelancerProfile, ranking, roadmap
    comparisons/       # ComparisonEntry logic
    sentiment/         # SentimentReview + aggregation
    mentorship/        # MentorshipRequest, MentorshipMessage
    industries/        # Industry definitions
    core/              # Shared utils, mixins, services

  common/
    services/          # ranking_service.py, sentiment_service.py
    permissions/       # IsOwner, IsMentor
    pagination.py
    validators.py
```

Each app exposes `routers.py` or `urls.py` aggregated by root `fairfound/urls.py`.

---
## 3. Models
Use UUID primary keys where externally exposed (except optional integer for User if easier). PostgreSQL JSONB for arrays.

### 3.1 User (accounts.models.User)
Extends `AbstractUser` or `AbstractBaseUser`.
Fields:
- `id: UUIDField(pk)`
- `email: EmailField(unique)`
- `name: CharField(150)`
- `is_mentor: BooleanField(default=False)` (flag to access mentor dashboard)
- `date_joined: DateTimeField(auto_now_add=True)`
Indexes: email unique.

### 3.2 FreelancerProfile (freelancers.models.FreelancerProfile)
1:1 with User.
Fields (maps to frontend FreelancerMetrics):
- `user: OneToOneField(User, on_delete=CASCADE, related_name="profile")`
- `profile_completeness: PositiveSmallIntegerField(default=0)` (0–100)
- `profile_views: PositiveIntegerField(default=0)`
- `proposal_success_rate: PositiveSmallIntegerField(default=0)` (0–100)
- `job_invitations: PositiveIntegerField(default=0)`
- `hourly_rate: PositiveIntegerField(default=0)`
- `skills: ArrayField(CharField(max_length=60), default=list)` or JSONField
- `portfolio_items: PositiveSmallIntegerField(default=0)`
- `repeat_clients_rate: PositiveSmallIntegerField(default=0)` (0–100)
- `updated_at: DateTimeField(auto_now=True)`

### 3.3 RoadmapMilestone (freelancers.models.RoadmapMilestone)
Fields:
- `id: UUIDField(pk)`
- `user: ForeignKey(User, on_delete=CASCADE, related_name="roadmap_milestones")`
- `title: CharField(160)`
- `description: TextField()`
- `estimated_effort: CharField(40)`
- `completed: BooleanField(default=False)`
- `order: PositiveSmallIntegerField()`
- `created_at: DateTimeField(auto_now_add=True)`
- `updated_at: DateTimeField(auto_now=True)`
Constraint: `(user, order)` unique for deterministic ordering.

### 3.4 RankingSnapshot (freelancers.models.RankingSnapshot)
Stores historical pseudo ranking.
Fields:
- `id: UUIDField(pk)`
- `user: ForeignKey(User, on_delete=CASCADE, related_name="ranking_snapshots")`
- `value: PositiveSmallIntegerField()` (0–100)
- `breakdown: JSONField()` (component contributions)
- `created_at: DateTimeField(auto_now_add=True)`
Index: `user, -created_at` for recent retrieval.

### 3.5 ComparisonEntry (comparisons.models.ComparisonEntry)
Fields:
- `id: UUIDField(pk)`
- `user: ForeignKey(User, on_delete=CASCADE, related_name="comparisons")`
- `competitor_identifier: CharField(160)` (opaque slug/profile URL)
- `competitor_role: CharField(80)`
- `pseudo_ranking: PositiveSmallIntegerField()` (calculated at time of snapshot)
- `snapshot: JSONField()` (serialized metrics at comparison time)
- `created_at: DateTimeField(auto_now_add=True)`
Index: `user, -created_at`.

### 3.6 SentimentReview (sentiment.models.SentimentReview)
Fields:
- `id: UUIDField(pk)`
- `user: ForeignKey(User, on_delete=CASCADE, related_name="sentiment_reviews")`
- `text: TextField()`
- `score: DecimalField(max_digits=5, decimal_places=2)` (normalized -1..1 stored maybe -1.00 to 1.00)
- `label: CharField(10, choices=[positive, neutral, negative])`
- `categories: JSONField(default=list)`
- `suggestions: JSONField(default=list)`
- `created_at: DateTimeField(auto_now_add=True)`

### 3.7 MentorshipRequest (mentorship.models.MentorshipRequest)
Fields:
- `id: UUIDField(pk)`
- `requester: ForeignKey(User, on_delete=CASCADE, related_name="mentorship_requests")`
- `mentor: ForeignKey(User, null=True, blank=True, on_delete=SET_NULL, related_name="assigned_requests")`
- `topic: CharField(160)`
- `context: TextField()`
- `preferred_expertise: JSONField(default=list)`
- `status: CharField(20, choices=[pending, in_progress, completed, rejected])`
- `created_at: DateTimeField(auto_now_add=True)`
- `updated_at: DateTimeField(auto_now=True)`
Index: `status`.

### 3.8 MentorshipMessage (mentorship.models.MentorshipMessage)
Fields:
- `id: UUIDField(pk)`
- `request: ForeignKey(MentorshipRequest, on_delete=CASCADE, related_name="messages")`
- `sender: ForeignKey(User, on_delete=CASCADE)`
- `text: TextField()`
- `created_at: DateTimeField(auto_now_add=True)`

### 3.9 Industry (industries.models.Industry)
Fields:
- `id: UUIDField(pk)`
- `slug: SlugField(unique)`
- `name: CharField(100)`
- `description: TextField()`
- `features: JSONField(default=list)` (list of strings)

---
## 4. Services (Domain Logic)
### 4.1 Ranking Service (`ranking_service.py`)
Function: `compute_pseudo_ranking(profile: FreelancerProfile, milestone_count: int, total_milestones: int) -> (int, dict)`.
Formula (mirrors frontend):
```
score = clamp( profile.profile_completeness * 0.25
             + min(profile.proposal_success_rate * 2, 30)
             + min(profile.portfolio_items * 3, 20)
             + min(profile.repeat_clients_rate, 15)
             + (milestone_count/total_milestones)*15 ) to 0..100
```
Return breakdown dict for transparency.

### 4.2 Sentiment Service (`sentiment_service.py`)
Function: `analyze_text(text: str) -> dict` returns `{score, label, categories, suggestions}`. Use lightweight heuristic or ML model (transformers) behind asynchronous task. Provide deterministic fallback for dev.

### 4.3 Aggregation
`aggregate_reviews(user) -> {positives, neutrals, negatives, avg_score, top_categories, actionable_suggestions}` with Postgres queries & `Func` for arrays.

---
## 5. Serializers
Use DRF ModelSerializers; hide internal fields where not needed.
Key serializers:
- `UserSerializer` (id, name, email, is_mentor, date_joined)
- `FreelancerProfileSerializer`
- `RoadmapMilestoneSerializer`
- `RankingSnapshotSerializer`
- `ComparisonEntrySerializer`
- `SentimentReviewSerializer`
- `MentorshipRequestSerializer`
- `MentorshipMessageSerializer`
- `IndustrySerializer`
- Aggregate serializer objects for sentiment & dashboard responses.

---
## 6. Authentication & Permissions
- JWT access (short lived) + refresh.
- Endpoints under `/auth/` for register/login/refresh/logout.
- Custom permissions:
  - `IsOwner` for modifying own milestones/profile.
  - `IsMentor` for mentor dashboard requests.
  - `IsRequesterOrMentor` for mentorship messages.
- Rate-limit sentiment submission (e.g., 200/day) using `django-ratelimit`.

---
## 7. Pagination & Query Params
Use DRF `PageNumberPagination` with `page` and `page_size` (default 20, max 100). All list endpoints: comparisons, feedback, roadmap (optional), mentorship requests.

Filtering examples:
- `/mentorship/dashboard/requests/?status=pending`
- `/freelancers/me/comparisons/?role=frontend`
- `/sentiment/?label=negative` (optional future scope)

---
## 8. REST Endpoints (Complete)
Base prefix: `/api/v1/`

### 8.1 Health
- `GET /health/` → `{status: "ok", time: ISO8601}`

### 8.2 Auth
- `POST /auth/register/` → create user
- `POST /auth/login/` → `{access, refresh}`
- `POST /auth/refresh/` → new access
- `POST /auth/logout/` → invalidate refresh
- `GET /auth/me/` → current user

### 8.3 Users
- `GET /users/{id}/`
- `PATCH /users/me/` (name, email)

### 8.4 Freelancer Profile
- `GET /freelancers/me/profile/`
- `PATCH /freelancers/me/profile/` (partial update)
- `GET /freelancers/{id}/profile/` (public subset) – optional

### 8.5 Ranking
- `GET /freelancers/me/ranking/` → current + previous + improvement + breakdown
- `POST /freelancers/me/ranking/save/` → create snapshot
- `GET /freelancers/me/ranking/history/` → list snapshots (paginate)

### 8.6 Roadmap
- `GET /freelancers/me/roadmap/`
- `POST /freelancers/me/roadmap/`
- `PATCH /freelancers/me/roadmap/{uuid}/`
- `DELETE /freelancers/me/roadmap/{uuid}/`
- `POST /freelancers/me/roadmap/{uuid}/toggle/`

### 8.7 Comparisons
- `GET /freelancers/me/comparisons/`
- `POST /freelancers/me/comparisons/`
- `GET /freelancers/me/comparisons/{uuid}/`
- `DELETE /freelancers/me/comparisons/{uuid}/`

### 8.8 Sentiment Reviews
- `GET /freelancers/me/feedback/`
- `POST /freelancers/me/feedback/` (body: `{text}`)
- `DELETE /freelancers/me/feedback/{uuid}/`
- `GET /freelancers/me/feedback/aggregate/`
- `GET /freelancers/me/feedback/export/` (query `format=csv`)

### 8.9 Mentorship
- `GET /mentorship/requests/?mine=true` (requester view)
- `POST /mentorship/requests/`
- `GET /mentorship/requests/{uuid}/`
- `PATCH /mentorship/requests/{uuid}/` (mentor sets status/assignment)
- `GET /mentorship/dashboard/requests/` (mentor aggregated view)
- `POST /mentorship/requests/{uuid}/messages/`
- `GET /mentorship/requests/{uuid}/messages/`

### 8.10 Industries
- `GET /industries/`
- `GET /industries/{slug}/`

### 8.11 Dashboard
- `GET /freelancers/me/dashboard/` → merged object {profile, ranking, roadmap_progress, next_milestones:[...]}

### 8.12 Suggestions
- `GET /freelancers/suggestions/?role=frontend&limit=5` → competitor suggestions (placeholder logic)

### 8.13 System
- `GET /system/rate-limit/` → remaining quotas (optional)

---
## 9. Example JSON Schemas
Use `camel_case` in frontend; backend may serve `snake_case`. Provide consistent serializer naming or transform.

### 9.1 FreelancerProfile Response
```
{
  "user_id": "8c7d...",
  "profile_completeness": 72,
  "proposal_success_rate": 18,
  "hourly_rate": 45,
  "portfolio_items": 8,
  "repeat_clients_rate": 25,
  "skills": ["React", "TypeScript", "Node.js", "UI/UX Design"],
  "updated_at": "2025-11-25T09:15:00Z"
}
```

### 9.2 Ranking Response
```
{
  "current": 68,
  "previous": 64,
  "improvement": 4,
  "breakdown": {
    "profile_completeness": 18,
    "proposal_success": 30,
    "portfolio": 12,
    "repeat_clients": 10,
    "milestone_bonus": 5
  }
}
```

### 9.3 RoadmapMilestone
```
{
  "id": "3d91...",
  "title": "Fix Profile Basics",
  "description": "Complete your headline, overview, and add 3 strong portfolio items",
  "estimated_effort": "2-3 days",
  "completed": false,
  "order": 1
}
```

### 9.4 ComparisonEntry
```
{
  "id": "ab12...",
  "competitor_identifier": "freelancer:top_user_123",
  "competitor_role": "frontend",
  "pseudo_ranking": 72,
  "snapshot": {
    "profile_completeness": 72,
    "proposal_success_rate": 18,
    "portfolio_items": 8,
    "hourly_rate": 45,
    "repeat_clients_rate": 25
  },
  "created_at": "2025-11-25T09:28:11Z"
}
```

### 9.5 SentimentReview
```
{
  "id": "fb_123",
  "text": "Great communication and fast delivery, minor issues with final polish.",
  "score": 0.76,
  "label": "positive",
  "categories": ["communication", "quality"],
  "suggestions": ["Provide structured progress updates"],
  "created_at": "2025-11-25T09:30:00Z"
}
```

### 9.6 Sentiment Aggregate
```
{
  "positives": 12,
  "neutrals": 5,
  "negatives": 3,
  "avg_score": 0.44,
  "top_categories": ["communication", "quality", "responsiveness"],
  "actionable_suggestions": ["Provide structured progress updates", "Ask for a brief quality score"]
}
```

### 9.7 MentorshipRequest
```
{
  "id": "req_456",
  "topic": "Improve React performance patterns",
  "context": "I have 3 years experience; need guidance on scaling large component trees",
  "preferred_expertise": ["Senior Frontend", "Performance"],
  "status": "pending",
  "requester_id": "8c7d...",
  "mentor_id": null,
  "created_at": "2025-11-25T09:40:00Z",
  "updated_at": "2025-11-25T09:40:00Z"
}
```

### 9.8 MentorshipMessage
```
{
  "id": "msg_789",
  "request_id": "req_456",
  "sender_id": "8c7d...",
  "text": "Thanks for the initial guidance, could you review my memo?",
  "created_at": "2025-11-25T09:55:00Z"
}
```

### 9.9 Dashboard
```
{
  "profile": { ... },
  "ranking": { ... },
  "roadmap_progress": {"completed": 2, "total": 5, "percent": 40.0},
  "next_milestones": [ {"id": "...", "title": "Skill Upgrade"} ]
}
```

---
## 10. Validation Rules
- Rates & percentages clamped (0–100 where applicable).
- Skills: max length 60 per item; maximum 50 skills.
- Roadmap order positive; cannot duplicate order for same user.
- Sentiment text length: 10–5000 chars.
- Mentorship context length max 5000.
- Comparison snapshot fields must be numeric integers or positive small ints.

---
## 11. Error Format
Consistent DRF error envelope:
```
{
  "error": {
    "code": "validation_error",
    "detail": "Portfolio items must be >= 0",
    "fields": {"portfolio_items": ["Ensure this value is greater than or equal to 0."]}
  }
}
```
Authorization example:
```
{
  "error": {"code": "not_authenticated", "detail": "Authentication credentials were not provided."}
}
```

---
## 12. Rate Limiting (Optional)
Strategy: IP + User based bucket for sentiment submissions & comparison creation (e.g., 200/day, 100/day). Expose counts at `/system/rate-limit/`.

---
## 13. Caching
- Cache ranking calculations for user (invalidate on profile or milestone change).
- Aggregate sentiment summary cached (invalidate on new review).
- Industry list & details cached long-lived.

---
## 14. Testing Guidelines
- Model tests: constraints, ordering.
- Service tests: ranking & sentiment functions.
- API tests: auth cycle, CRUD on milestones, comparison creation, aggregation endpoints.
- Permissions tests: mentorship dashboard restricted to `is_mentor` users.

---
## 15. Security & Privacy
- Store only text reviews; avoid PII beyond what's provided.
- Allow user to delete any SentimentReview (hard delete).
- Ensure mentors cannot view other private user data except request context.
- Enforce HTTPS & secure cookies for refresh token if using cookie strategy.

---
## 16. Deployment Considerations
- Use separate worker (Celery + Redis) if sentiment analysis becomes asynchronous.
- Database migrations: create initial schema with apps listed.
- Observability: add `/health/` and optional `/metrics/` for Prometheus.

---
## 17. Implementation Order (Recommended)
1. Accounts & Auth
2. FreelancerProfile + Roadmap
3. Ranking service + snapshots
4. Comparisons
5. Sentiment ingestion + aggregation
6. Mentorship (requests + messages)
7. Industries
8. Dashboard + suggestions
9. Rate limiting & caching layer

---
## 18. Open Extensions (Future)
- WebSocket for mentorship real-time messages
- Historical trend endpoints for ranking & sentiment
- Multi-industry support with different metrics mapping

---
## 19. Endpoint Inventory Quick Reference
(See `api.http` for examples)
```
GET  /health/
POST /auth/register/
POST /auth/login/
POST /auth/refresh/
POST /auth/logout/
GET  /auth/me/
GET  /users/{id}/
PATCH /users/me/
GET  /freelancers/me/profile/
PATCH /freelancers/me/profile/
GET  /freelancers/{id}/profile/ (optional public)
GET  /freelancers/me/ranking/
POST /freelancers/me/ranking/save/
GET  /freelancers/me/ranking/history/
GET  /freelancers/me/roadmap/
POST /freelancers/me/roadmap/
PATCH /freelancers/me/roadmap/{uuid}/
DELETE /freelancers/me/roadmap/{uuid}/
POST /freelancers/me/roadmap/{uuid}/toggle/
GET  /freelancers/me/comparisons/
POST /freelancers/me/comparisons/
GET  /freelancers/me/comparisons/{uuid}/
DELETE /freelancers/me/comparisons/{uuid}/
GET  /freelancers/me/feedback/
POST /freelancers/me/feedback/
DELETE /freelancers/me/feedback/{uuid}/
GET  /freelancers/me/feedback/aggregate/
GET  /freelancers/me/feedback/export/
GET  /mentorship/requests/
POST /mentorship/requests/
GET  /mentorship/requests/{uuid}/
PATCH /mentorship/requests/{uuid}/
GET  /mentorship/dashboard/requests/
POST /mentorship/requests/{uuid}/messages/
GET  /mentorship/requests/{uuid}/messages/
GET  /industries/
GET  /industries/{slug}/
GET  /freelancers/me/dashboard/
GET  /freelancers/suggestions/
GET  /system/rate-limit/
```

---
## 20. Feeding to an LLM
Provide this entire file + `api.http`. Instruct LLM:
"Generate Django apps & models as defined. Implement DRF viewsets/routers for each REST endpoint (read-only where noted). Include JWT auth with simplejwt, custom permissions, and full serializer coverage. Add ranking & sentiment service functions. Ensure responses match provided JSON schemas and error contract." Use incremental generation by section to avoid token limits.

---
## 21. License / IP Notice
All specifications proprietary to FairFound project; do not expose externally without approval.

---
End of specification.
