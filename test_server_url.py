#!/usr/bin/env python3
"""
Test server package URL directly
"""

import requests

def test_server_url():
    print("=== Testing Server Package URL ===")

    url = "https://cursor.blob.core.windows.net/remote-releases/61e99179e4080fecf9d8b92c6e2e3e00fbfb53f0/cursor-reh-linux-x64.tar.gz"

    headers = {
        "User-Agent": "Cursor/2.6.13 (Windows; Remote-SSH)"
    }

    print(f"URL: {url}")

    try:
        response = requests.head(url, timeout=30, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("\nOK: Server URL works!")
            print(f"Content-Length: {response.headers.get('Content-Length')}")
        else:
            print(f"\nERROR: Server URL failed with status: {response.status_code}")

    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    test_server_url()