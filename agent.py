"""Deep Research Agent: multi-step web research via DuckDuckGo, structured report output."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

load_dotenv()

# Model from env or default to gpt-5-mini
MODEL_NAME = os.getenv("OPENAI_MODEL", "openai:gpt-5-mini")


# --- Report schema (structured output) ---


class EvidenceCitation(BaseModel):
    """A single cited fact with source."""

    claim: str = Field(description="The factual claim or number being cited.")
    source_title: str = Field(description="Title of the source (e.g. article or page title).")
    url: str = Field(description="URL of the source.")


class ReportSection(BaseModel):
    """One section of the report (one research angle)."""

    title: str = Field(description="Section title, e.g. 'SWOT analysis', 'Last 12 months performance'.")
    key_findings: list[str] = Field(
        default_factory=list,
        description="Bullet-point key findings for this section.",
    )
    evidence: list[EvidenceCitation] = Field(
        default_factory=list,
        description="Evidence bullets with claim, source title, and URL. Every key fact must have a citation.",
    )


class DeepResearchReport(BaseModel):
    """Structured deep research report with citations."""

    executive_summary: str = Field(
        description="Brief executive summary (2–4 sentences) of the overall findings."
    )
    sections: list[ReportSection] = Field(
        default_factory=list,
        description="One section per research angle, each with key findings and evidence with citations.",
    )
    risks_uncertainties: list[str] = Field(
        default_factory=list,
        description="Risks, uncertainties, conflicting information, or data limitations.",
    )
    what_to_watch_next: list[str] = Field(
        default_factory=list,
        description="Concrete items to monitor or follow up on (e.g. next earnings, regulatory decision).",
    )


# --- Agent ---

DEEP_RESEARCH_INSTRUCTIONS = """
You are a Deep Research Agent. You produce a single, detailed, well-sourced report from web research using DuckDuckGo.

## 1. Intent and entity detection
- If the user input looks like a stock ticker (1–5 uppercase letters, possibly with "stock" or similar), treat it as a ticker.
  - First, run a DuckDuckGo search to resolve the ticker to company name and context (e.g. NVDA → NVIDIA, semiconductors, GPUs, AI).
  - Use that resolved context for all later steps.
- Otherwise, treat the input as a free-text research query and use it as-is.

## 2. Initial discovery search
- Run exactly one DuckDuckGo search with the (resolved) query or topic.
- From the top results and snippets, identify 3–4 non-overlapping research angles (keywords/themes).
- For a stock: typical angles include SWOT analysis, last 12 months stock performance, competition and market positioning, latest quarterly results and forward guidance.
- For a general topic: choose angles that cover different aspects (e.g. overview, recent news, risks, outlook).

## 3. Deep dives (one search per angle)
- For each research angle, run a separate DuckDuckGo search with a focused query.
- Use only the returned results: title, href (URL), and body (snippet). Do not invent URLs or sources.
- Prefer primary sources for financials: earnings releases, SEC/filings, investor relations.
- Prefer reputable outlets for news when multiple options exist.
- Extract key facts, numbers, and claims. Track which source (title + URL) supports which claim.

## 4. Synthesis
- Produce exactly one structured report (the required output format) with:
  - **Executive summary**: 2–4 sentences summarizing the main findings.
  - **Sections**: One section per research angle. Each section has a title, key_findings (bullets), and evidence (list of claim + source_title + url). Every factual claim must appear in evidence with a real source URL and title.
  - **Risks/uncertainties**: List any conflicting information, caveats, or data limitations.
  - **What to watch next**: Concrete follow-up items (e.g. next earnings date, key catalyst).
- Do not invent sources or URLs. Only cite results you actually received from the search tool.
"""

agent = Agent(
    MODEL_NAME,
    tools=[duckduckgo_search_tool()],
    output_type=DeepResearchReport,
    instructions=DEEP_RESEARCH_INSTRUCTIONS,
    model_settings=ModelSettings(max_tokens=4096),
)
