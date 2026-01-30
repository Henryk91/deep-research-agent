"""Gradio frontend for the Pydantic AI agent."""

import gradio as gr

from agent import agent


def chat(message: str, history):
    """Send user message to the agent and return the reply string."""
    if not message.strip():
        return ""
    result = agent.run_sync(message)
    return result.output if isinstance(result.output, str) else str(result.output)


def main():
    demo = gr.ChatInterface(
        fn=chat,
        title="Pydantic AI Agent",
        description="Ask anything — the agent answers briefly.",
    )
    demo.launch(share=False)


if __name__ == "__main__":
    main()
