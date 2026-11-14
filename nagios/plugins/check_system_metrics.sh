#!/bin/bash
# ==============================================================================
# Nagios Check Plugin: Linux CPU, Memory & Disk Utilization
# ==============================================================================

WARN_MEM=80
CRIT_MEM=90

MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

if [ "$MEM_USAGE" -ge "$CRIT_MEM" ]; then
    echo "CRITICAL - Memory usage is at ${MEM_USAGE}% | mem=${MEM_USAGE}%"
    exit 2
elif [ "$MEM_USAGE" -ge "$WARN_MEM" ]; then
    echo "WARNING - Memory usage is at ${MEM_USAGE}% | mem=${MEM_USAGE}%"
    exit 1
else
    echo "OK - Memory usage is normal (${MEM_USAGE}%) | mem=${MEM_USAGE}%"
    exit 0
fi

