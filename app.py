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


# Placeholder shown in chat while the agent is working (typing indicator)
TYPING_PLACEHOLDER = "▌"


def _history_to_messages(history: list[tuple[str, str]]) -> list[dict]:
    """Convert list of (user, assistant) tuples to Gradio 6 Chatbot messages format."""
    messages = []
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    return messages


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
                        if len(q) > 50:
                            q = q[:47] + "..."
                        if search_count == 1:
                            status_queue.put("⏳ **Initial discovery search:** identifying research angles")
                        else:
                            status_queue.put(f"⏳ **Deep dive {search_count - 1}:** _{q}_")
                    else:
                        status_queue.put(f"🔧 Calling {tool_name}...")
                if AgentRunResultEvent and isinstance(event, AgentRunResultEvent):
                    status_queue.put((None, event.result))
                    return
        except Exception as e:
            status_queue.put((None, e))

    asyncio.run(run())


def chat_with_status(message: str, history: list[tuple[str, str]]):
    """
    Generator that yields (chat_history, status_md).
    Chat shows user msg + typing placeholder, then user msg + report (separate from status).
    Status area shows current step; we re-yield every ~0.4s so the typing indicator stays visible.
    """
    if not message.strip():
        yield history, ""
        return

    if not (AgentRunResultEvent and FunctionToolCallEvent):
        result = agent.run_sync(message)
        report = result.output
        if isinstance(report, DeepResearchReport):
            report_md = report_to_markdown(report)
        else:
            report_md = str(report)
        yield history + [(message, report_md)], "✅ Done"
        return

    status_queue: queue.Queue = queue.Queue()
    status_lines: list[str] = [
        "### Current step",
        "",
        "⏳ **Checking intent** and resolving query...",
        "",
    ]
    # Show user message + typing placeholder in chat; status in separate area
    history_with_typing = history + [(message, TYPING_PLACEHOLDER)]
    thread = threading.Thread(target=_run_agent_with_events, args=(message, status_queue))
    thread.start()

    def status_md() -> str:
        return "\n".join(status_lines)

    # Initial yield: typing + "Checking intent..."
    yield history_with_typing, status_md()

    final_result = None
    while True:
        try:
            item = status_queue.get(timeout=0.4)
        except queue.Empty:
            # Re-yield so Gradio keeps showing typing and current status
            yield history_with_typing, status_md()
            continue
        if isinstance(item, tuple) and item[0] is None:
            final_result = item[1]
            break
        status_lines.append(item)
        status_lines.append("")
        yield history_with_typing, status_md()

    thread.join()

    # Synthesis step
    status_lines.append("⏳ **Synthesis:** finalizing report...")
    status_lines.append("")
    yield history_with_typing, status_md()

    if isinstance(final_result, Exception):
        yield history + [(message, "**Error:** " + str(final_result))], status_md() + "\n\n❌ Error."
        return
    if not hasattr(final_result, "output"):
        yield history + [(message, "**Error:** Unexpected result format.")], status_md() + "\n\n❌ Error."
        return

    report = final_result.output
    if isinstance(report, DeepResearchReport):
        report_md = report_to_markdown(report)
    else:
        report_md = str(report)

    # Replace typing placeholder with report; status = Done
    status_lines.append("✅ **Done**")
    final_history = history + [(message, report_md)]
    yield final_history, "\n".join(status_lines)


def main():
    with gr.Blocks(title="Deep Research Agent") as demo:
        gr.Markdown(
            "Enter a free-text query or a stock ticker (e.g. NVDA). "
            "The agent runs multi-step web research and returns a structured report with citations."
        )
        chatbot = gr.Chatbot(label="Chat", height=400)
        status_box = gr.Markdown(
            value="",
            label="Current step",
            elem_id="status-box",
        )
        msg = gr.Textbox(
            label="Message",
            placeholder="e.g. TSLA or What is the outlook for renewable energy?",
            show_label=False,
            container=False,
        )
        submit_btn = gr.Button("Submit", variant="primary")

        state = gr.State(value=[])

        def submit_wrapper(message, history):
            if not message or not message.strip():
                yield _history_to_messages(history), "", history, ""
                return
            for new_history, status_md in chat_with_status(message, history):
                yield _history_to_messages(new_history), status_md, new_history, ""

        submit_btn.click(
            fn=submit_wrapper,
            inputs=[msg, state],
            outputs=[chatbot, status_box, state, msg],
        )
        msg.submit(
            fn=submit_wrapper,
            inputs=[msg, state],
            outputs=[chatbot, status_box, state, msg],
        )

    demo.launch(share=False, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
