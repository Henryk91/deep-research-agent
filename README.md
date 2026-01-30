# Pydantic AI Agent + Gradio

A simple chat agent built with [Pydantic AI](https://ai.pydantic.dev) and [Gradio](https://gradio.app). The agent uses OpenAI's **gpt-5-mini** and is instructed to answer in a short way.

## What you need

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Steps

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` to your key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

(Do not commit `.env` — it is for secrets.)

### 4. Run the app

```bash
python app.py
```

Gradio will print a local URL (e.g. `http://127.0.0.1:7860`). Open it in your browser and chat with the agent.

## Project layout

| File / folder   | Purpose                                      |
|-----------------|----------------------------------------------|
| `agent.py`      | Pydantic AI agent (short answers, gpt-5-mini) |
| `app.py`        | Gradio chat UI that calls the agent          |
| `requirements.txt` | Python dependencies                        |
| `.env.example`  | Template for `.env` (copy to `.env`)         |
| `README.md`     | This file                                    |

## Optional

- **Change model:** set `OPENAI_MODEL` in `.env`, e.g. `OPENAI_MODEL=openai:gpt-4o-mini`.
- **Share the app:** in `app.py`, use `demo.launch(share=True)` to get a public Gradio link.
