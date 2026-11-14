#!/bin/bash
# ==============================================================================
# Nagios Installation and Setup Automation Script for Ubuntu / Debian
# ==============================================================================

set -e

echo "[+] Updating apt repositories..."
apt-get update -y

echo "[+] Installing Nagios Core, Plugins and NRPE..."
apt-get install -y nagios4 nagios-plugins-basic nagios-nrpe-plugin apache2 libapache2-mod-auth-digest

echo "[+] Linking NexGrad custom monitoring configurations..."
mkdir -p /etc/nagios4/nexgrad
cp -r /opt/nexgrad/nagios/configurations/* /etc/nagios4/nexgrad/
cp /opt/nexgrad/nagios/plugins/* /usr/lib/nagios/plugins/
chmod +x /usr/lib/nagios/plugins/check_*

echo "[+] Verifying Nagios configuration syntax..."
nagios4 -v /etc/nagios4/nagios.cfg

echo "[+] Restarting Nagios service..."
systemctl restart nagios4
systemctl enable nagios4

echo "[✓] Nagios monitoring initialized with active self-healing event handlers!"

