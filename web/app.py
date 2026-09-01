"""FastAPI web UI + async job API for ScoutAgent — WebMCP-enabled."""
from __future__ import annotations

import asyncio
import csv
import io
import json
import uuid
from typing import Any

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from scout_agent.tools import run_pipeline

app = FastAPI(title="ScoutAgent", version="0.2.0")

JOBS: dict[str, dict[str, Any]] = {}

# --- WebMCP Tool Definitions ---
WEBMCP_TOOLS = [
    {
        "name": "scout_leads",
        "description": (
            "Find local businesses in a niche and city, verify their websites, "
            "score their online pain (0-100), and generate a personalized outreach "
            "draft for each lead. Returns JSON with scored leads and outreach drafts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "niche": {
                    "type": "string",
                    "description": "Business niche, e.g. 'salon', 'dentist', 'gym', 'cafe'"
                },
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Pune', 'Mumbai', 'Bangalore'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of leads to return (3-20)",
                    "default": 10,
                    "minimum": 3,
                    "maximum": 20
                }
            },
            "required": ["niche", "city"]
        }
    },
    {
        "name": "scout_csv",
        "description": (
            "Same as scout_leads but returns the results as a CSV string. "
            "Useful for downloading leads into a spreadsheet or CRM."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "niche": {"type": "string"},
                "city": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["niche", "city"]
        }
    },
    {
        "name": "list_cities",
        "description": "List the cities currently supported by ScoutAgent (bounding box map).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "list_niches",
        "description": "List the niches currently supported by ScoutAgent.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

# --- WebMCP HTML client with navigator.modelContext polyfill ---
INDEX = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScoutAgent</title>
<style>
 body{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:2rem;max-width:760px;margin:auto}
 h1{color:#58a6ff} input,button{padding:.6rem .8rem;font-size:1rem;border-radius:8px;border:1px solid #30363d}
 input{background:#161b22;color:#e6edf3;width:45%} button{background:#238636;color:#fff;border:none;cursor:pointer}
 #out{margin-top:1.5rem;white-space:pre-wrap;background:#161b22;padding:1rem;border-radius:8px;min-height:120px}
 .lead{border-bottom:1px solid #21262d;padding:.5rem 0}
 .score{color:#f0883e;font-weight:700}
 .badge{background:#1f6feb;color:#fff;font-size:.7rem;padding:.1rem .4rem;border-radius:4px;margin-left:.5rem}
</style>
<script src="https://unpkg.com/@mcp-b/global@latest/dist/index.min.js"></script>
<script>
window.navigator.modelContext = window.navigator.modelContext || {};
if (window.navigator.modelContext.registerTool) {
  // Native WebMCP available
  window.navigator.modelContext.registerTool({
    name: 'scout_leads',
    description: 'Find local businesses in a niche and city, verify their websites, score pain, and draft outreach.',
    inputSchema: { type:'object', properties:{ niche:{type:'string'}, city:{type:'string'}, limit:{type:'integer',default:10} }, required:['niche','city'] },
    execute: async ({niche, city, limit=10}) => {
      const r = await fetch('/api/scout?niche='+encodeURIComponent(niche)+'&city='+encodeURIComponent(city)+'&limit='+limit);
      return await r.json();
    }
  });
  document.title = '🕵️ ScoutAgent — WebMCP Native';
} else {
  document.title = '🕵️ ScoutAgent';
}
</script>
</head><body>
<h1>🕵️ ScoutAgent <span class="badge">WebMCP-enabled</span></h1>
<p>Autonomous local-business lead research. Give it a niche + city; it searches,
verifies, scores, and drafts outreach — in the background. WebMCP-aware agents
can call <code>scout_leads()</code> directly from this page.</p>
<input id="niche" placeholder="niche (e.g. salons)" value="salon">
<input id="city" placeholder="city (e.g. Pune)" value="Pune">
<button onclick="go()">Scout</button>
<div id="out">Results appear here…</div>
<script>
async function go(){
 const n=document.getElementById('niche').value, c=document.getElementById('city').value;
 const out=document.getElementById('out'); out.textContent='Scouting…';
 const r=await fetch('/api/scout?niche='+encodeURIComponent(n)+'&city='+encodeURIComponent(c));
 const d=await r.json();
 out.innerHTML=d.leads.map(l=>l.error
   ? '<div class="lead">⚠️ '+l.error+'</div>'
   : '<div class="lead"><span class="score">['+l.pain_score+']</span> <b>'+(l.name||'?')+'</b><br>'
     +'<small>'+l.url+'</small><br><small>'+ (l.pain_reasons||'') +'</small><br><em>'+(l.outreach_draft||'')+'</em></div>').join('');
}
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX


@app.get("/api/scout")
async def scout(niche: str, city: str, limit: int = 10) -> dict[str, Any]:
    leads = await asyncio.to_thread(run_pipeline, niche, city, limit)
    return {"niche": niche, "city": city, "count": len(leads), "leads": leads}


@app.get("/api/scout.csv")
async def scout_csv(niche: str, city: str, limit: int = 10) -> StreamingResponse:
    leads = await asyncio.to_thread(run_pipeline, niche, city, limit)
    buf = io.StringIO()
    if leads:
        keys = ["name", "url", "phone", "live", "status", "load_ms", "mobile_friendly",
                "has_ssl", "has_contact", "pain_score", "pain_reasons", "outreach_draft"]
        w = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for row in leads:
            w.writerow(row)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scout_{niche}_{city}.csv"})


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


# --- WebMCP standard endpoints (declarative + imperative tool discovery) ---
@app.get("/.well-known/webmcp.json")
async def webmcp_manifest() -> JSONResponse:
    """WebMCP manifest endpoint — declares available tools for AI agents."""
    return JSONResponse({
        "name": "ScoutAgent",
        "description": (
            "Autonomous local-business lead research agent. Searches "
            "OpenStreetMap, verifies websites, scores digital pain 0-100, "
            "and drafts personalized outreach per lead."
        ),
        "version": "0.2.0",
        "tools": WEBMCP_TOOLS,
        "endpoint": "https://webmcp.devpost.com/submissions/new"
    })


@app.get("/api/webmcp/tools")
async def webmcp_tools() -> JSONResponse:
    """List tools in the format WebMCP-aware agents expect."""
    return JSONResponse({"tools": WEBMCP_TOOLS})


@app.post("/api/webmcp/execute")
async def webmcp_execute(request: Request) -> JSONResponse:
    """Execute a WebMCP-registered tool from an agent's call."""
    payload = await request.json()
    name = payload.get("name")
    args = payload.get("arguments", {})
    if name == "scout_leads" or name == "scout_csv":
        niche = args.get("niche")
        city = args.get("city")
        limit = int(args.get("limit", 10))
        leads = await asyncio.to_thread(run_pipeline, niche, city, limit)
        if name == "scout_csv":
            buf = io.StringIO()
            if leads:
                keys = ["name", "url", "phone", "live", "pain_score", "pain_reasons", "outreach_draft"]
                w = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                for row in leads:
                    w.writerow(row)
            return JSONResponse({"csv": buf.getvalue()})
        return JSONResponse({"leads": leads, "count": len(leads)})
    if name == "list_cities":
        from scout_agent.tools import CITY_BBOX
        return JSONResponse({"cities": list(CITY_BBOX.keys())})
    if name == "list_niches":
        from scout_agent.tools import NICHE_TAGS
        return JSONResponse({"niches": list(NICHE_TAGS.keys())})
    return JSONResponse({"error": f"unknown tool: {name}"}, status_code=400)
