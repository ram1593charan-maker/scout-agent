"""Gradio UI for ScoutAgent — deployable to HuggingFace Spaces."""
import gradio as gr
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from scout_agent.tools import run_pipeline

def sync_scout(niche: str, city: str, limit: int = 10):
    """Sync wrapper for gradio."""
    try:
        result = run_pipeline(niche.strip(), city.strip(), limit)
        if not result:
            return "No leads found. Try a different niche/city."
        lines = []
        for i, lead in enumerate(result, 1):
            name = lead.get('name', '?')
            url = lead.get('url') or '(no website)'
            phone = lead.get('phone') or '—'
            score = lead.get('pain_score', 0)
            reasons = lead.get('pain_reasons', '—')
            draft = lead.get('outreach_draft', '—')
            lines.append(
                f"**{i}. {name}**\n"
                f"   URL: {url} | Phone: {phone}\n"
                f"   Pain Score: {score}/100 — {reasons}\n"
                f"   Outreach: {draft}\n"
            )
        return "\n---\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

demo = gr.Interface(
    fn=sync_scout,
    inputs=[
        gr.Textbox(label="Niche (e.g. salon, dentist, gym)", value="salon"),
        gr.Textbox(label="City (e.g. Pune, Mumbai)", value="Pune"),
        gr.Slider(3, 20, value=10, step=1, label="Number of leads"),
    ],
    outputs=gr.Markdown(label="Lead Research Results"),
    title="🕵️ ScoutAgent — Local Business Lead Research",
    description=(
        "Autonomous lead research for local businesses. "
        "Searches, verifies websites, scores digital pain, and drafts outreach — live."
    ),
    examples=[
        ["salon", "Pune", 10],
        ["dentist", "Pune", 10],
        ["gym", "Mumbai", 10],
        ["clinic", "Bangalore", 10],
    ],
    article=(
        "<p>Built for the WebMCP Challenge + All Things Agentic Hackathon 2026. "
        "Powered by Gemini + OpenStreetMap + httpx.</p>"
    ),
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
