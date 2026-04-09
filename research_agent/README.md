# Research Agent

A Strands Agents-based research assistant with DuckDuckGo web search and slide generation capabilities, ready for AgentCore runtime deployment.

## Features

- **Web Search**: Uses DuckDuckGo via `ddgs` library as a custom `@tool`
- **Slide Generation**: Creates structured slide-by-slide presentations from research
- **Two-Pass Architecture**: 
  - Pass 1: Initial research and slide generation
  - Pass 2: Gate keeper to clean/extract only slide content
- **AgentCore Ready**: Uses `BedrockAgentCoreApp` with `@app.entrypoint` decorator

## Quick Start

### Install Dependencies

```bash
cd research_agent
uv sync
```

### Run Locally

```bash
uv run python main.py
```

### Test with Curl

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "3 slide presentation for Raspberry Pi"}'
```

## Configuration

Environment variables (can be set in shell or `config.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_BASE_URL` | `http://127.0.0.1:4000/v1` | OpenAI-compatible API endpoint |
| `MODEL_ID` | `llama3` | Model name |
| `OPENAI_API_KEY` | `not-needed` | API key (not needed for local models) |

## Project Structure

```
research_agent/
├── main.py                   # Agent + AgentCore entry point
├── config.py                 # Model configuration (swappable)
├── pyproject.toml            # Dependencies
├── tools/
│   ├── __init__.py
│   └── duckduckgo_search.py  # Custom @tool for DuckDuckGo
└── __init__.py
```

## Code Highlights

### Custom Tool (duckduckgo_search.py)

```python
@tool
def duckduckgo_search(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo for information."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
    # ... format results
    return {"status": "success", "content": [{"text": formatted}]}
```

### AgentCore Entry Point (main.py)

```python
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload):
    # Pass 1: Generate slides
    result = await agent.invoke_async(user_message)
    slide_text = str(result)
    
    # Pass 2: Clean output
    cleaned = await agent.invoke_async(f"Extract slide content:\n{slide_text}")
    return {"result": str(cleaned)}
```

## Extending

- **Add more tools**: Add to `tools/` directory and import in `main.py`
- **Change model**: Update `config.py` - swap OpenAI-compatible for Anthropic, Bedrock, etc.
- **Structured output**: Use `agent.structured_output(YourModel, prompt)` with Pydantic

## Notes

- Uses `str(result)` (via `AgentResult.__str__()`) for text extraction - built into Strands SDK
- Output is slide-by-slide text format (not JSON)
- Debug prints show Pass 1 and Pass 2 outputs for troubleshooting