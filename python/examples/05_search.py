"""
Episode 2/3 (v2): Search for objects by keyword.

Original v1 equivalent: Episodes/Episode2/4-SimpleSearch-REST.py
  - v1 used searchByObjectTypes and searchByCategory
  - v2 uses a unified /search endpoint with filters
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS")
if not BAM_PASS:
    print("Set BAM_PASS environment variable.")
    sys.exit(1)

with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
    # Search for IP addresses matching a pattern
    print("=== Search: IP addresses matching '192.168.2' ===")
    results = bam.search("192.168.2", object_types="IP4Address")
    for item in results.get("data", []):
        print(f"  {item}")

    # Search for a server by name
    print("\n=== Search: 'bdds1' across all types ===")
    results = bam.search("bdds1")
    for item in results.get("data", []):
        print(f"  [{item.get('type')}] {item.get('name', 'unnamed')} (id={item['id']})")
