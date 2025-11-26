# FairFound – Freelancer Frontend

A Vite + React + TypeScript app for the FairFound platform. It helps freelancers understand their standing (pseudo‑ranking), improve profiles with a guided roadmap, compare profiles, analyze client sentiment, and request mentorship. This repo is frontend‑only; it integrates with a Django REST API (see API spec below) and supports a data workflow for seeding and experimentation.

## Overview
- Built with Vite, React 18, TypeScript, TailwindCSS, and shadcn/ui (Radix primitives).
- Routing via `react-router-dom`.
- Local state and demo data via context/localStorage; easily replaceable with real API calls.
- Production‑ready component library for forms, dialogs, toasts, tables, charts, etc.

## Tech Stack
- React 18, TypeScript
- Vite 5
- TailwindCSS + tailwind-merge + class-variance-authority
- shadcn/ui (Radix UI)
- recharts (basic charts)
- react-hook-form, zod (forms/validation scaffolding)

## Key Features
- Authentication pages: Login and Registration (UI scaffolding).
- Industry selection onboarding: picks the user’s industry to tailor the experience.
- Freelancer suite:
	- Profile: edit core metrics; compute pricing suggestions using pseudo‑ranking.
	- Dashboard: quick metrics, ranking badge, shortcuts to comparisons and roadmap.
	- Profile Comparison: compare to competitor/top averages; save snapshots to history.
	- Comparison History + Detail: list, open detail pages with charts.
	- Career Roadmap: milestones with completion tracking; impacts ranking.
	- Insights & Re‑Evaluation: show effects of improvements and progress since last save.
	- Sentiment Insights: add client feedback; see labels, categories, suggestions; CSV export.
- Mentorship:
	- Freelancer side: create mentorship requests and message threads.
	- Professional side: mentor dashboard to review/accept requests.
- Navigation/footer components and shared UI primitives.

## Recent Additions
- Logout confirmation dialog (with cancel/confirm) on Profile page.
- Toast system improvements: configurable limit and auto‑dismiss; success toasts on key actions.
- Sentiment CSV export utility and Export button on Sentiment Insights page.
- Backend collaboration docs added:
	- `README_API.md` – complete backend spec (models, endpoints, validation, guidance).
	- `api.http` – executable REST Client collection for all endpoints.
	- `README_DATA.md` – data science playbook for scraping, synthesis, and seeding.

## Project Structure
- `src/pages` – route pages (Freelancer, Professional, Landing, Auth, Onboarding)
- `src/components` – UI components (shadcn/ui) and custom widgets
- `src/context/AppContext.tsx` – demo state (user, profile, roadmap, sentiment, ranking)
- `src/hooks` – utilities like toasts and comparison history
- `src/lib` – helpers (utils, sentiment heuristics)
- `src/components/ui/*` – shadcn/ui primitives

## Backend API
The frontend is designed to consume a Django REST API.
- Full spec: `README_API.md`
- Endpoint examples: `api.http`
- Highlights include: auth, user/industry update, freelancer profile, ranking (current/history/save), roadmap CRUD, comparisons, sentiment reviews (aggregate/export), mentorship (requests/messages), industries, dashboard, suggestions.

## Data Workflow
For teams using dummy/scraped data and local NLP:
- Playbook: `README_DATA.md` (datasets to create, scraping rules, local models, seeding scripts).
- Local models suggested: VADER/transformers for sentiment, zero‑shot for categories.

## Development
- Prereqs: Node 18+ recommended.
- Install deps:
	- `npm install`
- Run dev server:
	- `npm run dev`
- Build:
	- `npm run build`
- Preview build:
	- `npm run preview`

## Notes & Assumptions
- Currently uses localStorage and context for demo data; hook up to real API by replacing reads/writes in context/hooks with `fetch`/React Query calls to endpoints in `api.http`.
- The toast system is configured to allow multiple concurrent toasts and shorter auto‑dismiss. You can tweak via `configureToasts` in `src/hooks/use-toast.ts`.
- Charts and some visualizations use seeded/demo values; wire them to API responses as backend lands.

## Contributing
- Keep UI components consistent with shadcn/ui patterns.
- Prefer small, composable components and co-located styles.
- Align any new endpoints with `README_API.md` and add examples to `api.http`.

## License
Internal project files. Do not redistribute without permission.

