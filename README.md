# Pydantic AI Chat Agent (gpt-5-mini)

This project demonstrates a simple AI Agent built using the [Pydantic AI](https://ai.pydantic.dev/) framework, featuring a modern [Gradio](https://gradio.app/) frontend. The agent is configured to provide short, concise answers using the `gpt-5-mini` model.

## Features

- **Pydantic AI Framework**: Leverages the Pydantic way of building agents.
- **gpt-5-mini Model**: Uses OpenAI's latest mini model (as per request/documentation).
- **Short Responses**: System-level instructions ensure the agent stays brief.
- **Gradio Frontend**: An interactive, user-friendly chat interface.

## Prerequisites

- Python 3.10 or higher
- An OpenAI API Key

## Setup Instructions

### 1. Clone the repository (if applicable)

```bash
# Navigate to the project directory
cd "PydanticAI Deep Research Agent"
```

### 2. Create and Activate a Virtual Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a file named `.env` in the root directory and add your OpenAI API key:

```env
OPENAI_API_KEY=your_sk_key_here
```

### 5. Run the Application

```bash
python app.py
```

After running the command, Gradio will provide a local URL (e.g., `http://127.0.0.1:7860`) where you can interact with your agent.

## Project Structure

- `app.py`: Main application code containing the Agent logic and Gradio UI.
- `requirements.txt`: List of Python dependencies.
- `.env`: (To be created) Configuration for API keys.
- `docs.md`: Reference documentation for Pydantic AI.
