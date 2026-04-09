from strands import tool
from ddgs import DDGS


@tool
def duckduckgo_search(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo for information.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        A dictionary with search results formatted as text content.
    """
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)

    if not results:
        return {"status": "success", "content": [{"text": "No results found."}]}

    formatted = "\n\n".join(
        [
            f"Title: {r.get('title', 'N/A')}\nURL: {r.get('href', 'N/A')}\n{r.get('body', '')}"
            for r in results
        ]
    )

    return {"status": "success", "content": [{"text": formatted}]}
