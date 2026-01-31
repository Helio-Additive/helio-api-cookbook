"""
Authentication helpers for the Helio Additive API.

Supports loading a Personal Access Token (PAT) from:
  1. HELIO_PAT environment variable (recommended)
  2. ~/.helio_config file
  3. Interactive prompt
"""

import os
import sys


def load_pat_token():
    """Load PAT token from env var, config file, or interactive prompt.

    Returns:
        The PAT token string.

    Raises:
        SystemExit: If no token is provided interactively.
    """
    # 1. Environment variable
    token = os.environ.get("HELIO_PAT", "").strip()
    if token:
        print("PAT loaded from HELIO_PAT environment variable.")
        return token

    # 2. Config file
    config_path = os.path.expanduser("~/.helio_config")
    if os.path.isfile(config_path):
        with open(config_path, "r") as f:
            token = f.read().strip()
        if token:
            print(f"PAT loaded from {config_path}")
            return token

    # 3. Interactive prompt
    print("No PAT token found in HELIO_PAT env var or ~/.helio_config")
    token = input("Enter your Helio PAT token: ").strip()
    if not token:
        print("Error: PAT token is required.")
        sys.exit(1)
    return token
