# CivicBriefs.ai

CivicBriefs.ai is an AI-powered UPSC preparation platform that combines three workflows in one product:
- Daily current-affairs capsule generation
- Section-wise mock test + performance analytics
- Personalized improvement planning

## Demo Video
▶️ [Watch Full Demo](https://drive.google.com/file/d/1fBkrOP1G0kAO2E-t8SB7_lU8afTQW3Ne/view?usp=sharing)

## Why this application was built
UPSC aspirants usually use disconnected tools for news, practice tests, and planning. That creates three major issues:
1. News is consumed but not converted into exam-focused revision.
2. Mock test results are seen, but not translated into clear next actions.
3. Study planning is generic instead of adaptive to actual weak sections.

CivicBriefs.ai solves this by turning daily inputs (news + attempts) into actionable outputs (capsules + score diagnostics + focused study plan).

## What the application contains
### 1. Authentication and user workspace
- Sign up / login
- Dashboard with score, streak, reminders, and activity feed
- Per-user history for reports and capsule interactions

### 2. Daily news capsule system
- Fetches UPSC-relevant news from trusted sources
- Filters low-quality / blocked domains
- Summarizes into exam-oriented capsule format
- Stores date-wise capsules for dashboard reading
- Sends daily email capsule to active subscribers

### 3. Planner lab (mock test + analysis)
- Adaptive sectional mock test UI
- Question palette with progress tracking
- Submit confirmation modal
- Instant report generation after submission
- Section strength analysis (weak/average/strong)
- You-vs-topper benchmark graph
- Priority focus topics + wrong-question review
- Download attempt paper / JSON report

### 4. Personalized study planning
- Converts section-wise accuracy into weekly allocations
- Generates 7-day and 30-day guidance
- Builds improvement summary based on latest attempt

## Core components and what each does
| Component | Path | Responsibility |
|---|---|---|
| FastAPI app entry | `app/main.py` | Starts API, registers routes, starts scheduler |
| Auth routes | `app/api/routes/auth.py` | Session, login, signup, subscription status |
| Planner routes/UI | `app/api/routes/agents.py` | Test generation, submit, planner UI/report rendering |
| News routes | `app/api/routes/news.py` | Capsule APIs and related endpoints |
| Planner engine | `app/agents/planner_agent.py` | Test prep, evaluation, plan generation |
| News collection | `app/agents/news/news_collection.py` | Fetch/scrape/filter/chunk/embed news |
| Capsule generator | `app/agents/generate_news_capsule.py` | Builds capsule artifacts (md/json/pdf) |
| Scheduler | `app/services/capsule_scheduler.py` | Daily 6:00 AM dispatch and startup catch-up |
| Subscriber store | `app/services/subscriber_store.py` | Subscription state + once-per-day email dedupe |
| Web pages | `app/web/pages.py` | Dashboard and portal frontend templates |

## Project file structure
```text
CivicBriefs.ai/
├── app/
│   ├── main.py
│   ├── __main__.py
│   ├── requirements.txt
│   ├── agents/
│   │   ├── news_agent.py
│   │   ├── planner_agent.py
│   │   ├── news_collection.py
│   │   ├── generate_news_capsule.py
│   │   ├── convert_to_pdf.py
│   │   ├── build_chroma_embeddings.py
│   │   └── news/
│   │       ├── news_collection.py
│   │       ├── generate_news_capsule.py
│   │       └── pipeline.py
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── news.py
│   │       └── agents.py
│   ├── services/
│   │   ├── mongo.py
│   │   ├── mailer.py
│   │   ├── news_mailer.py
│   │   ├── news_store.py
│   │   ├── news_summary.py
│   │   ├── capsule_scheduler.py
│   │   ├── subscriber_store.py
│   │   ├── report_store.py
│   │   ├── user_store.py
│   │   └── user_capsule_store.py
│   ├── utils/
│   │   ├── llm_utils.py
│   │   ├── planner_utils.py
│   │   ├── markdown_utils.py
│   │   ├── pdf_utils.py
│   │   ├── chroma_utils.py
│   │   └── calendar_tool.py
│   └── web/
│       └── pages.py
├── scripts/
│   └── dev_server.py
├── data/
├── chroma_store/
├── README.md
├── requirements.txt
├── Procfile
├── .env
└── .gitignore
```

Notes:
- `app/agents/news/` contains the newer news pipeline modules.
- `app/agents/` also has compatibility wrappers and utility scripts.
- `app/web/pages.py` contains embedded dashboard and portal frontend templates.

## Tech stack
- Backend: FastAPI, Python
- Database: MongoDB
- Vector/semantic tooling: Sentence Transformers, ChromaDB
- Summarization/planning: OpenAI-compatible LLM endpoint (local or remote)
- Email: SMTP-based sending
- Frontend: Server-rendered HTML/CSS/JS templates

## Run locally
### Prerequisites
- Python 3.10+
- MongoDB (local or Atlas)
- Required API keys in `.env`

### 1) Install
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
```

### 2) Configure `.env`
At minimum configure:
- `MONGODB_URI`
- `NEWS_API_KEY1`
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY`
- SMTP/email settings used by your mailer

### 3) Start backend
```powershell
python scripts/dev_server.py
```

Server default:
- `http://127.0.0.1:8005/`

Useful routes:
- Home: `http://127.0.0.1:8005/`
- Dashboard: `http://127.0.0.1:8005/dashboard`
- Planner Lab: `http://127.0.0.1:8005/agents/planner/ui`

## How to use the system
1. Create account and login.
2. Open Planner Lab and start a mock test.
3. Submit test (confirmation popup appears).
4. Review score, weak/strong sections, and focus topics.
5. Open dashboard to track activity and date-wise score history.
6. Read daily capsule on dashboard or receive capsule by email.

## Daily capsule automation behavior
- Scheduler target time: 6:00 AM (configurable)
- Startup catch-up: if backend starts after 6:00 AM, it still dispatches that day
- One-time daily email per user enforced via delivery claim (`last_sent_on`)

## Deployment notes
For recruiter/HR demo links, deploy web backend on Render/Railway.
Recommended production split:
- Web service for API/UI
- Scheduled job for capsule generation/dispatch reliability

## Security notes
- Never commit `.env`.
- Rotate exposed keys immediately if leaked.
- Keep secrets only in deployment environment variables.

## Author objective
This project demonstrates end-to-end product thinking:
- data pipeline + AI integration
- user workflow design
- adaptive analytics UX
- backend automation and delivery reliability
