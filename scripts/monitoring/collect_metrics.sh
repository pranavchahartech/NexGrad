#!/bin/bash
# Collect runtime system performance metrics
echo "=== Host Resource Metrics ==="
date
echo "CPU Load:"
uptime
echo ""
echo "Memory Utilization:"
free -m
echo ""
echo "Disk Storage:"
df -h /

