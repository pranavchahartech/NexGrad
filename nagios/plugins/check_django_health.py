#!/usr/bin/env python3
"""
Nagios Check Plugin: Verify Django Backend HTTP Health Status
Exit Codes: 0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN
"""

import sys
import argparse
import urllib.request
import urllib.error
import time

def main():
    parser = argparse.ArgumentParser(description="Nagios check for Django Backend health")
    parser.add_argument("-H", "--host", required=True, help="Target host address")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Target port")
    parser.add_argument("-u", "--uri", default="/healthz", help="Health check URI")
    parser.add_argument("-w", "--warning", type=float, default=1.5, help="Warning latency (seconds)")
    parser.add_argument("-c", "--critical", type=float, default=3.0, help="Critical latency (seconds)")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}{args.uri}"
    start_time = time.time()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Nagios-Check-Django"})
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            elapsed = time.time() - start_time

            if status_code == 200:
                if elapsed >= args.critical:
                    print(f"CRITICAL - Django Backend response latency high: {elapsed:.3f}s | time={elapsed:.3f}s")
                    sys.exit(2)
                elif elapsed >= args.warning:
                    print(f"WARNING - Django Backend response latency: {elapsed:.3f}s | time={elapsed:.3f}s")
                    sys.exit(1)
                else:
                    print(f"OK - Django Backend healthy (HTTP 200 in {elapsed:.3f}s) | time={elapsed:.3f}s")
                    sys.exit(0)
            else:
                print(f"WARNING - Django Backend returned HTTP {status_code} | time={elapsed:.3f}s")
                sys.exit(1)

    except urllib.error.HTTPError as e:
        print(f"CRITICAL - Django Backend HTTP error: {e.code} {e.reason}")
        sys.exit(2)
    except Exception as e:
        print(f"CRITICAL - Django Backend unreachable at {url}: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()

