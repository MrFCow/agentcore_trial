# HTML Generator MCP

An MCP (Model Context Protocol) server that generates interactive HTML presentations from slide text using LLM-powered parsing.

## Features

- **LLM-Powered Parsing**: Uses Strands with OpenAI-compatible models to parse unstructured slide text into structured data
- **Interactive Presentations**: Generates self-contained HTML with navigation, progress bar, and keyboard controls
- **Flexible Input**: Accepts various slide text formats (numbered slides, markdown-style, pipe-separated, etc.)

## Requirements

- Python 3.10+
- OpenAI-compatible LLM endpoint (local or hosted)
- Environment variables:
  - `OPENAI_BASE_URL`: API endpoint URL (default: `http://127.0.0.1:4000/v1`)
  - `OPENAI_API_KEY`: API key (default: `NA` for local models)
  - `MODEL_ID`: Model name (default: `nemotron-3-super-120b-a12b`)

## Installation

```bash
cd html_generator_mcp
uv sync
```

## Usage

### Start the MCP Server

```bash
python main.py
```

The server runs on `http://0.0.0.0:8000`.

### As an MCP Tool

Call the `generate_presentation` tool with slide text:

```
Slide 1: Welcome | Welcome to our presentation!
Slide 2: Agenda | - Topic 1
- Topic 2
- Topic 3
```

Returns JSON with path to the generated HTML file.

### Input Formats Supported

- `Slide 1: Title | Content...`
- Numbered slides with newlines: `Slide 1\nTitle\nContent`
- Markdown with `---` separators
- Any text describing multiple slides

## Output

Generates HTML files in `html_generator_mcp/output/` with:
- Interactive slide navigation (Previous/Next buttons)
- Keyboard controls (Arrow keys, Space)
- Progress bar
- Slide counter
- Dark theme with smooth transitions

## Architecture

- **FastMCP**: MCP server framework
- **Strands**: Agent framework for LLM interactions
- **OpenAI Compatible**: Works with any OpenAI-compatible API (Ollama, LM Studio, vLLM, etc.)