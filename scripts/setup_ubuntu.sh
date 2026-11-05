#!/usr/bin/env bash
set -euo pipefail
# Convenience only. The supported environment is the staff-distributed CSC458 VM.
sudo apt-get update
sudo apt-get install -y \
  mininet openvswitch-switch iproute2 iputils-ping traceroute tcpdump iperf3 \
  python3 python3-venv python3-pip
sudo service openvswitch-switch start || true
echo "Testing Mininet..."
sudo mn --test pingall || true
echo "Now import your PA1 prefix_tools.py and run: sudo python3 tools/check_environment.py"
