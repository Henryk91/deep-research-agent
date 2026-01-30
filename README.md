# Deep Research Agent

A **Deep Research Agent** that takes either a free-text query or a stock ticker (e.g. NVDA), runs multi-step web research using [DuckDuckGo](https://duckduckgo.com), and returns a structured, cited report. Built with [Pydantic AI](https://ai.pydantic.dev) and [Gradio](https://gradio.app).

## What it does

- **Intent & entity detection** — Detects whether the input is a stock ticker or a general query. For tickers, it resolves to company name and context (e.g. NVDA → NVIDIA, semiconductors, GPUs, AI).
- **Discovery** — Runs one DuckDuckGo search and derives 3–4 non-overlapping research angles (e.g. SWOT, 12-month performance, competition, quarterly results).
- **Deep dives** — For each angle, runs a separate search, collects sources (title, URL, snippet), and extracts key facts with source attribution. Prefers primary sources for financials (earnings, filings, investor relations) and reputable outlets for news.
- **Synthesis** — Produces a single report with:
  - Executive summary  
  - Key findings per section  
  - Evidence bullets with citations (source title + URL)  
  - Risks / uncertainties and conflicting info  
  - “What to watch next” list  

Research can take **30–60+ seconds** per query because of multiple searches.

## Requirements

- Python 3.10+
- [OpenAI API key](https://platform.openai.com/api-keys) (the agent uses gpt-5-mini by default)

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example env file and add your OpenAI key:

```bash
cp .env.example .env
```

Edit `.env` and set:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

Do not commit `.env`; it is for secrets.

### 4. Run the app

```bash
python app.py
```

Gradio will print a local URL (e.g. `http://127.0.0.1:7860`). Open it in your browser, enter a query or ticker, and wait for the report.

## Project layout

| File / folder     | Purpose |
|-------------------|---------|
| `agent.py`        | Pydantic AI Deep Research agent: report schema, DuckDuckGo tool, instructions. |
| `app.py`          | Gradio chat UI; calls the agent and renders the report as markdown. |
| `requirements.txt`| Python dependencies (pydantic-ai, openai, ddgs, gradio, python-dotenv). |
| `.env.example`    | Template for `.env` (copy to `.env` and set `OPENAI_API_KEY`). |
| `docs.md`         | Pydantic AI documentation (reference). |
| `README.md`       | This file. |

## Report structure

Each run returns a structured report (Pydantic model) that the UI converts to markdown:

- **Executive summary** — Short overview of findings.
- **Sections** — One per research angle: title, key findings, evidence (claim + source title + URL).
- **Risks and uncertainties** — Caveats, conflicts, data limitations.
- **What to watch next** — Follow-up items (e.g. next earnings, catalysts).

## Optional

- **Change model** — Set `OPENAI_MODEL` in `.env`, e.g. `OPENAI_MODEL=openai:gpt-4o-mini`.
- **Share the app** — In `app.py`, use `demo.launch(share=True)` to get a public Gradio link.
