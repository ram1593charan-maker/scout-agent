"""CLI entry point.

Two modes:
  python -m scout_agent.cli "salons" "Pune"            # deterministic pipeline (no API key)
  python -m scout_agent.cli "salons" "Pune" --agent    # full ADK agent (needs GEMINI_API_KEY)
"""
from __future__ import annotations

import asyncio
import csv
import json
import sys
from pathlib import Path

from .tools import run_pipeline


def write_csv(leads: list[dict], path: Path) -> None:
    if not leads:
        return
    keys = ["name", "url", "phone", "live", "status", "load_ms", "mobile_friendly",
            "has_ssl", "has_contact", "pain_score", "pain_reasons", "outreach_draft"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for row in leads:
            w.writerow(row)


async def run_agent_mode(niche: str, city: str) -> None:
    from google.genai import types
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    from .agent import make_runner

    runner = make_runner()
    user_id = "cli"
    sess = await runner.session_service.create_session(
        app_name="scout_agent", user_id=user_id)
    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Research leads: niche={niche!r}, city={city!r}. "
                               f"Find 10, verify, score, and draft outreach.")])
    async for event in runner.run_async(user_id=user_id, session_id=sess.id,
                                        new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    print(p.text)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    niche, city = args[0], args[1]

    if "--agent" in flags:
        asyncio.run(run_agent_mode(niche, city))
        return

    print(f"Scouting {niche!r} in {city!r} ...")
    leads = run_pipeline(niche, city, limit=10)
    out = Path("leads.csv")
    write_csv(leads, out)
    print(f"\nFound {len(leads)} candidates -> {out.resolve()}\n")
    for i, l in enumerate(leads[:5], 1):
        if "error" in l:
            print(f"{i}. ERROR: {l['error']}")
            continue
        print(f"{i}. [{l.get('pain_score', 0):>3}] {l.get('name', '?')[:60]}")
        print(f"     {l.get('url', '')}  |  {l.get('pain_reasons', '')}")
    print("\nFull data:", json.dumps({"count": len(leads)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
