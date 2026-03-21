#!/usr/bin/env python3
"""
Test Azure blob storage URL
"""

import requests

def test_azure():
    print("=== Testing Azure Blob Storage URL ===")

    # Try the old Azure URL format
    url = "https://cursor.blob.core.windows.net/remote-releases/61e99179e4080fecf9d8b92c6e2e3e00fbfb53f0/cli-alpine-x64.tar.gz"

    headers = {
        "User-Agent": "Cursor/2.6.13 (Windows; Remote-SSH)"
    }

    print(f"URL: {url}")

    try:
        response = requests.head(url, timeout=30, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("\n✓ Azure URL works!")
        else:
            print(f"\n✗ Azure URL failed with status: {response.status_code}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    test_azure()