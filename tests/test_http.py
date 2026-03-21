#!/usr/bin/env python3
"""
Test HTTP request directly
"""

import requests

def test_download():
    print("=== Testing HTTP Request ===")

    url = "https://downloads.cursor.com/production/60faf7b51077ed1df1db718157bbfed740d2e160/linux/x64/cursor-reh-linux-x64.tar.gz"

    headers = {
        "User-Agent": "Cursor/2.6.13 (Windows; Remote-SSH)"
    }

    print(f"URL: {url}")
    print(f"Headers: {headers}")

    try:
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("\n✓ Download successful!")
            # Try to read first few bytes
            content = response.content[:100]
            print(f"First 100 bytes: {content}")
        else:
            print(f"\n✗ Download failed with status: {response.status_code}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    test_download()