#!/usr/bin/env python3
"""
Nagios Check Plugin: Verify NexGrad AI Microservice Health & Gemini Connectivity
Exit Codes: 0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN
"""

import sys
import argparse
import urllib.request
import json
import time

def main():
    parser = argparse.ArgumentParser(description="Nagios check for AI Microservice")
    parser.add_argument("-H", "--host", required=True, help="Target host address")
    parser.add_argument("-p", "--port", type=int, default=8001, help="AI service port")
    parser.add_argument("-u", "--uri", default="/health", help="Health check URI")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}{args.uri}"
    start = time.time()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Nagios-Check-AI"})
        with urllib.request.urlopen(req, timeout=5) as response:
            elapsed = time.time() - start
            data = json.loads(response.read().decode())
            if response.getcode() == 200 and data.get("status") == "healthy":
                print(f"OK - NexGrad AI Service operational (Model: {data.get('model', 'gemini')}) in {elapsed:.3f}s | time={elapsed:.3f}s")
                sys.exit(0)
            else:
                print(f"WARNING - AI Service abnormal payload: {data}")
                sys.exit(1)
    except Exception as e:
        print(f"CRITICAL - AI Microservice failure: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()

