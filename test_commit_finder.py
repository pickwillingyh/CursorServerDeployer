#!/usr/bin/env python3
"""
Find working commit hash for downloads.cursor.com
"""

import requests
from urllib.parse import quote

def test_commits():
    print("=== Testing Different Commits ===")

    # Test a few common commit patterns
    test_commits = [
        "60faf7b51077ed1df1db718157bbfed740d2e160",  # Current
        "61e99179e4080fecf9d8b92c6e2e3e00fbfb53f0",  # Azure
        "60faf7b51077ed1df1db718157bbfed740d2e168",  # Truncated?
        "60faf7b51077ed1df1db718157bbfed740d2e",     # Shorter
        "60faf7b51077ed1df1db718157bbfed740",        # Even shorter
    ]

    base_url = "https://downloads.cursor.com/production"
    test_file = "cursor-reh-linux-x64.tar.gz"

    headers = {
        "User-Agent": "Cursor/2.6.13 (Windows; Remote-SSH)"
    }

    for commit in test_commits:
        url = f"{base_url}/{commit}/linux/x64/{test_file}"

        print(f"\nTesting commit: {commit}")
        print(f"URL: {url}")

        try:
            response = requests.head(url, timeout=10, headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("OK: This commit works!")
                print(f"Content-Length: {response.headers.get('Content-Length')}")
                return commit
            elif response.status_code == 403:
                print("Forbidden - commit might exist but not accessible")
            else:
                print("Failed")

        except Exception as e:
            print(f"Error: {e}")

    return None

if __name__ == "__main__":
    working_commit = test_commits()
    if working_commit:
        print(f"\nFound working commit: {working_commit}")
    else:
        print("\nNo working commit found")