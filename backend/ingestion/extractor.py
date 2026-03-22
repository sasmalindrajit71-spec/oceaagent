"""
OCEAN Ingestion Layer — Graph RAG extraction pipeline.
Accepts text/URL/PDF, runs multi-pass extraction, produces a validated knowledge graph.
"""

import re
import json
import uuid
import httpx
from typing import Optional
from llm import router


EXTRACTION_SYSTEM = """You are a knowledge graph extraction specialist. 
Extract structured information from text and return ONLY valid JSON — no preamble, no markdown fences.

Return this exact structure:
{
  "entities": [
    {"id": "e1", "label": "Entity Name", "type": "person|organization|location|concept|event|policy", "description": "brief description"}
  ],
  "relationships": [
    {"source": "e1", "target": "e2", "label": "relationship type", "sentiment": -1.0}
  ],
  "narrative_tensions": [
    {"description": "tension description", "entities_involved": ["e1", "e2"], "intensity": 0.8}
  ],
  "core_topics": ["topic1", "topic2"],
  "overall_sentiment": 0.0,
  "key_claims": ["claim1", "claim2"]
}

sentiment values: -1.0 (very negative) to 1.0 (very positive)
intensity values: 0.0 to 1.0"""


VALIDATION_SYSTEM = """You are a knowledge graph validator.
Review and reconcile two knowledge graph extractions of the same text.
Merge them, remove duplicates, resolve conflicts, and return a single clean graph.
Return ONLY valid JSON with the same structure."""


async def extract_from_text(text: str) -> dict:
    """Run multi-pass Graph RAG extraction on text."""

    # Pass 1 — full document extraction
    pass1_response = await router.complete(
        role="graph_rag",
        messages=[{"role": "user", "content": f"Extract knowledge graph from this text:\n\n{text[:8000]}"}],
        system=EXTRACTION_SYSTEM,
        max_tokens=2048,
        temperature=0.3,
    )

    pass1 = _safe_parse_json(pass1_response)

    # Pass 2 — chunked extraction (first half)
    mid = len(text) // 2
    pass2_response = await router.complete(
        role="graph_rag",
        messages=[{"role": "user", "content": f"Extract knowledge graph from this text excerpt:\n\n{text[:mid]}"}],
        system=EXTRACTION_SYSTEM,
        max_tokens=2048,
        temperature=0.3,
    )
    pass2 = _safe_parse_json(pass2_response)

    # Reconciliation pass
    reconcile_prompt = f"""Reconcile these two knowledge graph extractions:

EXTRACTION 1:
{json.dumps(pass1, indent=2)}

EXTRACTION 2:
{json.dumps(pass2, indent=2)}

Merge into one comprehensive, deduplicated graph."""

    final_response = await router.complete(
        role="graph_rag",
        messages=[{"role": "user", "content": reconcile_prompt}],
        system=VALIDATION_SYSTEM,
        max_tokens=3000,
        temperature=0.2,
    )

    final_graph = _safe_parse_json(final_response)

    # Ensure all entities have IDs
    for i, entity in enumerate(final_graph.get("entities", [])):
        if not entity.get("id"):
            entity["id"] = f"e{i+1}"

    return final_graph


async def extract_from_url(url: str) -> tuple[str, dict]:
    """Fetch URL content and extract knowledge graph."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "OCEAN-Simulation/1.0"})
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        html = resp.text

    # Basic HTML stripping
    text = _strip_html(html)
    graph = await extract_from_text(text)
    return text, graph


async def extract_from_pdf(pdf_bytes: bytes) -> tuple[str, dict]:
    """Extract text from PDF and run knowledge graph extraction."""
    try:
        import pypdf
        import io
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")

    graph = await extract_from_text(text)
    return text, graph


def _strip_html(html: str) -> str:
    """Basic HTML → plain text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)[:12000]


def _safe_parse_json(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {
        "entities": [],
        "relationships": [],
        "narrative_tensions": [],
        "core_topics": [],
        "overall_sentiment": 0.0,
        "key_claims": [],
    }
