# AgentCore Test

Demos showcasing Strands agents with Amazon Bedrock AgentCore — including multi-agent A2A communication, MCP server patterns, and AgentCore runtime deployment.

## Demos

| Folder | Description |
|--------|-------------|
| `a2a/` | Multi-agent travel booking system with 3 Strands agents (Travel, Hotel, Airline) communicating via A2A protocol. Deployable to AgentCore Runtime. |
| `agent_as_mcp/` | Running Strands agents as MCP servers: `html_generator_mcp` (parses slide text to HTML), `research_agent` (web search + slide generation, deployable to AgentCore). |