import asyncio
import httpx
from typing import List, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from ddgs import DDGS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()


# Models
class QueryClassification(BaseModel):
    input_type: Literal["ticker", "general"]
    resolved_name: str = Field(
        description="Resolved company name if ticker, or cleaned query if general"
    )
    context: str = Field(description="Brief context (e.g., semiconductors for NVDA)")


class ResearchAngle(BaseModel):
    angle: str = Field(
        description="The research angle/keyword (e.g., SWOT Analysis, Recent Financial Performance)"
    )
    keywords: List[str] = Field(description="List of keywords to search for this angle")
    description: str = Field(description="Brief description of what to look for")


class ResearchPlan(BaseModel):
    angles: List[ResearchAngle] = Field(max_length=4, min_length=3)


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class ResearchFinding(BaseModel):
    claim: str
    source_title: str
    source_url: str
    evidence: str


class SectionFindings(BaseModel):
    angle: str
    summary: str
    findings: List[ResearchFinding]


class DeepResearchReport(BaseModel):
    title: str
    executive_summary: str
    sections: List[SectionFindings]
    risks_and_uncertainties: str
    watch_list: List[str]


# Tools
def search_duckduckgo(query: str, max_results: int = 5) -> List[SearchResult]:
    """Search DuckDuckGo and return top results."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
        return [
            SearchResult(title=r["title"], url=r["href"], snippet=r["body"])
            for r in results
        ]


async def fetch_page_content(url: str) -> str:
    """Fetch and extract text from a URL."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=" ", strip=True)
                return text[:5000]  # Limit content size
            return ""
    except Exception:
        return ""


# Agents
model_name = os.getenv("MODEL_NAME", "openai:gpt-5-mini")

classifier_agent = Agent(
    model_name,
    output_type=QueryClassification,
    system_prompt=(
        "You are an intent detection expert. "
        "Classify the user input as a 'ticker' or 'general' query. "
        "If it's a ticker, resolve it to the full company name and provide context."
    ),
)

planner_agent = Agent(
    model_name,
    output_type=ResearchPlan,
    system_prompt=(
        "You are a research strategist. "
        "Based on the initial discovery search results, generate 3-4 distinct research angles. "
        "Angles should be relevant and non-overlapping and cover key aspects (SWOT, Financials, Competitors, etc. for stocks; Key trends, History, Pros/Cons for general topics)."
    ),
)

worker_agent = Agent(
    model_name,
    output_type=SectionFindings,
    system_prompt=(
        "You are a senior researcher. Your goal is to investigate a specific research angle deeply. "
        "Use the provided angle and search results to extract key facts, numbers, and claims. "
        "Always cite your sources with title and URL."
        "Synthesize the findings into a concise section with citations. "
        "Prefer primary sources for financials."
    ),
)

writer_agent = Agent(
    model_name,
    output_type=str,
    system_prompt=(
        "You are a professional report writer. "
        "Synthesize all section findings into a final cohesive markdown report. "
        "Includes an Executive Summary, the main Sections, Risks, and What to Watch. "
        "Ensure clear sections, evidence bullets with citations, risks/uncertainties, and a watch list. "
        "For the sources, use the format: [Source Title](Source URL)"
    ),
)


# Orchestration
async def run_research(user_query: str):
    yield f"🔎 Starting research for: {user_query}..."

    # 1. Classify
    classification = (await classifier_agent.run(user_query)).output
    yield f"✅ Type: {classification.input_type}, Resolved: {classification.resolved_name}"

    # 2. Initial Discovery
    discovery_query = f"{classification.resolved_name} {classification.context}"
    discovery_results = search_duckduckgo(discovery_query, max_results=3)
    discovery_context = "\n".join(
        [f"{r.title} ({r.url}): {r.snippet}" for r in discovery_results]
    )

    print("Discovery Results:")
    for r in discovery_results:
        print(f"Discovery: {r.title}")

    # 3. Plan
    yield f"🤔 Generating research plan..."
    plan = (
        await planner_agent.run(
            f"Topic: {classification.resolved_name}\nContext: {discovery_context}"
        )
    ).output

    print(f"Generated {len(plan.angles)} angles.")
    yield f"📋 Plan generated with {len(plan.angles)} research angles."

    # 4. Deep Dive (Parallel)
    tasks = []
    for angle in plan.angles:
        yield f"🕵️ Starting deep dive for: {angle.angle}..."
        tasks.append(run_worker(angle, classification))

    section_results = await asyncio.gather(*tasks)

    print("Research completed. Starting Synthesis...")
    yield "📝 Research completed. Synthesizing final report..."

    # 5. Synthesize
    synthesis_input = f"Topic: {classification.resolved_name}\n\n"
    for section in section_results:
        synthesis_input += f"## Angle: {section.angle}\n{section.summary}\n"
        for f in section.findings:
            synthesis_input += (
                f"- {f.claim} (Source: {f.source_title}, URL: {f.source_url})\n"
            )
        synthesis_input += "\n"

    print("Synthesis complete. Generating final report...")
    final_report = (await writer_agent.run(synthesis_input)).output
    print("Final report generated.")
    yield final_report


async def run_worker(
    angle: ResearchAngle, classification: QueryClassification
) -> SectionFindings:
    print(
        f"  > Starting worker for '{classification.resolved_name}' angle: {angle.angle}"
    )
    # Search for this specific angle
    query = f"{classification.resolved_name} {angle.angle}"
    results = search_duckduckgo(query, max_results=3)

    findings_context = ""
    for r in results:
        content = await fetch_page_content(r.url)
        findings_context += (
            f"Source: {r.title}\nURL: {r.url}\n\nContent:\n{content[:2000]}\n---\n"
        )
    print(f"Found context for {angle.angle} Investigating findings...")
    prompt = f"Topic: {classification.resolved_name}\nAngle: {angle.angle}\nDescription: {angle.description}\n\nSearch Content:\n{findings_context}"
    result = await worker_agent.run(prompt)
    print(f"Completed investigating findings for {angle.angle}")
    return result.output


if __name__ == "__main__":

    async def test():
        report = await run_research("NVDA")
        print("\n=== FINAL REPORT ===\n")
        print(report)

    asyncio.run(test())
