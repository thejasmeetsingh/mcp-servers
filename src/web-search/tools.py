import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from schema import SearchResult, WebPageExtractResult
from utils import convert_dict_to_markdown


load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

RESULTS_PER_PAGE = 10
MAX_REQUEST_TIMEOUT = 30  # In seconds


mcp = FastMCP("web-search")


@mcp.tool(
    name="Web Search",
    description="Perform a web search using Brave Search API",
    annotations={"title": "Web Search", "readOnlyHint": True}
)
async def web_search(query: str, country: str = "IN") -> str:
    """
    This function connects to the Brave Search API, executes the provided query,
    and returns formatted search results as markdown.

    Args:
        query (str): The search query string to be sent to Brave Search

        country (str, optional): The search query country, where the results come from.
                                Defaults to IN (India). The country string is limited 
                                to 2 character country codes of supported countries by Brave API
    """

    try:
        if not BRAVE_API_KEY:
            raise ValueError(
                "Brave API Key is not configured. Please check your environment variables.")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
        params = {
            "q": query,
            "result_filter": "web",
            "count": RESULTS_PER_PAGE,
            "search_lang": "en",
            "country": country
        }

        client = httpx.AsyncClient(headers=headers, params=params,
                                   timeout=MAX_REQUEST_TIMEOUT)

        response = await client.get(url=url)
        response.raise_for_status()

        web_results = response.json().get("web", {}).get("results", [])

        if not web_results:
            return "No search results found for the query."

        results = {
            "results": [
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("description", "")
                ).model_dump()

                for result in web_results
            ]
        }

        return convert_dict_to_markdown(results)

    except Exception as e:
        raise ValueError(
            f"Error caught while perform a web search: {str(e)}") from e


@mcp.tool(
    name="Extract Web Page Content",
    description="Extract web page content from URLs using Tavily Extract API.",
    annotations={"title": "Extract Web Page Content", "readOnlyHint": True}
)
async def extract_web_page_content(urls: list[str]) -> str:
    """
    This function processes one or more URLs, extracts their content using
    the Tavily Extract API, and returns the extracted content in markdown format.

    Args:
        urls: A single URL string or a list of URL strings to extract content from.
    """

    try:
        if not TAVILY_API_KEY:
            raise ValueError(
                "Tavily API Key is not configured. Please check your environment variables.")

        url = "https://api.tavily.com/extract"
        headers = {
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "urls": urls,
            "extract_depth": "basic",
            "include_images": False
        }

        client = httpx.AsyncClient(headers=headers,
                                   timeout=MAX_REQUEST_TIMEOUT)

        response = await client.post(url=url, json=payload)
        response.raise_for_status()

        extraction_results = response.json().get("results", [])
        if not extraction_results:
            return "No content could be extracted from the provided URLs."

        results = {
            "results": [
                WebPageExtractResult(
                    url=result.get("url", ""),
                    content=result.get("raw_content", "")
                ).model_dump()

                for result in extraction_results
            ]
        }

        return convert_dict_to_markdown(results)

    except Exception as e:
        raise ValueError(
            f"Error caught while extracting web page content: {str(e)}") from e
