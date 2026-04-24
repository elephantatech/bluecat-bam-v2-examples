"""
Episode 1 (v2): Bulk add host records from a CSV file.

Original v1 equivalent: Episodes/Episode1/3-bulk-addhostrecords.py
  - v1 used the suds SOAP library
  - v2 uses simple REST POST calls
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bam_client import BAMClient

BAM_URL = os.environ.get("BAM_URL", "https://bam.lab.corp")
BAM_USER = os.environ.get("BAM_USER", "admin")
BAM_PASS = os.environ.get("BAM_PASS")

CSV_FILE = os.environ.get("CSV_FILE", "printers.csv")
CONFIG_NAME = "main"
VIEW_NAME = "default"
ZONE_NAME = "lab.corp"

# CSV format (with header row):
#   ip,hostname
#   192.168.1.10,printer-1f
#   192.168.1.11,printer-2f


def load_records(csv_path: str) -> list[tuple[str, str]]:
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        return [(row["ip"].strip(), row["hostname"].strip()) for row in reader]


def main():
    if not BAM_PASS:
        print("Set BAM_PASS environment variable.")
        sys.exit(1)

    if not os.path.exists(CSV_FILE):
        print(f"CSV file not found: {CSV_FILE}")
        print("Expected format (with header row):")
        print("  ip,hostname")
        print("  192.168.1.10,printer-1f")
        print("  192.168.1.11,printer-2f")
        sys.exit(1)

    records = load_records(CSV_FILE)
    print(f"Loaded {len(records)} records from {CSV_FILE}")

    with BAMClient(BAM_URL, BAM_USER, BAM_PASS, verify_ssl=False) as bam:
        config = bam.find_configuration(CONFIG_NAME)
        view = bam.find_view(config["id"], VIEW_NAME)
        zones = bam.get_zones(view["id"])
        zone = next(
            (z for z in zones.get("data", []) if z["name"] == ZONE_NAME),
            None,
        )
        if not zone:
            print(f"Zone '{ZONE_NAME}' not found")
            sys.exit(1)

        created = 0
        failed = 0
        for ip, hostname in records:
            try:
                bam.create_host_record(zone["id"], hostname, ip, reverse=True)
                created += 1
                print(f"  Created: {hostname}.{ZONE_NAME} -> {ip}")
            except Exception as e:
                failed += 1
                print(f"  FAILED: {hostname}.{ZONE_NAME} -> {ip}: {e}")

        print(f"\nDone. Created {created}, failed {failed}.")


if __name__ == "__main__":
    main()
