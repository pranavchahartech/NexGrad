#!/usr/bin/env python3
"""
Nagios Diagnostic Helper
Validates local monitoring plugins and tests alerting pipeline
"""

import subprocess
import sys

PLUGINS = [
    ["python", "nagios/plugins/check_db_connectivity.py", "-H", "127.0.0.1"],
]

def run_diagnostics():
    print("Running NexGrad Diagnostic Checks...")
    all_ok = True
    for cmd in PLUGINS:
        print(f"Executing: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(f"  Return code: {res.returncode}")
            print(f"  Output: {res.stdout.strip()}")
            if res.returncode != 0:
                all_ok = False
        except Exception as e:
            print(f"  Failed: {e}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)

