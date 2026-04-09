import os
from strands import tool
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def get_mcp_url() -> str:
    """Get MCP server URL from environment or default to local."""
    return os.getenv("MCP_URL", "http://localhost:8000/mcp")


@tool
async def generate_presentation(slide_text: str) -> dict:
    """Generate HTML presentation from slide text.

    Use this as your FINAL step after creating slide content.

    Args:
        slide_text: Multi-line slide text (e.g., "Slide 1: Title | Content...")

    Returns:
        JSON with path, filename, slide_count, and preview.
    """
    url = get_mcp_url()

    async with streamable_http_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "generate_presentation", {"slide_text": slide_text}
            )
            if result.content and len(result.content) > 0:
                return {
                    "status": "success",
                    "content": [{"text": result.content[0].text}],
                }
            return {
                "status": "error",
                "content": [{"text": "No result from MCP server"}],
            }
