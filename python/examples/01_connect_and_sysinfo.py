"""
Episode 1 (v2): Connect to BAM and get system info.

Original v1 equivalent: Episodes/Episode1/1-firstscript-REST.py
  - v1 used: GET /Services/REST/v1/login?username=...&password=...
  - v1 parsed token from string: "Session Token-> BAMAuthToken: ..."
  - v2 uses: POST /api/v2/sessions with JSON body
  - v2 returns a proper JSON response with apiToken
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
    # Get system info
    info = bam.get_system_info()
    print("=== System Info ===")
    for key, val in info.items():
        print(f"  {key}: {val}")

    # List configurations
    configs = bam.get_configurations()
    print("\n=== Configurations ===")
    for cfg in configs.get("data", []):
        print(f"  [{cfg['id']}] {cfg['name']}")
