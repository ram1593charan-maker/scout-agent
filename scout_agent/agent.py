"""ADK agent definition for ScoutAgent.

The agent orchestrates the deterministic tools with Gemini-powered planning
and personalised outreach drafting. Runs on Gemini 3.5 Flash via google-adk.
"""
from __future__ import annotations

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from . import tools

INSTRUCTION = """You are ScoutAgent, an autonomous lead-research agent for local businesses.

When the user gives you a NICHE and a CITY (e.g. "salons in Pune"):
1. Call search_businesses(niche, city) to discover candidate businesses.
2. For each result, call verify_website(url) to probe the site.
3. Call score_lead(probe) on each probe to rate digital pain 0-100.
4. Call draft_outreach(...) for the top leads, then improve each draft in your
   own words: keep it under 40 words, specific to the pain found, warm, no hype.
5. Finish with a compact report: total found, how many verified, top 5 leads
   by pain score with one-line reasons, and the full outreach drafts.

Rules:
- Always use the tools; never invent businesses, URLs, or scores.
- If a tool returns an error, report it honestly and continue with what worked.
- Be concise. Output the final report as clean markdown.
"""

root_agent = Agent(
    name="scout_agent",
    model="gemini-3.5-flash",
    description="Autonomous local-business lead research agent",
    instruction=INSTRUCTION,
    tools=[
        tools.search_businesses,
        tools.verify_website,
        tools.score_lead,
        tools.draft_outreach,
    ],
)


def make_runner() -> InMemoryRunner:
    return InMemoryRunner(agent=root_agent)
