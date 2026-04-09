from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from config import create_model
from tools.duckduckgo_search import duckduckgo_search
from tools.mcp_gateway import generate_presentation

SYSTEM_PROMPT = """You are a research assistant with web search and presentation capabilities.

## Available Tools:
1. `duckduckgo_search(query, max_results=5)` - Search the web for information.
2. `generate_presentation(slide_text)` - Generate HTML presentation from slide text.

## Guidelines:
- MAXIMUM 3 web searches per task - gather essential info efficiently and move on.
- Use generate_presentation as your FINAL step after creating slide content.
- Output ONLY slide content starting with "Slide 1:" - no reasoning or meta-commentary.
- After generating presentation, include the HTML file path in your response."""


app = BedrockAgentCoreApp()
model = create_model()

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[duckduckgo_search, generate_presentation],
)


@app.entrypoint
async def invoke(payload):
    """AgentCore entrypoint - receives prompt, returns response."""
    user_message = payload.get("prompt", "")
    if not user_message:
        return {"error": "No prompt provided in payload"}

    result = await agent.invoke_async(user_message)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
