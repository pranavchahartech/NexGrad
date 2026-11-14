#!/bin/bash
# ==============================================================================
# Nagios Event Handler: Self-Healing Remediation for NexGrad Backend Failure
# Arguments:
# $1 = Service State (OK, WARNING, UNKNOWN, CRITICAL)
# $2 = State Type (SOFT or HARD)
# $3 = Current Attempt
# $4 = Host Address
# ==============================================================================

SERVICE_STATE=$1
STATE_TYPE=$2
SERVICE_ATTEMPT=$3
HOST_ADDRESS=$4
LOG_FILE="/var/log/nexgrad/self-healing.log"

mkdir -p /var/log/nexgrad
echo "$(date '+%Y-%m-%d %H:%M:%S') [EVENT_HANDLER] Backend check on $HOST_ADDRESS is in state $SERVICE_STATE ($STATE_TYPE, attempt $SERVICE_ATTEMPT)" >> "$LOG_FILE"

case "$SERVICE_STATE" in
    CRITICAL)
        case "$STATE_TYPE" in
            SOFT)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] Soft critical state. Proactively restarting nexgrad-backend service..." >> "$LOG_FILE"
                systemctl restart nexgrad-backend
                ;;
            HARD)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] Hard critical state! Triggering full automated Ansible remediation playbook..." >> "$LOG_FILE"
                ansible-playbook -i /opt/nexgrad/ansible/inventory/hosts.ini /opt/nexgrad/ansible/playbooks/self_healing.yml --extra-vars "target_host=$HOST_ADDRESS failed_service=nexgrad-backend check_port=8000" >> "$LOG_FILE" 2>&1
                ;;
        esac
        ;;
    OK)
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SELF_HEALING] Backend service on $HOST_ADDRESS has recovered and is healthy." >> "$LOG_FILE"
        ;;
esac

exit 0

