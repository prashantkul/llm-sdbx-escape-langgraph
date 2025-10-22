"""
HTTP client with baseline security.

✅ Implements: URL format validation, method restrictions
❌ Exploitable: No IP filtering (SSRF to 169.254.169.254), localhost accessible
"""

import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def http_request_tool(args: dict) -> str:
    """Make HTTP request with baseline security checks."""
    url = args.get("url", "")
    method = args.get("method", "GET").upper()
    data = args.get("data")

    # ✅ SECURITY: Input validation
    if not isinstance(url, str) or not url.strip():
        return "Error: Invalid URL"

    if method not in ["GET", "POST", "HEAD"]:
        return f"Error: Method {method} not allowed. Use GET, POST, or HEAD"

    # ✅ SECURITY: URL format validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return "Error: Invalid URL format"

        # ✅ SECURITY: Block file:// protocol
        if parsed.scheme not in ["http", "https"]:
            logger.warning(f"Blocked dangerous protocol: {parsed.scheme}")
            return f"Error: Protocol {parsed.scheme} not allowed. Use http or https"

    except Exception as e:
        return f"Error: Invalid URL: {str(e)}"

    # ❌ SECURITY GAP: No IP address validation
    # ❌ SECURITY GAP: 169.254.169.254 (AWS metadata) accessible!
    # ❌ SECURITY GAP: 169.254.169.254 (GCP metadata) accessible!
    # ❌ SECURITY GAP: localhost accessible
    # ❌ SECURITY GAP: 172.17.0.1 (Docker host) accessible
    # ❌ SECURITY GAP: Private IP ranges (10.0.0.0/8, 192.168.0.0/16) accessible

    try:
        logger.info(f"Making {method} request to: {url}")

        response = requests.request(
            method=method,
            url=url,
            json=data if data else None,
            timeout=10,
            allow_redirects=False  # ✅ SECURITY: Don't follow redirects (prevents some bypasses)
        )

        result = f"Status: {response.status_code}\n"
        result += f"Headers: {dict(response.headers)}\n\n"
        result += f"Body:\n{response.text[:2000]}"  # Limit body size

        return result

    except requests.exceptions.Timeout:
        return "Error: Request timed out after 10 seconds"
    except requests.exceptions.ConnectionError as e:
        return f"Error: Connection failed: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
