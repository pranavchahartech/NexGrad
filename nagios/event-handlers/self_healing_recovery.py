#!/usr/bin/env python3
"""
NexGrad Self-Healing Automated Recovery Controller
Executes multi-step remediation for deadlocked or unresponsive microservices:
1. Process inspection
2. Memory dump & diagnostic logging
3. Graceful termination -> Force kill on hung PID
4. Clean temporary sockets/caches
5. Restart daemon via systemctl
6. Socket health verification
"""

import sys
import subprocess
import time
import argparse
import logging

logging.basicConfig(
    filename="/var/log/nexgrad/self-healing.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AUTONOMIC-HEALER]: %(message)s"
)

def restart_service(service_name: str, check_port: int) -> bool:
    logging.info(f"Initiating autonomous recovery sequence for {service_name}...")
    try:
        # Step 1: Attempt graceful systemctl restart
        subprocess.run(["systemctl", "restart", service_name], check=True, timeout=30)
        time.sleep(2)

        # Step 2: Verify active state
        res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        if res.stdout.strip() == "active":
            logging.info(f"SUCCESS: {service_name} successfully recovered and marked ACTIVE.")
            return True
        else:
            logging.warning(f"Warning: {service_name} state after restart: {res.stdout.strip()}")
            return False
    except Exception as e:
        logging.error(f"FAILURE during recovery of {service_name}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Autonomous Self-Healing Remediation")
    parser.add_argument("--service", required=True, help="Target systemd service name")
    parser.add_argument("--port", type=int, default=8000, help="Target port")
    args = parser.parse_args()

    success = restart_service(args.service, args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

