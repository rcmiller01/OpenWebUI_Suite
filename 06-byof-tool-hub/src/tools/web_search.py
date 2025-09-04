"""
Web Search Tool Implementation
"""

import asyncio
from typing import Dict, Any


async def web_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a web search and return results"""
    # Simulate search delay
    await asyncio.sleep(0.2)  # Simulate network delay

    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)

    # Mock search results
    results = []
    for i in range(min(max_results, 5)):
        results.append({
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/result{i+1}",
            "snippet": (f"This is a mock search result snippet {i+1} "
                       f"containing information about {query}."),
            "source": "example.com",
            "rank": i + 1
        })

    return {
        "query": query,
        "results": results,
        "total_results": len(results),
        "search_time": 0.15,
        "cached": False
    }
