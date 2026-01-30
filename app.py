"""Gradio frontend for the Deep Research Agent."""

import gradio as gr

from agent import DeepResearchReport, agent


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


def chat(message: str, history):
    """Send user message to the agent and return the report as markdown."""
    if not message.strip():
        return ""
    result = agent.run_sync(message)
    report = result.output
    if isinstance(report, DeepResearchReport):
        return report_to_markdown(report)
    return str(report)


def main():
    demo = gr.ChatInterface(
        fn=chat,
        title="Deep Research Agent",
        description="Enter a free-text query or a stock ticker (e.g. NVDA). The agent will run multi-step web research and return a structured report with citations.",
    )
    demo.launch(share=False)


if __name__ == "__main__":
    main()
