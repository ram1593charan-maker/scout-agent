"""ScoutAgent tools: search, verify, score, draft.

Each tool is a plain function the ADK agent can call. Tools are deliberately
deterministic and side-effect-free so the agent's behaviour is reproducible.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any

import httpx

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0 Safari/537.36")
TIMEOUT = 12.0


# ---------------------------------------------------------------- search ----
# Niche -> OSM tag mapping for Overpass. Businesses WITHOUT a website are
# themselves the hottest leads (pain: no online presence at all).
NICHE_TAGS: dict[str, list[tuple[str, str]]] = {
    "salon": [("shop", "hairdresser"), ("shop", "beauty")],
    "salons": [("shop", "hairdresser"), ("shop", "beauty")],
    "spa": [("shop", "beauty"), ("leisure", "spa")],
    "restaurant": [("amenity", "restaurant")],
    "restaurants": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "clinic": [("amenity", "clinic"), ("amenity", "doctors")],
    "dentist": [("amenity", "dentist")],
    "gym": [("leisure", "fitness_centre")],
    "gyms": [("leisure", "fitness_centre")],
    "pharmacy": [("amenity", "pharmacy")],
    "bakery": [("shop", "bakery")],
    "boutique": [("shop", "clothes")],
    "hotel": [("tourism", "hotel")],
    "tutor": [("amenity", "tutoring_centre")],
    "coaching": [("amenity", "tutoring_centre")],
}

# Rough city bounding boxes (south, west, north, east). Extend as needed.
CITY_BBOX: dict[str, tuple[float, float, float, float]] = {
    "pune": (18.45, 73.78, 18.58, 73.92),
    "mumbai": (18.90, 72.80, 19.10, 72.90),
    "bangalore": (12.90, 77.55, 13.05, 77.70),
    "bengaluru": (12.90, 77.55, 13.05, 77.70),
    "delhi": (28.55, 77.10, 28.70, 77.30),
    "hyderabad": (17.35, 78.40, 17.50, 78.55),
}

OVERPASS_UA = "ScoutAgent/0.1 (hackathon project; contact 20hshant@gmail.com)"


def search_businesses(niche: str, city: str, limit: int = 10) -> list[dict[str, str]]:
    """Discover candidate businesses for a niche+city via OpenStreetMap Overpass.

    Free, no API key, no bot-blocking. Returns {name, url, phone, source}.
    Businesses without a website get url="" — they are valid (hot) leads.
    """
    key = niche.lower().strip()
    tags = NICHE_TAGS.get(key)
    if not tags:
        # generic fallback: try shop=<niche>
        tags = [("shop", key.rstrip("s"))]
    ck = city.lower().strip()
    bbox = CITY_BBOX.get(ck)
    if not bbox:
        return [{"error": f"city '{city}' not in bbox map yet — add it to CITY_BBOX"}]
    s, w, n, e = bbox
    parts = "\n".join(f'  node["{k}"="{v}"]({s},{w},{n},{e});' for k, v in tags)
    q = f"[out:json][timeout:25];\n(\n{parts}\n);\nout center {max(limit*4, 40)};"
    results: list[dict[str, str]] = []
    try:
        with httpx.Client(timeout=40, headers={"User-Agent": OVERPASS_UA}) as c:
            r = c.post("https://overpass-api.de/api/interpreter", data={"data": q})
            r.raise_for_status()
            els = r.json().get("elements", [])
        for el in els:
            t = el.get("tags", {})
            name = t.get("name", "").strip()
            if not name:
                continue
            results.append({
                "name": name,
                "url": t.get("website", "") or t.get("contact:website", ""),
                "phone": t.get("phone", "") or t.get("contact:phone", ""),
                "source": "openstreetmap",
            })
            if len(results) >= limit:
                break
    except Exception as e:  # noqa: BLE001 — tool must never crash the agent
        return [{"error": f"search failed: {e}"}]
    return results


# ---------------------------------------------------------------- verify ----
@dataclass
class SiteProbe:
    url: str
    live: bool = False
    status: int | None = None
    load_ms: int | None = None
    mobile_friendly: bool = False
    has_contact: bool = False
    has_ssl: bool = False
    title: str = ""
    error: str = ""


def verify_website(url: str) -> dict[str, Any]:
    """Probe a website and extract signals used for pain scoring."""
    probe = SiteProbe(url=url)
    try:
        with httpx.Client(headers={"User-Agent": UA}, timeout=TIMEOUT,
                          follow_redirects=True) as c:
            t0 = time.monotonic()
            r = c.get(url)
            probe.load_ms = int((time.monotonic() - t0) * 1000)
            probe.status = r.status_code
            probe.live = r.status_code < 400
            probe.has_ssl = url.startswith("https")
            html = r.text[:200_000].lower()
            probe.mobile_friendly = 'name="viewport"' in html
            probe.has_contact = any(k in html for k in
                                    ("tel:", "mailto:", "phone", "contact", "whatsapp"))
            tm = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
            probe.title = re.sub(r"\s+", " ", tm.group(1)).strip()[:80] if tm else ""
    except Exception as e:  # noqa: BLE001
        probe.error = str(e)[:120]
    return asdict(probe)


# ----------------------------------------------------------------- score ----
def score_lead(probe: dict[str, Any]) -> dict[str, Any]:
    """Heuristic 'digital pain' score 0-100. Higher = better prospect.

    Signals (weights):
      dead/unreachable site      +45
      no SSL                     +15
      not mobile-friendly        +20
      slow (>3s)                 +10
      no visible contact info    +10
    """
    score = 0
    reasons: list[str] = []
    if not probe.get("live"):
        score += 45
        reasons.append("site unreachable or erroring")
    if probe.get("live") and not probe.get("has_ssl"):
        score += 15
        reasons.append("no HTTPS")
    if probe.get("live") and not probe.get("mobile_friendly"):
        score += 20
        reasons.append("not mobile-friendly")
    if probe.get("live") and (probe.get("load_ms") or 0) > 3000:
        score += 10
        reasons.append(f"slow load ({probe.get('load_ms')}ms)")
    if probe.get("live") and not probe.get("has_contact"):
        score += 10
        reasons.append("no visible contact info")
    score = min(score, 100)
    return {"score": score, "reasons": reasons}


# ----------------------------------------------------------------- draft ----
def draft_outreach(name: str, url: str, score_info: dict[str, Any],
                   niche: str, city: str) -> str:
    """Template outreach draft. Gemini refines tone in the agent layer;
    this keeps a deterministic fallback that never needs an API key."""
    reasons = score_info.get("reasons", [])
    hook = reasons[0] if reasons else "your online presence"
    if not url or url == "(no website)":
        return (
            f"Hi {name or 'there'}, I was researching {niche} in {city} and "
            f"couldn't find a website for your business — most customers now "
            f"search on their phones first. I build affordable sites for local "
            f"businesses exactly like yours. Worth a 2-minute chat?"
        )
    return (
        f"Hi {name or 'there'}, I came across {url} while researching {niche} "
        f"in {city}. I noticed {hook} — that's usually costing you customers "
        f"who search on their phones. I build quick fixes for exactly this. "
        f"Worth a 2-minute look?"
    )


# ------------------------------------------------------------- pipeline ----
def run_pipeline(niche: str, city: str, limit: int = 10) -> list[dict[str, Any]]:
    """Full deterministic pipeline: search -> verify -> score -> draft.

    Used by the CLI and as the agent's 'heavy lifting' path. The ADK agent
    wraps this and adds Gemini-powered planning + personalised drafts.
    """
    leads: list[dict[str, Any]] = []
    found = search_businesses(niche, city, limit)
    for f in found:
        if "error" in f:
            leads.append(f)
            continue
        url = f.get("url", "")
        if not url:
            # No website at all = maximum pain, hottest lead
            sc = {"score": 100, "reasons": ["no website at all"]}
            draft = draft_outreach(f["name"], "(no website)", sc, niche, city)
            leads.append({
                "name": f["name"],
                "url": "",
                "phone": f.get("phone", ""),
                "live": False,
                "pain_score": 100,
                "pain_reasons": "no website at all",
                "outreach_draft": draft,
            })
            continue
        probe = verify_website(url)
        sc = score_lead(probe)
        draft = draft_outreach(f["name"], url, sc, niche, city)
        leads.append({
            "name": f["name"],
            "url": url,
            "phone": f.get("phone", ""),
            **probe,
            "pain_score": sc["score"],
            "pain_reasons": "; ".join(sc["reasons"]),
            "outreach_draft": draft,
        })
    leads.sort(key=lambda l: l.get("pain_score", 0), reverse=True)
    return leads
