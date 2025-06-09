#!/usr/bin/env python3

import os
import time
import pandas as pd
from datetime import datetime, timedelta
import logging
import subprocess

class LatencyAlertMonitor:
    def __init__(self, log_file="logs/network_latency.log",
                 alert_thresholds={
                     'rtt': 100.0,  # ms
                     'jitter': 20.0,  # ms
                     'loss_rate': 5.0  # percent
                 },
                 window_size=300):  # 5 minutes in seconds
        
        self.log_file = log_file
        self.alert_thresholds = alert_thresholds
        self.window_size = window_size
        
        # Setup logging
        logging.basicConfig(
            filename='logs/alerts.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize state
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between repeated alerts
        
    def send_notification(self, message):
        """Send desktop notification and log alert"""
        logging.info(message)
        
        # Send desktop notification
        try:
            # For macOS
            subprocess.run(['osascript', '-e', f'display notification "{message}" with title "Network Alert"'])
        except Exception as e:
            logging.error(f"Failed to send desktop notification: {e}")
    
    def check_thresholds(self, stats):
        """Check if any metrics exceed their thresholds"""
        current_time = time.time()
        
        # Check RTT
        if stats['avg'] > self.alert_thresholds['rtt']:
            if 'rtt' not in self.last_alert_time or \
               (current_time - self.last_alert_time['rtt']) > self.alert_cooldown:
                self.send_notification(
                    f"High latency detected: {stats['avg']:.2f}ms "
                    f"(threshold: {self.alert_thresholds['rtt']}ms)")
                self.last_alert_time['rtt'] = current_time
        
        # Check jitter
        if stats['jitter'] > self.alert_thresholds['jitter']:
            if 'jitter' not in self.last_alert_time or \
               (current_time - self.last_alert_time['jitter']) > self.alert_cooldown:
                self.send_notification(
                    f"High jitter detected: {stats['jitter']:.2f}ms "
                    f"(threshold: {self.alert_thresholds['jitter']}ms)")
                self.last_alert_time['jitter'] = current_time
        
        # Check packet loss
        if stats['loss_rate'] > self.alert_thresholds['loss_rate']:
            if 'loss_rate' not in self.last_alert_time or \
               (current_time - self.last_alert_time['loss_rate']) > self.alert_cooldown:
                self.send_notification(
                    f"High packet loss detected: {stats['loss_rate']:.2f}% "
                    f"(threshold: {self.alert_thresholds['loss_rate']}%)")
                self.last_alert_time['loss_rate'] = current_time
    
    def calculate_statistics(self, df):
        """Calculate statistics from the data frame"""
        if df.empty:
            return None

        successful_pings = df[df['status'] == 'success']
        if successful_pings.empty:
            return None

        stats = {
            'avg': successful_pings['rtt'].mean(),
            'max': successful_pings['rtt'].max(),
            'min': successful_pings['rtt'].min(),
            'jitter': successful_pings['rtt'].std(),
            'loss_rate': (1 - len(successful_pings) / len(df)) * 100
        }
        return stats
    
    def monitor(self):
        """Main monitoring loop"""
        while True:
            try:
                # Read the log file
                if os.path.exists(self.log_file):
                    df = pd.read_csv(self.log_file)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Get data from the last window_size seconds
                    cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
                    recent_data = df[df['timestamp'] > cutoff_time]
                    
                    if not recent_data.empty:
                        stats = self.calculate_statistics(recent_data)
                        if stats:
                            self.check_thresholds(stats)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer if there's an error

def main():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize and start the monitor
    monitor = LatencyAlertMonitor()
    monitor.monitor()

if __name__ == '__main__':
    main() 