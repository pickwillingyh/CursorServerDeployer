#!/usr/bin/env python3
"""
List files in Azure blob storage
"""

import requests
import xml.etree.ElementTree as ET

def list_azure_files():
    print("=== Listing Azure Blob Storage Files ===")

    url = "https://cursor.blob.core.windows.net/remote-releases?restype=container&comp=list"

    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # Parse XML response
            root = ET.fromstring(response.content)

            # Find all blob names
            blobs = root.findall(".//BlobName")
            print(f"\nFound {len(blobs)} files:")

            for blob in blobs:
                name = blob.text
                if name.endswith('.tar.gz'):
                    print(f"  - {name}")
                else:
                    print(f"  - {name} (not a tar.gz)")
        else:
            print(f"Failed to list files: {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_azure_files()