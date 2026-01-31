"""
Core GraphQL client for the Helio Additive API.

Provides the HelioClient class that wraps authentication and request
handling, plus shared utility functions used across the library.
"""

import datetime
import os
import sys

import requests

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

API_URL_GLOBAL = "https://api.helioadditive.com/graphql"
API_URL_CHINA = "https://api.helioam.cn/graphql"

# ---------------------------------------------------------------------------
# Polling Constants
# ---------------------------------------------------------------------------

GCODE_POLL_INTERVAL_S = 2
GCODE_POLL_MAX = 60
SIM_OPT_POLL_INTERVAL_S = 3
MAX_CONSECUTIVE_HTTP_FAILURES = 5


class HelioClient:
    """Client for the Helio Additive GraphQL API.

    Wraps authentication headers and provides a ``query()`` method for
    executing GraphQL operations against the Helio endpoint.

    Args:
        pat_token: Helio Personal Access Token.
        api_url: Override API URL.  Resolution order:
            1. This explicit argument
            2. ``HELIO_API_URL`` environment variable
            3. Default: ``API_URL_GLOBAL`` (api.helioadditive.com)
    """

    DEFAULT_API_URL = API_URL_GLOBAL
    CLIENT_NAME = "PythonScript"
    CLIENT_VERSION = "1.0.0"

    def __init__(self, pat_token: str, api_url: str | None = None):
        self.pat_token = pat_token
        if api_url is not None:
            self.api_url = api_url
        else:
            self.api_url = os.environ.get("HELIO_API_URL", API_URL_GLOBAL)

    def _get_headers(self) -> dict[str, str]:
        """Return standard auth headers for Helio API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.pat_token}",
            "HelioAdditive-Client-Name": self.CLIENT_NAME,
            "HelioAdditive-Client-Version": self.CLIENT_VERSION,
        }

    def query(
        self, query: str, variables: dict | None = None
    ) -> tuple[dict | None, list[str] | None, str]:
        """Execute a GraphQL query or mutation.

        Args:
            query: The GraphQL query/mutation string.
            variables: Optional variables dict for the operation.

        Returns:
            ``(data, errors, trace_id)`` tuple where:
            - *data*: the ``data`` field from the response, or ``None``
            - *errors*: list of error message strings, or ``None``
            - *trace_id*: ``trace-id`` response header value, or ``""``
        """
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        headers = self._get_headers()
        trace_id = ""

        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
        except requests.exceptions.RequestException as e:
            return None, [f"Network error: {e}"], trace_id

        trace_id = resp.headers.get("trace-id", "")

        if resp.status_code == 401:
            return None, ["HTTP 401 Unauthorized - check your PAT token."], trace_id
        if resp.status_code == 429:
            return None, ["HTTP 429 - quota exceeded or rate limited."], trace_id
        if resp.status_code != 200:
            return None, [f"HTTP {resp.status_code}: {resp.text[:500]}"], trace_id

        try:
            body = resp.json()
        except ValueError:
            return None, ["Failed to parse JSON response."], trace_id

        errors = None
        if "errors" in body:
            errs = body["errors"]
            if isinstance(errs, list):
                errors = [e.get("message", str(e)) for e in errs]
            elif isinstance(errs, dict):
                errors = [errs.get("message", str(errs))]

        data = body.get("data")
        return data, errors, trace_id


# ---------------------------------------------------------------------------
# Shared Utility Functions
# ---------------------------------------------------------------------------


def print_progress_bar(progress: float, width: int = 40) -> None:
    """Print an ASCII progress bar to stdout.

    Args:
        progress: Percentage value (0-100).
        width: Character width of the bar.
    """
    filled = int(width * progress / 100)
    bar = "#" * filled + "-" * (width - filled)
    sys.stdout.write(f"\r  [{bar}] {progress:.0f}%")
    sys.stdout.flush()


def generate_timestamped_name() -> str:
    """Generate a timestamped name like ``PythonScript 2025-03-12T14:23:45``."""
    now = datetime.datetime.utcnow()
    return f"PythonScript {now.strftime('%Y-%m-%dT%H:%M:%S')}"
