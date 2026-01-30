"""Pydantic AI agent with short answers, powered by OpenAI gpt-5-mini."""

import os

from dotenv import load_dotenv
from pydantic_ai import Agent

load_dotenv()

# Model from env or default to gpt-5-mini
MODEL_NAME = os.getenv("OPENAI_MODEL", "openai:gpt-5-mini")

agent = Agent(
    MODEL_NAME,
    instructions='You are a helpful assistant.',
)
