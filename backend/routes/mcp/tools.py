import logging
from typing import Any, Dict, Optional
from pydantic import Field
import httpx
import json
from trafilatura import extract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scraping_tools')

# ScrapingDog API Key
SCRAPINGDOG_API_KEY = ""


async def webpage_scraper(
    url: str,
    dynamic: bool = True,
    **kwargs: Any
) -> str:
    """Scrape a webpage using ScrapingDog API"""
    try:
        scrape_url = "https://api.scrapingdog.com/scrape"
        params = {
            "api_key": SCRAPINGDOG_API_KEY,
            "url": url,
            "dynamic": str(dynamic).lower(),
        }
        for key, value in kwargs.items():
            if value is not None:
                params[key] = str(value)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(scrape_url, params=params)
            if response.status_code == 200:
                return response.text
            else:
                error_msg = f"ScrapingDog API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    except Exception as e:
        logger.exception("Error while calling ScrapingDog API")
        raise


async def web_page_results(
    url: str,
    dynamic: bool = True,
    include_links: bool = True,
) -> Dict[str, Any]:
    """
    Fetch and parse a single web page.
    Use this when the user provides a URL or asks to scrape a specific page.
    """
    try:
        html = await webpage_scraper(url=url, dynamic=dynamic)
    except Exception as exc:
        return {"url": url, "error": str(exc)}
    
    if not html:
        return {"url": url, "error": "No HTML returned from scraper."}
    
    # Limit HTML size
    if len(html) > 800000:
        html = html[:800000]
    
    try:
        extracted_json = extract(
            html,
            output_format="json",
            with_metadata=True,
            include_links=include_links,
        )
        extracted = json.loads(extracted_json) if extracted_json else {}
    except Exception as exc:
        return {"url": url, "error": f"Failed to parse HTML: {exc}"}
    
    text_content = extracted.get("text") or ""
    
    return {
        "url": url,
        "title": extracted.get("title"),
        "description": extracted.get("description"),
        "language": extracted.get("language"),
        "author": extracted.get("author"),
        "published": extracted.get("date"),
        "content": text_content,
        "links": extracted.get("links") if include_links else None,
        "metadata": {
            "sitename": extracted.get("sitename"),
            "favicon": extracted.get("favicon"),
            "canonical_url": extracted.get("canonical"),
        },
    }


async def google_search_scraper(
    query: str,
    country: str = "us",
    results: int = 10,
    location: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Internal function to call ScrapingDog Google Search API"""
    try:
        url = "https://api.scrapingdog.com/google/"
        params = {
            "api_key": SCRAPINGDOG_API_KEY,
            "query": query,
            "results": str(results),
        }
        
        if location is not None:
            params["location"] = location
        else:
            params["country"] = country
        
        for key, value in kwargs.items():
            if value is not None:
                params[key] = str(value)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data
                }
            else:
                logger.error(f"ScrapingDog API returned status {response.status_code}")
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "response": response.text
                }
    except httpx.TimeoutException:
        logger.exception("ScrapingDog API timeout")
        return {
            "success": False,
            "error": "Request timed out after 30 seconds",
        }
    except Exception as e:
        logger.exception("Error while calling ScrapingDog Google API")
        return {
            "success": False,
            "error": str(e),
        }


async def serp(
    query: str,
    country: str = "us",
    results: int = 10,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a Google web search via ScrapingDog.
    Use this when the user asks for Google search results, SERP info, or fresh web information.
    """
    try:
        raw = await google_search_scraper(
            query=query,
            country=country,
            results=results,
            location=location
        )
        
        if not raw.get("success"):
            return {
                "query": query,
                "country": country,
                "location": location,
                "results": [],
                "provider": "scrapingdog",
                "error": raw.get("error", "Unknown error"),
            }
        
        data = raw.get("data", {})
        return {
            "query": query,
            "country": country,
            "location": location,
            "provider": "scrapingdog",
            "raw_metadata": data.get("search_metadata"),
            "results": data,
        }
    except Exception as exc:
        logger.exception(f"Error in serp tool: {exc}")
        return {
            "query": query,
            "country": country,
            "location": location,
            "results": [],
            "provider": "scrapingdog",
            "error": str(exc),
        }
