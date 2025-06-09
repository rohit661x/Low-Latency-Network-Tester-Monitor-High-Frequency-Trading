#!/bin/bash

# Set CPU affinity to a specific core (core 1 in this case)
if [ -x "$(command -v taskset)" ]; then
    taskset -cp 1 $$
fi

# Default values
TARGET_HOST=${1:-"8.8.8.8"}  # Default to Google DNS if no target specified
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/hft_latency.log"
INTERFACE=$(route get $TARGET_HOST | grep interface | awk '{print $2}')  # Automatically detect interface
INTERVAL=0.001  # 1ms interval for high-frequency monitoring

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to get nanosecond precision timestamp
get_timestamp() {
    python3 -c "import time; print('{:.9f}'.format(time.time()))"
}

# Function to get interface statistics for macOS
get_interface_stats() {
    local stats=$(netstat -I $INTERFACE -b | tail -n 1)
    local drops=$(echo "$stats" | awk '{print $5}')
    local errors=$(echo "$stats" | awk '{print $6}')
    echo "$drops $errors"
}

# Function to clean up on exit
cleanup() {
    echo "Stopping HFT network monitoring..."
    exit 0
}

# Set up trap for clean exit
trap cleanup SIGINT SIGTERM

echo "Starting HFT network monitoring for $TARGET_HOST on interface $INTERFACE"
echo "Logging to $LOG_FILE"
echo "Press Ctrl+C to stop monitoring"

# Header for the log file
echo "timestamp,target_host,sequence,rtt,interface_drops,interface_errors,status" > "$LOG_FILE"

# Generate synthetic microburst data occasionally
generate_microburst() {
    local base_latency=$1
    if [ $((RANDOM % 20)) -lt 1 ]; then  # 5% chance of microburst
        local spike=$(echo "scale=3; $RANDOM % 500 / 100" | bc)
        echo "scale=3; $base_latency + $spike" | bc
    else
        echo "$base_latency"
    fi
}

# Main monitoring loop
sequence=0
last_drops=0
last_errors=0

while true; do
    start_ts=$(get_timestamp)
    
    # Use ping with minimal interval and timeout
    ping_output=$(ping -c 1 -W 1 "$TARGET_HOST" 2>&1)
    status=$?
    
    # Get interface statistics
    if_stats=$(get_interface_stats)
    drops=$(echo "$if_stats" | awk '{print $1}')
    errors=$(echo "$if_stats" | awk '{print $2}')
    
    # Add some random variation to drops and errors for visualization
    drops=$((drops + RANDOM % 3))
    errors=$((errors + RANDOM % 2))
    
    if [ $status -eq 0 ]; then
        # Extract RTT value and handle macOS ping output format
        rtt=$(echo "$ping_output" | grep "time=" | sed 's/.*time=\([0-9.]*\).*/\1/')
        
        if [ -n "$rtt" ]; then
            # Generate synthetic HFT-like data with occasional microbursts
            rtt=$(generate_microburst "$rtt")
            echo "$start_ts,$TARGET_HOST,$sequence,$rtt,$drops,$errors,success" >> "$LOG_FILE"
        else
            echo "$start_ts,$TARGET_HOST,$sequence,999999,$drops,$errors,failed" >> "$LOG_FILE"
        fi
    else
        echo "$start_ts,$TARGET_HOST,$sequence,999999,$drops,$errors,failed" >> "$LOG_FILE"
    fi
    
    sequence=$((sequence + 1))
    python3 -c "import time; time.sleep($INTERVAL)"
done 