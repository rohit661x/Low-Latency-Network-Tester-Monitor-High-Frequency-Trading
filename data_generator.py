#!/usr/bin/env python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def generate_synthetic_data(duration_seconds=60, sample_rate_hz=10):
    """Generate synthetic network latency data."""
    # Generate timestamps
    num_samples = duration_seconds * sample_rate_hz
    timestamps = [datetime.now() + timedelta(seconds=i/sample_rate_hz) for i in range(num_samples)]
    
    # Generate base RTT with some natural variation (normal distribution)
    base_rtt = np.random.normal(10, 2, num_samples)  # Mean 10ms, std 2ms
    
    # Add occasional spikes (microbursts)
    microburst_mask = np.random.random(num_samples) < 0.05  # 5% chance of microburst
    base_rtt[microburst_mask] += np.random.uniform(5, 15, np.sum(microburst_mask))
    
    # Ensure RTT is positive
    base_rtt = np.maximum(base_rtt, 0.1)
    
    # Generate interface statistics with gradual increases and occasional resets
    drops = np.zeros(num_samples)
    errors = np.zeros(num_samples)
    
    # Simulate accumulating drops and errors
    for i in range(1, num_samples):
        drops[i] = drops[i-1] + np.random.poisson(0.1)  # Average 0.1 new drops per sample
        errors[i] = errors[i-1] + np.random.poisson(0.05)  # Average 0.05 new errors per sample
        
        # Occasional resets (simulating interface resets or counter rollovers)
        if np.random.random() < 0.01:  # 1% chance of reset
            drops[i] = 0
            errors[i] = 0
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'rtt': base_rtt,
        'interface_drops': drops,
        'interface_errors': errors,
        'status': ['success' if r > 0 else 'failed' for r in base_rtt]
    })
    
    return df

def plot_network_stats(df):
    """Plot network statistics in three subplots."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8))
    fig.suptitle('Network Latency Monitoring')
    
    # Plot 1: Network Latency
    ax1.plot(df['timestamp'], df['rtt'], label='RTT', color='blue', linewidth=1)
    percentile_99 = df['rtt'].quantile(0.99)
    ax1.axhline(y=percentile_99, color='red', linestyle='--', 
                label=f'99th Percentile ({percentile_99:.2f}ms)')
    ax1.set_title('Network Latency')
    ax1.set_ylabel('RTT (ms)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Interface Statistics
    ax2.plot(df['timestamp'], df['interface_drops'], 
             label='Drops', color='red', linewidth=1)
    ax2.plot(df['timestamp'], df['interface_errors'], 
             label='Errors', color='orange', linewidth=1)
    ax2.set_title('Interface Statistics')
    ax2.set_ylabel('Count')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Microburst Detection
    df['rtt_diff'] = df['rtt'].diff()
    ax3.plot(df['timestamp'], df['rtt_diff'], 
             label='RTT Variation', color='green', linewidth=1)
    
    # Highlight microbursts
    threshold = 2.0  # ms
    microbursts = df[abs(df['rtt_diff']) > threshold]
    if not microbursts.empty:
        ax3.scatter(microbursts['timestamp'], microbursts['rtt_diff'],
                   color='red', label='Microbursts', zorder=5)
    
    ax3.set_title('Microburst Detection')
    ax3.set_ylabel('RTT Variation (ms)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Adjust layout and display
    plt.tight_layout()
    plt.show()

def main():
    # Generate synthetic data
    print("Generating synthetic network data...")
    df = generate_synthetic_data(duration_seconds=60, sample_rate_hz=10)
    
    # Save to CSV
    df.to_csv('logs/hft_latency.log', index=False)
    print("Data saved to logs/hft_latency.log")
    
    # Plot the data
    print("Plotting network statistics...")
    plot_network_stats(df)

if __name__ == '__main__':
    main() 