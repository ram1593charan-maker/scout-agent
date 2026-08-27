# DEMO VIDEO SCRIPT (~4 min) — ScoutAgent
Record AFTER Cloud Run deploy (morning). Use a screen recorder (e.g. `wf-recorder`
or OBS). Keep it tight; show it WORKING live.

## 0:00–0:20 — The problem
"I run a business building websites for local shops. The hardest part isn't
building — it's finding which businesses actually NEED a website. That research
takes hours. So I built an agent that does it for me, in the background."

## 0:20–0:50 — One input, autonomous work
- Open the web UI (the .run URL).
- Type niche = "salons", city = "Pune", click Scout.
- NARRATE: "I give it one goal. It plans the research, searches OpenStreetMap,
  visits every website, checks if it's mobile-friendly, scores the pain, and
  writes outreach — all on its own."

## 0:50–1:40 — Watch it work (the money shot)
- Show the results populating: scored leads, pain reasons, outreach drafts.
- Point at a "100 — no website at all" lead: "This salon has no website. That's
  the hottest possible lead, and the agent flagged it automatically."
- Point at a broken-site lead: "This one's site is down — the agent caught that too."

## 1:40–2:20 — The agent brain (Gemini + ADK)
- Switch to terminal, run: `python -m scout_agent.cli "gyms" "Pune" --agent`
- Show Gemini's markdown report streaming out with personalised drafts.
- NARRATE: "This is Gemini 3.6 Flash orchestrating four tools through Google's
  Agent Development Kit — search, verify, score, draft."

## 2:20–3:00 — REQUIRED: prove it's on Google Cloud
- Open Google Cloud Console → Cloud Run dashboard.
- Show the `scout-agent` service, the `.run` URL, region asia-south1.
- (This segment is mandatory per the rules — do not skip.)

## 3:00–3:40 — Architecture + value
- Show docs/architecture.html.
- "A goal in, a finished, actionable lead list out. That's what autonomous means."

## 3:40–4:00 — Close
"ScoutAgent. Built for the All Things Agentic Hackathon on Gemini and Google Cloud."

## Recording checklist
- [ ] Cloud Run deployed + .run URL working
- [ ] Web UI loads on the .run URL
- [ ] Terminal agent run works (has GEMINI_API_KEY)
- [ ] GCP Console Cloud Run page ready
- [ ] Record → upload (YouTube unlisted or direct mp4) → paste link in Devpost submission
