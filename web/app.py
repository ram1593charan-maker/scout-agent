"""FastAPI web UI + async job API for ScoutAgent."""
from __future__ import annotations

import asyncio
import csv
import io
import uuid
from typing import Any

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse

from scout_agent.tools import run_pipeline

app = FastAPI(title="ScoutAgent", version="0.1.0")

JOBS: dict[str, dict[str, Any]] = {}

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
</style></head><body>
<h1>🕵️ ScoutAgent</h1>
<p>Autonomous local-business lead research. Give it a niche + city; it searches,
verifies, scores, and drafts outreach — in the background.</p>
<input id="niche" placeholder="niche (e.g. salons)"> <input id="city" placeholder="city (e.g. Pune)">
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
     +'<small>'+l.url+'</small><br><small>'+ (l.pain_reasons||'') +'</small></div>').join('');
}
</script></body></html>"""


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
