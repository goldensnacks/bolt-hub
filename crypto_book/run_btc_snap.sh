#!/bin/bash

# Make sure we're in the correct directory
cd "$(dirname "$0")"

echo "Starting BTC snap script in a loop (30 second intervals)..."
echo "Press Ctrl+C to stop"

while true; do
    echo "Running BTC snap at $(date)"
    python3 btc_snap.py
    sleep 30
done 