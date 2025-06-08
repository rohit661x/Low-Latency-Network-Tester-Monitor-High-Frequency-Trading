#!/usr/bin/env python3

import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import warnings

warnings.filterwarnings('ignore')

class LatencyMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Network Latency Monitor')
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create figure and canvas
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Initialize data
        self.log_file = "logs/network_latency.log"
        self.window_size = timedelta(minutes=5)  # Show last 5 minutes
        self.update_interval = 1000  # Update every 1 second

        # Setup plots
        self.setup_plots()
        
        # Start animation
        self.anim = FuncAnimation(self.fig, self.update_plot, 
                                interval=self.update_interval)

    def setup_plots(self):
        # Latency plot
        self.ax1.set_title('Network Latency')
        self.ax1.set_ylabel('RTT (ms)')
        self.ax1.grid(True)

        # Statistics plot
        self.ax2.set_title('Latency Statistics')
        self.ax2.set_ylabel('Value (ms)')
        self.ax2.grid(True)

        self.fig.tight_layout()

    def load_data(self):
        try:
            df = pd.read_csv(self.log_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

    def calculate_statistics(self, df):
        if df.empty:
            return {}

        successful_pings = df[df['status'] == 'success']
        if successful_pings.empty:
            return {}

        stats = {
            'avg': successful_pings['rtt'].mean(),
            'max': successful_pings['rtt'].max(),
            'min': successful_pings['rtt'].min(),
            'jitter': successful_pings['rtt'].std(),
            'loss_rate': (1 - len(successful_pings) / len(df)) * 100
        }
        return stats

    def update_plot(self, frame):
        df = self.load_data()
        if df.empty:
            return

        current_time = datetime.now()
        start_time = current_time - self.window_size
        
        # Filter data for the current window
        mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= current_time)
        df_window = df.loc[mask]

        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()

        # Plot latency
        successful = df_window[df_window['status'] == 'success']
        failed = df_window[df_window['status'] == 'failed']

        if not successful.empty:
            self.ax1.plot(successful['timestamp'], successful['rtt'], 
                         label='Successful', color='green', marker='.')
        if not failed.empty:
            self.ax1.scatter(failed['timestamp'], 
                           [0] * len(failed), color='red', 
                           marker='x', label='Failed')

        # Calculate and plot statistics
        stats = self.calculate_statistics(df_window)
        if stats:
            metrics = ['avg', 'max', 'min', 'jitter']
            values = [stats[m] for m in metrics]
            self.ax2.bar(metrics, values, color=['blue', 'red', 'green', 'purple'])
            self.ax2.text(0.02, 0.95, f"Packet Loss: {stats['loss_rate']:.2f}%",
                         transform=self.ax2.transAxes)

        # Format plots
        self.ax1.set_title('Network Latency')
        self.ax1.set_ylabel('RTT (ms)')
        self.ax1.grid(True)
        self.ax1.legend()

        self.ax2.set_title('Latency Statistics')
        self.ax2.set_ylabel('Value (ms)')
        self.ax2.grid(True)

        # Rotate x-axis labels for better readability
        plt.setp(self.ax1.xaxis.get_majorticklabels(), rotation=45)
        self.fig.tight_layout()

def main():
    app = QApplication(sys.argv)
    monitor = LatencyMonitor()
    monitor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 