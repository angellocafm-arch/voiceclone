"""
VoiceClone — Browser Control

Opens URLs and reads web content. All actions use the user's default
browser (Chrome preferred) on macOS/Linux.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Max content to extract from a webpage
MAX_PAGE_CONTENT = 10000
HTTP_TIMEOUT = 15.0


class BrowserControl:
    """
    Browser operations for VoiceClone.

    Opens URLs in the system browser and can read webpage content
    via HTTP for the LLM to process.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "VoiceClone/4.0 (Accessibility Assistant)"},
        )

    # ─── Open URLs ────────────────────────────────────────

    def open_url(self, url: str) -> dict[str, Any]:
        """
        Open a URL in the default system browser.

        Confirmation level: NONE (opening a URL is safe)

        Args:
            url: URL to open.

        Returns:
            Success/failure dict.
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            system = os.uname().sysname
            if system == "Darwin":
                subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Linux":
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                return {"error": f"Unsupported OS: {system}", "success": False}

            logger.info("Opened URL: %s", url)
            return {"success": True, "url": url}

        except Exception as e:
            logger.error("Failed to open URL: %s", e)
            return {"error": str(e), "success": False}

    # ─── Read Web Content ─────────────────────────────────

    async def read_webpage(
        self,
        url: str,
        max_chars: int = MAX_PAGE_CONTENT,
    ) -> dict[str, Any]:
        """
        Fetch and extract text content from a webpage.

        Confirmation level: NONE

        Args:
            url: URL to read.
            max_chars: Maximum characters to return.

        Returns:
            Dict with page title and content.
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            html = response.text

            # Simple HTML → text extraction
            title = _extract_title(html)
            text = _html_to_text(html)
            truncated = len(text) > max_chars

            return {
                "success": True,
                "url": str(response.url),
                "title": title,
                "content": text[:max_chars],
                "truncated": truncated,
            }

        except httpx.ConnectError:
            return {"error": "Could not connect to the website", "success": False}
        except httpx.TimeoutException:
            return {"error": "Website took too long to respond", "success": False}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    # ─── Search ───────────────────────────────────────────

    async def search_web(
        self,
        query: str,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Search the web. Uses DuckDuckGo HTML API (no API key needed).

        Confirmation level: NONE

        Args:
            query: Search query.
            max_results: Number of results.

        Returns:
            Dict with search results.
        """
        try:
            response = await self._client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
            )
            response.raise_for_status()

            results = _parse_ddg_results(response.text, max_results)

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            logger.error("Web search failed: %s", e)
            return {"error": str(e), "success": False}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


# ─── HTML Helpers ─────────────────────────────────────────

def _extract_title(html: str) -> str:
    """Extract <title> from HTML."""
    import re
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text (simple extraction)."""
    import re

    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _parse_ddg_results(html: str, max_results: int) -> list[dict[str, str]]:
    """Parse DuckDuckGo HTML search results."""
    import re

    results: list[dict[str, str]] = []

    # Find result blocks
    pattern = r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</span'
    matches = re.findall(pattern, html, re.DOTALL)

    for url, title, snippet in matches[:max_results]:
        results.append({
            "title": re.sub(r"<[^>]+>", "", title).strip(),
            "url": url,
            "snippet": re.sub(r"<[^>]+>", "", snippet).strip(),
        })

    return results
