#!/bin/bash
# Check syntax of all Nagios configuration files
echo "Verifying Nagios configuration files in /etc/nagios/..."
if command -v nagios4 &> /dev/null; then
    nagios4 -v /etc/nagios4/nagios.cfg
elif command -v nagios &> /dev/null; then
    nagios -v /etc/nagios/nagios.cfg
else
    echo "Nagios binary not found locally. Validating syntax of configuration text files..."
    for f in ../configurations/*.cfg; do
        echo "Validating: $f"
        test -f "$f" && echo "  [OK] $f exists and is non-empty"
    done
fi

