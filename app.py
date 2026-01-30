"""Gradio frontend for the Deep Research Agent."""

import asyncio
import json
import queue
import threading

import gradio as gr

from agent import DeepResearchReport, agent

# Event types for streaming status (avoid hard dependency on internal module path)
try:
    from pydantic_ai import AgentRunResultEvent, FunctionToolCallEvent
except ImportError:
    AgentRunResultEvent = None
    FunctionToolCallEvent = None


def report_to_markdown(report: DeepResearchReport) -> str:
    """Convert structured report to readable markdown for display."""
    lines: list[str] = []

    lines.append("## Executive summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")

    for section in report.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        if section.key_findings:
            lines.append("**Key findings**")
            lines.append("")
            for f in section.key_findings:
                lines.append(f"- {f}")
            lines.append("")
        if section.evidence:
            lines.append("**Evidence**")
            lines.append("")
            for e in section.evidence:
                lines.append(f"- {e.claim}")
                lines.append(f"  — Source: [{e.source_title}]({e.url})")
            lines.append("")

    if report.risks_uncertainties:
        lines.append("## Risks and uncertainties")
        lines.append("")
        for r in report.risks_uncertainties:
            lines.append(f"- {r}")
        lines.append("")

    if report.what_to_watch_next:
        lines.append("## What to watch next")
        lines.append("")
        for w in report.what_to_watch_next:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines).strip()


def _run_agent_with_events(message: str, status_queue: queue.Queue) -> None:
    """Run the agent in an event loop and push status updates to the queue."""
    async def run():
        search_count = 0
        try:
            async for event in agent.run_stream_events(message):
                if FunctionToolCallEvent and isinstance(event, FunctionToolCallEvent):
                    tool_name = getattr(event.part, "tool_name", "") or ""
                    raw_args = getattr(event.part, "args", None)
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except (json.JSONDecodeError, TypeError):
                            args = {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                    if args.get("query"):
                        search_count += 1
                        q = args["query"]
                        if len(q) > 60:
                            q = q[:57] + "..."
                        status_queue.put(f"🔍 Search {search_count}: _{q}_")
                    else:
                        status_queue.put(f"🔧 Calling {tool_name}...")
                if AgentRunResultEvent and isinstance(event, AgentRunResultEvent):
                    status_queue.put((None, event.result))
                    return
        except Exception as e:
            status_queue.put((None, e))

    asyncio.run(run())


def chat(message: str, history):
    """Send user message to the agent; stream status updates, then return the report as markdown."""
    if not message.strip():
        return ""
    if not (AgentRunResultEvent and FunctionToolCallEvent):
        # Fallback: no streaming, just run and return
        result = agent.run_sync(message)
        report = result.output
        if isinstance(report, DeepResearchReport):
            return report_to_markdown(report)
        return str(report)

    status_queue: queue.Queue = queue.Queue()
    status_lines: list[str] = [
        "**Research progress**",
        "",
        "🔍 Starting research (detecting intent, then running discovery search)...",
        "",
    ]
    thread = threading.Thread(target=_run_agent_with_events, args=(message, status_queue))
    thread.start()

    def build_status() -> str:
        return "\n".join(status_lines)

    yield build_status()

    final_result = None
    while True:
        try:
            item = status_queue.get(timeout=2)
        except queue.Empty:
            # Re-yield current status so Gradio knows we're still running
            yield build_status()
            continue
        if isinstance(item, tuple) and item[0] is None:
            final_result = item[1]
            break
        status_lines.append(item)
        status_lines.append("")
        yield build_status()

    thread.join()

    if isinstance(final_result, Exception):
        yield build_status() + "\n\n**Error:** " + str(final_result)
        return
    if not hasattr(final_result, "output"):
        yield build_status() + "\n\n**Error:** Unexpected result format."
        return

    report = final_result.output
    if isinstance(report, DeepResearchReport):
        report_md = report_to_markdown(report)
    else:
        report_md = str(report)

    status_lines.append("✅ Synthesis complete.")
    status_lines.append("")
    status_lines.append("---")
    status_lines.append("")
    yield build_status() + "\n\n" + report_md


def main():
    demo = gr.ChatInterface(
        fn=chat,
        title="Deep Research Agent",
        description="Enter a free-text query or a stock ticker (e.g. NVDA). The agent will run multi-step web research and return a structured report with citations.",
    )
    demo.launch(share=False)


if __name__ == "__main__":
    main()
