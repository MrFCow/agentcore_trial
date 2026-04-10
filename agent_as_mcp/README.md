# Agent as MCP

Examples of running Strands agents as MCP (Model Context Protocol) servers. MCP allows agents to expose their capabilities as tools that can be consumed by other agents, LLMs, or applications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP Client (LLM/Agent)                        │
│                                  │                                   │
│                                  ▼                                   │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │ HTML Generator MCP  │    │   Research Agent    │                │
│  │      (port 8000)    │    │    (port 8080)      │                │
│  └─────────────────────┘    └─────────────────────┘                │
│           │                            │                            │
│           ▼                            ▼                            │
│   LLM for parsing              DuckDuckGo search                   │
│   slide text                   + LLM for synthesis                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Agents

### HTML Generator MCP

An MCP server that generates interactive HTML presentations from slide text using LLM-powered parsing.

- **Port**: 8000
- **Framework**: FastMCP + Strands
- **Input**: Unstructured slide text in various formats
- **Output**: Self-contained HTML file with navigation, progress bar, keyboard controls

**Input Formats Supported**:
- `Slide 1: Title | Content...`
- Numbered slides with newlines: `Slide 1\nTitle\nContent`
- Markdown with `---` separators
- Any text describing multiple slides

**Output Features**:
- Interactive slide navigation (Previous/Next buttons)
- Keyboard controls (Arrow keys, Space)
- Progress bar
- Slide counter
- Dark theme with smooth transitions

### Research Agent

A Strands agent with web search and slide generation capabilities, deployable to AgentCore Runtime.

- **Port**: 8080
- **Framework**: Strands + BedrockAgentCoreApp
- **Tools**: DuckDuckGo search (custom `@tool`)
- **Architecture**: Two-pass (generate → clean/extract)

**Two-Pass Flow**:
1. **Pass 1**: Initial research and slide generation
2. **Pass 2**: Gate keeper to clean/extract only slide content

## Project Structure

```
agent_as_mcp/
├── README.md
├── html_generator_mcp/
│   ├── README.md
│   ├── main.py                # FastMCP server + generate_presentation tool
│   ├── pyproject.toml
│   ├── output/                 # Generated HTML files
│   └── prompt.py              # System prompt for LLM parsing
└── research_agent/
    ├── README.md
    ├── main.py                # Agent + AgentCore entry point
    ├── config.py              # Model configuration
    ├── pyproject.toml
    └── tools/
        ├── __init__.py
        └── duckduckgo_search.py  # Custom @tool for web search
```

## Communication

- **MCP Protocol**: Uses FastMCP to expose agents as MCP servers
- **Tool Calling**: Clients invoke `generate_presentation` or invoke the agent directly
- **HTTP**: Standard HTTP/JSON communication over MCP stdio or HTTP transport

## Quick Start

### Prerequisites

- Python 3.10+
- uv package manager
- OpenAI-compatible LLM endpoint (local or hosted)

### HTML Generator MCP

```bash
cd html_generator_mcp
uv sync
python main.py
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/tools/generate_presentation \
  -H "Content-Type: application/json" \
  -d '{
    "slide_text": "Slide 1: Welcome | Welcome!\nSlide 2: Agenda | - Topic 1\n- Topic 2"
  }'
```

### Research Agent

```bash
cd research_agent
uv sync
uv run python main.py
```

**Test with curl**:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "3 slide presentation for Raspberry Pi"}'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | OpenAI-compatible API endpoint | `http://127.0.0.1:4000/v1` |
| `OPENAI_API_KEY` | API key | `NA` |
| `MODEL_ID` | Model name | `nemotron-3-super-120b-a12b` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Agent port | 8000 / 8080 |

## MCP Tool Definition

### HTML Generator MCP

```json
{
  "name": "generate_presentation",
  "description": "Generate an interactive HTML presentation from slide text",
  "inputSchema": {
    "type": "object",
    "properties": {
      "slide_text": {
        "type": "string",
        "description": "Slide text in various formats (Slide 1: Title | Content, numbered slides, markdown)"
      }
    },
    "required": ["slide_text"]
  }
}
```

### Research Agent (via AgentCore)

```json
{
  "name": "invoke",
  "description": "Generate a slide presentation from research query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "Research topic or question"
      }
    },
    "required": ["prompt"]
  }
}
```

## MCP Integration: Research Agent → HTML Generator MCP

The Research Agent can use the HTML Generator MCP as a tool to create presentations from its research output. This demonstrates how one agent can consume another agent's MCP services.

### System Prompt Integration

The research agent's system prompt instructs it to use the HTML generator tool after generating slide content:

```
You are a research assistant. 
1. Search the web for information on the given topic
2. Generate a slide-by-slide presentation from the research
3. Use the generate_presentation tool to create the final HTML output

When the user asks for a presentation:
- First, use duckduckgo_search to gather information
- Then, synthesize the research into slide format (Slide 1: Title | Content)
- Finally, call generate_presentation with the slide text to create the HTML
```

### Tool Usage Flow

```
User: "Create a presentation about Raspberry Pi"

         ┌──────────────────┐
         │  Research Agent  │
         └────────┬─────────┘
                  │
         1. duckduckgo_search("Raspberry Pi")
                  │
         ┌────────▼─────────┐
         │   Web Results    │
         └────────┬─────────┘
                  │
         2. Generate slides │
                  │
         ┌────────▼─────────┐
         │  Slide Text      │
         │ "Slide 1: Intro  │
         │  | Raspberry Pi  │
         │  is a..."        │
         └────────┬─────────┘
                  │
         3. generate_presentation(slide_text)
                  │
         ┌────────▼──────────────────────────┐
         │  HTML Generator MCP (port 8000)  │
         └────────┬──────────────────────────┘
                  │
         4. LLM parses slides + generates HTML
                  │
         ┌────────▼─────────┐
         │  HTML file path  │
         └──────────────────┘
```

### Running Both Together

```bash
# Terminal 1: Start HTML Generator MCP
cd html_generator_mcp
uv sync
python main.py  # port 8000

# Terminal 2: Start Research Agent (with MCP tool configured)
cd research_agent
uv sync
uv run python main.py  # port 8080
```

### MCP Tool Configuration

For the research agent to use the HTML Generator MCP, configure the MCP client in the research agent:

```python
from mcp import Client

mcp_client = Client("http://localhost:8000")

# Add to agent's available tools
@mcp_client.tool
def generate_presentation(slide_text: str) -> dict:
    """Generate interactive HTML from slide text."""
    pass
```

Or via environment configuration:
```
MCP_SERVERS='{"html_generator": {"url": "http://localhost:8000"}}'
```

## Deployment to AgentCore

The Research Agent is designed for AgentCore deployment:

```bash
# Update config.py to use Bedrock model
# Then deploy via AgentCore CLI
agentcore deploy --entry-point main:app --name research-agent
```

When deploying:
1. Update `config.py` to use Bedrock model instead of OpenAI-compatible
2. Ensure `ddgs` package is in dependencies
3. Deploy using AgentCore CLI

## Extending

### Adding New MCP Agents

1. Create new folder under `agent_as_mcp/`
2. Use FastMCP for MCP server or BedrockAgentCoreApp for AgentCore
3. Add custom `@tool` decorators for capabilities
4. Update this README with agent details

### Adding Tools to Existing Agents

1. Add function with `@tool` decorator in main.py
2. Update system prompt with tool description
3. For MCP: tools auto-exposed via FastMCP
4. For AgentCore: tools auto-available in invocations

## Code Highlights

### Custom Tool (Research Agent)

```python
@tool
def duckduckgo_search(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo for information."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
    return {"status": "success", "content": [{"text": formatted}]}
```

### MCP Server (HTML Generator)

```python
from strands import Agent
from fastmcp import FastMCP

mcp = FastMCP("HTML Generator")
agent = Agent(system_prompt=...)

@mcp.tool
def generate_presentation(slide_text: str) -> dict:
    result = agent.invoke(slide_text)
    return {"html_path": save_html(result)}
```

### AgentCore Entry Point (Research Agent)

```python
from strands_agents import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload):
    result = await agent.invoke_async(user_message)
    cleaned = await agent.invoke_async(f"Extract slide content:\n{result}")
    return {"result": str(cleaned)}
```