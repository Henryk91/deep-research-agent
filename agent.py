"""Pydantic AI agent with short answers, powered by OpenAI gpt-5-mini."""

import os

from dotenv import load_dotenv
from pydantic_ai import Agent

load_dotenv()

# Model from env or default to gpt-5-mini
MODEL_NAME = os.getenv("OPENAI_MODEL", "openai:gpt-5-mini")

agent = Agent(
    MODEL_NAME,
    instructions=(
        "Answer in a short way. Keep replies concise: one or two sentences when possible. "
        "Do not use bullet lists or long paragraphs unless the user explicitly asks for detail."
    ),
)
