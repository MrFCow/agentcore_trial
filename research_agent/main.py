from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

from config import create_model
from tools.duckduckgo_search import duckduckgo_search

SYSTEM_PROMPT = """You are a research assistant with web search capabilities.
Use the duckduckgo_search tool to find information on the web when needed.

When presenting slides, output ONLY the slide content - start directly with "Slide 1:" or the first slide title. Do NOT include any reasoning, thought process, or meta-commentary."""


app = BedrockAgentCoreApp()
model = create_model()

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[duckduckgo_search],
)


@app.entrypoint
async def invoke(payload):
    """AgentCore entrypoint - receives prompt, returns response."""
    user_message = payload.get("prompt", "")
    if not user_message:
        return {"error": "No prompt provided in payload"}

    # Pass 1: Initial agent call
    print("=== Pass 1 Start ===")
    result = await agent.invoke_async(user_message)
    slide_text = str(result)
    print(f"Pass 1 output:\n{slide_text}\n=== Pass 1 End ===")

    # Pass 2: Gate keeper to extract clean slide content
    print("=== Pass 2 Start ===")
    cleaned_result = await agent.invoke_async(
        f"Extract ONLY the slide/presentation content from this response. "
        f"Start directly with 'Slide 1:' or first slide title. Remove any reasoning, "
        f"thoughts, or meta-commentary:\n\n{slide_text}"
    )
    cleaned_text = str(cleaned_result)
    print(f"Pass 2 output:\n{cleaned_text}\n=== Pass 2 End ===")

    return {"result": cleaned_text}


if __name__ == "__main__":
    app.run()
