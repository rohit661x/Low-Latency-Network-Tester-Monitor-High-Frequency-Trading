#!/bin/bash

# Default values
TARGET_HOST=${1:-"8.8.8.8"}  # Default to Google DNS if no target specified
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/network_latency.log"
INTERVAL=1  # Interval between pings in seconds

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to get high precision timestamp
get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S.%N"
}

# Function to clean up on exit
cleanup() {
    echo "Stopping network monitoring..."
    exit 0
}

# Set up trap for clean exit
trap cleanup SIGINT SIGTERM

echo "Starting network monitoring for $TARGET_HOST"
echo "Logging to $LOG_FILE"
echo "Press Ctrl+C to stop monitoring"

# Header for the log file
echo "timestamp,target_host,sequence,rtt,status" > "$LOG_FILE"

# Main monitoring loop
while true; do
    # Use ping with deadline to ensure it doesn't hang
    ping_output=$(ping -c 1 -W 1 "$TARGET_HOST" 2>&1)
    timestamp=$(get_timestamp)
    
    if [[ $? -eq 0 ]]; then
        # Extract RTT value
        rtt=$(echo "$ping_output" | grep -oP 'time=\K[0-9.]+')
        seq_num=$(echo "$ping_output" | grep -oP 'icmp_seq=\K[0-9]+')
        echo "$timestamp,$TARGET_HOST,$seq_num,$rtt,success" >> "$LOG_FILE"
    else
        # Log failure
        echo "$timestamp,$TARGET_HOST,0,0.0,failed" >> "$LOG_FILE"
    fi
    
    sleep $INTERVAL
done 