# app/claude_client.py

from anthropic import AsyncAnthropic
from tools import web_page_results, serp

client = AsyncAnthropic()

TOOLS = [
    {
        "name": "web_page_results",
        "description": (
            "Fetch and parse a single web page. "
            "Use this when the user provides a URL or asks to scrape a specific page."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Fully-qualified URL to fetch."
                },
                "dynamic": {
                    "type": "boolean",
                    "description": "Use dynamic renderer (JS).",
                    "default": True,
                },
                "include_links": {
                    "type": "boolean",
                    "description": "Whether to extract links from the page.",
                    "default": True,
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "serp",
        "description": (
            "Run a Google web search via ScrapingDog. "
            "Use this when the user asks for Google search results, SERP info, "
            "or fresh web information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to execute."
                },
                "country": {
                    "type": "string",
                    "description": "Country code (e.g. 'us', 'uk').",
                    "default": "us",
                },
                "results": {
                    "type": "integer",
                    "description": "Number of results to return (1-100).",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                },
                "location": {
                    "type": ["string", "null"],
                    "description": "Specific location for search."
                },
            },
            "required": ["query"],
        },
    },
]

TOOL_IMPLS = {
    "web_page_results": web_page_results,
    "serp": serp,
}
