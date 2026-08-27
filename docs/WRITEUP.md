# ScoutAgent — Submission Write-up
*All Things Agentic Hackathon · Taskmaster track*

## Problem
Finding verified local-business leads with real "pain signals" takes hours of
manual browsing. Sales teams and agencies burn time on research instead of
selling. Most AI today waits for you to ask — ScoutAgent doesn't.

## Value proposition
Give ScoutAgent **one input** — a niche and a city — and it autonomously plans,
searches, verifies, scores, and writes outreach-ready lead data **in the
background**, while you do something else. That's "autonomous" in practice:
a goal in, a finished, actionable deliverable out.

## Features & functionality
- **Autonomous planning** — decomposes "find me salon leads in Pune" into
  concrete research steps (ADK LlmAgent, Gemini 3.6 Flash).
- **Business discovery** — queries OpenStreetMap Overpass (free, no API key,
  no bot-blocking) with a niche→OSM-tag map and city bounding boxes.
- **Website verification** — probes each site with httpx: live/dead, HTTPS,
  mobile-friendly (viewport), load time, visible contact info.
- **Digital-pain scoring** — heuristic 0–100. No website = 100 (hottest lead);
  dead site +45, no HTTPS +15, not mobile-friendly +20, slow +10, no contact +10.
- **Personalised outreach** — Gemini drafts a <40-word, pain-specific message
  per lead (template fallback keeps it deterministic without an API key).
- **Async delivery** — CSV + scored markdown report; FastAPI web UI to run it
  interactively and download results.

## Technologies used
- **Gemini 3.6 Flash** (Google Generative Language API) — planning, scoring
  rationale, personalised drafts.
- **Google Agent Development Kit (ADK) 2.8** — agent orchestration + tool calling.
- **FastAPI + Uvicorn** — web UI + async job API.
- **httpx** — website verification probes.
- **OpenStreetMap Overpass API** — business discovery (no key required).
- **Docker / Cloud Run** — deployment target.

## Other data sources used
- OpenStreetMap (Overpass) for business names, websites, phone numbers.
- Live HTTP probes of each business's own website for health signals.

## Findings & learnings
- **Search engines bot-block headless agents.** DuckDuckGo, Bing, Brave and
  SearXNG all returned challenges/429s. OpenStreetMap Overpass is the reliable,
  key-free alternative for local-business discovery — and businesses *missing*
  from it (or missing a website tag) are themselves the hottest leads.
- **The "no website" segment is the real gold.** In Pune, ~70% of salons/gyms
  on OSM have no website at all — a clearer pain signal than any broken site.
- **ADK session handling gotcha:** `InMemoryRunner` must be constructed with
  `app_name`, and the session id must come from the `create_session` return —
  passing a hand-made id raises `SessionNotFoundError`.
- **Gemini model naming moves fast:** `gemini-2.5-flash` is retired for new
  API keys; `gemini-3.6-flash` is current.
- **Free-tier Gemini works without billing.** A Generative Language API key
  (created via `gcloud alpha services api-keys create`) needs no credit card —
  unlike Vertex AI, which requires billing enabled.

## Reproducibility
See `README.md` → Quickstart. The whole pipeline runs with just a
`GEMINI_API_KEY`; the deterministic path (search→verify→score→draft) runs with
no key at all.
