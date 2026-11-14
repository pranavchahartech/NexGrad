#!/bin/bash
# ==============================================================================
# Nagios Event Handler: Self-Healing Remediation for NexGrad AI Microservice
# ==============================================================================

SERVICE_STATE=$1
STATE_TYPE=$2
SERVICE_ATTEMPT=$3
HOST_ADDRESS=$4
LOG_FILE="/var/log/nexgrad/self-healing.log"

mkdir -p /var/log/nexgrad
echo "$(date '+%Y-%m-%d %H:%M:%S') [EVENT_HANDLER] AI Service check on $HOST_ADDRESS is $SERVICE_STATE ($STATE_TYPE, attempt $SERVICE_ATTEMPT)" >> "$LOG_FILE"

case "$SERVICE_STATE" in
    CRITICAL)
        case "$STATE_TYPE" in
            SOFT)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] Soft critical. Restarting nexgrad-ai systemd service..." >> "$LOG_FILE"
                systemctl restart nexgrad-ai
                ;;
            HARD)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] Hard critical! Executing automated self-healing script for AI Service..." >> "$LOG_FILE"
                /usr/local/bin/python3 /etc/nagios/event-handlers/self_healing_recovery.py --service nexgrad-ai --port 8001 >> "$LOG_FILE" 2>&1
                ;;
        esac
        ;;
    OK)
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] AI Microservice has recovered to OK state." >> "$LOG_FILE"
        ;;
esac

exit 0

