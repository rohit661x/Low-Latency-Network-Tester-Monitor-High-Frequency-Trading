# Low-Latency Network Tester/Monitor

A lightweight diagnostics tool designed to measure and analyze network performance with a focus on latency-sensitive environments such as high-frequency trading (HFT).

## Features

- Real-time network latency monitoring using high-precision timestamps
- Continuous logging of round-trip times
- Real-time visualization of latency metrics
- Performance metrics calculation:
  - Average latency
  - Maximum latency
  - Jitter
  - Packet loss rate
- Alert system for latency threshold violations
- Matplotlib-based visualization

## Requirements

- Python 3.8+
- Required Python packages (see requirements.txt)
- Bash shell environment
- Linux/Unix-based operating system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/LowLatencyNetworkTester
cd LowLatencyNetworkTester
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the network monitoring:
```bash
./network_monitor.sh [target_host]
```

2. Launch the visualization tool:
```bash
python latency_visualizer.py
```

## Components

- `network_monitor.sh`: Bash script for continuous network latency monitoring
- `latency_visualizer.py`: Python script for real-time visualization and analysis
- `alert_module.py`: Optional module for latency threshold alerts

## Configuration

Default configuration can be modified in the Python scripts:
- Latency thresholds for alerts
- Visualization update frequency
- Log file location
- Target hosts for monitoring

## Output

The tool provides:
- Real-time latency graphs
- Statistical analysis of network performance
- Alert notifications for threshold violations
- Detailed log files for further analysis


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
