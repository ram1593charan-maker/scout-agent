# PASTE-READY: All Things Agentic — Devpost submission fields
*Fill these into the Devpost "Submit project" form once Cloud Run is deployed.*

## Project name
ScoutAgent

## Tagline (short)
An autonomous agent that finds, verifies, and scores local-business leads — while you do something else.

## "Built with" tags
Gemini, Google ADK, Google Cloud, Cloud Run, Python, FastAPI, OpenStreetMap

## Description (paste into the text-description box)
**The problem.** Most AI waits for you to ask. Finding which local businesses
actually *need* a website — the research pass before any sales outreach — takes
hours of manual browsing. I run a business that builds sites for local shops, and
that research was the bottleneck.

**What ScoutAgent does.** Give it one input — a niche and a city — and it
autonomously plans the research, searches OpenStreetMap, visits every website,
checks whether each is live / HTTPS / mobile-friendly / fast, scores the
"digital pain" 0–100, and writes a personalised outreach draft per lead. A goal
in, a finished, actionable, outreach-ready deliverable out — in the background.
Businesses with **no website at all** score 100 (the hottest leads) and are
flagged automatically.

**Why it's "agentic."** It's not a chatbot that writes text. It's a Taskmaster:
it takes a messy multi-step chore (lead research), decomposes it, calls four
tools in sequence, handles the details, and delivers the result to the right
place (CSV + report + web UI) without further prompting.

**Track:** Taskmaster.

## Technologies (paste)
- Gemini 3.6 Flash (Generative Language API) — planning, scoring rationale, personalised drafts
- Google Agent Development Kit (ADK) 2.8 — agent orchestration + tool calling
- FastAPI + Uvicorn on Cloud Run — web UI + async job API
- httpx — website verification probes
- OpenStreetMap Overpass API — business discovery (no key required)

## Other data sources
OpenStreetMap (Overpass) for business names/websites/phones; live HTTP probes of
each business's own website for health signals.

## Findings & learnings (paste)
- Search engines bot-block headless agents (DuckDuckGo/Bing/Brave/SearXNG all
  returned challenges). OpenStreetMap Overpass is the reliable, key-free
  alternative — and businesses *missing* a website are themselves the hottest leads.
- In Pune, ~70% of salons/gyms on OSM have no website at all — a clearer pain
  signal than any broken site.
- ADK gotcha: InMemoryRunner must be constructed with app_name, and the session
  id must come from the create_session return value.
- Gemini model naming moves fast: gemini-2.5-flash is retired for new keys;
  gemini-3.6-flash is current.
- Free-tier Gemini works without a credit card via a Generative Language API key.

## Repo URL
https://github.com/ram1593charan-maker/scout-agent
(If kept private, share with testing@devpost.com and cloudhackathons@google.com)

## Hosted project URL
<the .run URL after Cloud Run deploy>

## Demo video URL
<YouTube unlisted or mp4 link after recording>

## REMINDER — required in the demo video
Must show the backend running on Google Cloud: Cloud Run dashboard / the .run
URL / Google Cloud Console. See docs/DEMO_SCRIPT.md.
