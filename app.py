import asyncio
import gradio as gr
from dotenv import load_dotenv
from research_agent import run_research

# Load environment variables from .env file
load_dotenv()


async def chat_with_agent(message, history):
    """
    Function to handle the research orchestration with streaming.
    """
    try:
        # Run the deep research orchestration
        log_buffer = "### Research Progress\n"
        async for update in run_research(message):
            if update.startswith("📝") or update.startswith(
                "Topic:"
            ):  # Final report or synthesis start
                yield update
            else:
                log_buffer += f"> {update}\n\n"
                yield log_buffer
    except Exception as e:
        yield f"Error during research: {str(e)}"


# Define the Gradio interface
demo = gr.ChatInterface(
    fn=chat_with_agent,
    title="Deep Research Agent",
    description="Multi-step web research agent using Pydantic AI and DuckDuckGo. Enter a stock ticker or a query.",
    examples=[
        "NVDA",
        "AAPL",
        "Future of generative AI agents in software engineering",
    ],
)

if __name__ == "__main__":
    # Launch the Gradio app
    demo.launch()
