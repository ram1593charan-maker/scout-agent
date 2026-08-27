# ScoutAgent 🕵️

**Autonomous local-business lead research agent.** Give it a niche + city, and it
plans, searches, verifies, scores, and writes outreach-ready lead data — all in
the background, while you do something else.

Built for the **All Things Agentic Hackathon** (Taskmaster track) with
**Gemini 3.5 Flash + Google ADK + Google Cloud**.

## The problem

Finding verified local-business leads with real "pain signals" (dead website,
no mobile support, missing pages) takes hours of manual browsing. Sales teams
and agencies burn time on research instead of selling.

## What ScoutAgent does

1. **Plan** — takes one input (`niche + city`), decomposes it into research steps
2. **Search** — discovers businesses via web search (DuckDuckGo)
3. **Verify** — visits each website: live/dead, mobile-friendly, load time, missing signals
4. **Score** — rates "digital pain" 0–100 (higher = better prospect)
5. **Write** — generates a personalized 2-line outreach draft per lead
6. **Deliver** — outputs CSV + summary report asynchronously

## Architecture

```
User (Web UI)
   │  niche + city
   ▼
ScoutAgent (ADK LlmAgent, Gemini 3.5 Flash)
   ├── plan_research()      → research plan
   ├── search_businesses()  → DuckDuckGo search tool
   ├── verify_website()     → httpx probe + HTML analysis
   ├── score_lead()         → heuristic pain scoring
   └── draft_outreach()     → Gemini-personalized draft
   │
   ▼
Cloud Run (async job) → CSV + report → notify
```

## Quickstart

```bash
git clone https://github.com/ram1593charan-maker/scout-agent.git
cd scout-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY
# Run the agent CLI
python -m scout_agent.cli "salons" "Pune"
# Or run the web UI
uvicorn web.app:app --port 8080
```

## Deploy to Google Cloud (Cloud Run)

```bash
gcloud run deploy scout-agent --source . --region asia-south1 --allow-unauthenticated
```

## Tech

- **Gemini 3.5 Flash** — planning, scoring rationale, outreach drafts
- **Google ADK 2.8** — agent orchestration + tool calling
- **FastAPI** — web UI + async job API
- **httpx** — website verification probes
- **DuckDuckGo search** — business discovery (no API key needed)

## Findings & learnings

(documented after the build — see docs/)
