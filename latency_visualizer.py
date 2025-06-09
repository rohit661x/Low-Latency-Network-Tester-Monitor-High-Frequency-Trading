#!/usr/bin/env python3

import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                           QLabel, QDesktopWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import warnings

warnings.filterwarnings('ignore')

class BaseMonitorWindow(QMainWindow):
    def __init__(self, title, x_offset=0, y_offset=0):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100 + x_offset, 100 + y_offset, 800, 400)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        self.log_file = "logs/hft_latency.log"
        self.window_size = timedelta(seconds=10)
        self.update_interval = 50
        self.microburst_threshold = 0.5

    def load_data(self):
        try:
            df = pd.read_csv(self.log_file)
            if df.empty:
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.loc[df['status'] == 'failed', 'rtt'] = np.nan
            df['rtt'] = pd.to_numeric(df['rtt'], errors='coerce')
            df['interface_drops'] = pd.to_numeric(df['interface_drops'], errors='coerce')
            df['interface_errors'] = pd.to_numeric(df['interface_errors'], errors='coerce')
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

class LatencyMonitor(BaseMonitorWindow):
    def __init__(self):
        super().__init__('Network Latency Monitor', x_offset=0)
        self.ax.set_title('Network Latency (ms)')
        self.ax.set_ylabel('RTT (ms)')
        self.ax.grid(True, alpha=0.3)
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=self.update_interval)

    def update_plot(self, frame):
        df = self.load_data()
        if df.empty:
            return

        current_time = df['timestamp'].max()
        if pd.isnull(current_time):
            return
            
        start_time = current_time - self.window_size
        mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= current_time)
        df_window = df.loc[mask].copy()

        if df_window.empty:
            return

        self.ax.clear()
        valid_data = df_window[df_window['rtt'].notna()]
        
        if not valid_data.empty:
            self.ax.plot(valid_data['timestamp'], valid_data['rtt'], 
                        label='Latency', color='blue', linewidth=1)
            percentile_99 = valid_data['rtt'].quantile(0.99)
            self.ax.axhline(y=percentile_99, color='r', linestyle='--', 
                          label=f'99th Percentile ({percentile_99:.2f}ms)')

        self.ax.set_title('Network Latency (ms)')
        self.ax.set_ylabel('RTT (ms)')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        self.ax.set_ylim(bottom=0)
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()

class InterfaceStatsMonitor(BaseMonitorWindow):
    def __init__(self):
        super().__init__('Interface Statistics Monitor', x_offset=850)
        self.ax.set_title('Interface Statistics')
        self.ax.set_ylabel('Count')
        self.ax.grid(True, alpha=0.3)
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=self.update_interval)

    def update_plot(self, frame):
        df = self.load_data()
        if df.empty:
            return

        current_time = df['timestamp'].max()
        if pd.isnull(current_time):
            return
            
        start_time = current_time - self.window_size
        mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= current_time)
        df_window = df.loc[mask].copy()

        if df_window.empty:
            return

        self.ax.clear()
        df_window['drops_smooth'] = df_window['interface_drops'].rolling(window=5, min_periods=1).mean()
        df_window['errors_smooth'] = df_window['interface_errors'].rolling(window=5, min_periods=1).mean()
        
        self.ax.plot(df_window['timestamp'], df_window['drops_smooth'],
                    label='Drops', color='red', linewidth=1)
        self.ax.plot(df_window['timestamp'], df_window['errors_smooth'],
                    label='Errors', color='orange', linewidth=1)

        self.ax.set_title('Interface Statistics')
        self.ax.set_ylabel('Count')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()

class MicroburstMonitor(BaseMonitorWindow):
    def __init__(self):
        super().__init__('Microburst Detection Monitor', y_offset=450)
        self.ax.set_title('Microburst Detection')
        self.ax.set_ylabel('RTT Variation (ms)')
        self.ax.grid(True, alpha=0.3)
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=self.update_interval)

    def detect_microbursts(self, df):
        if df.empty:
            return pd.DataFrame()
        
        df['rtt_diff'] = df['rtt'].diff()
        df.loc[df['rtt_diff'].abs() > 100, 'rtt_diff'] = np.nan
        microbursts = df[abs(df['rtt_diff']) > self.microburst_threshold].copy()
        return microbursts

    def update_plot(self, frame):
        df = self.load_data()
        if df.empty:
            return

        current_time = df['timestamp'].max()
        if pd.isnull(current_time):
            return
            
        start_time = current_time - self.window_size
        mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= current_time)
        df_window = df.loc[mask].copy()

        if df_window.empty:
            return

        self.ax.clear()
        df_window['rtt_diff'] = df_window['rtt'].diff()
        valid_diff = df_window[df_window['rtt_diff'].notna()]
        
        if not valid_diff.empty:
            self.ax.plot(valid_diff['timestamp'], valid_diff['rtt_diff'],
                        label='RTT Variation', color='green', linewidth=1)
            
            microbursts = self.detect_microbursts(valid_diff)
            if not microbursts.empty:
                self.ax.scatter(microbursts['timestamp'], microbursts['rtt_diff'],
                              color='red', label='Microbursts', zorder=5)

        self.ax.set_title('Microburst Detection')
        self.ax.set_ylabel('RTT Variation (ms)')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        self.ax.set_ylim(-5, 5)
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()

class StatsDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Network Statistics Dashboard')
        self.setGeometry(850, 450, 800, 200)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.stats_labels = []
        for _ in range(5):
            label = QLabel()
            label.setStyleSheet("QLabel { font-size: 14pt; padding: 5px; }")
            layout.addWidget(label)
            self.stats_labels.append(label)

        self.log_file = "logs/hft_latency.log"
        self.window_size = timedelta(seconds=10)
        self.update_interval = 50
        self.microburst_threshold = 0.5

        # Start update timer
        self.timer = self.startTimer(self.update_interval)

    def load_data(self):
        try:
            return pd.read_csv(self.log_file)
        except Exception:
            return pd.DataFrame()

    def calculate_stats(self, df):
        if df.empty:
            return {}

        valid_pings = df[
            (df['status'] == 'success') & 
            (df['rtt'].notna()) &
            (df['rtt'] < 1000) & 
            (df['rtt'] > 0)
        ]

        if valid_pings.empty:
            return {}

        stats = {
            'avg_latency': valid_pings['rtt'].mean(),
            'min_latency': valid_pings['rtt'].min(),
            'max_latency': valid_pings['rtt'].max(),
            'jitter': valid_pings['rtt'].std(),
            'packet_loss': (1 - len(valid_pings) / len(df)) * 100,
            '99th_percentile': valid_pings['rtt'].quantile(0.99),
            'interface_drops': df['interface_drops'].iloc[-1],
            'interface_errors': df['interface_errors'].iloc[-1]
        }
        return stats

    def timerEvent(self, event):
        df = self.load_data()
        if df.empty:
            return

        stats = self.calculate_stats(df)
        if not stats:
            return

        self.stats_labels[0].setText(f"Average Latency: {stats['avg_latency']:.2f} ms")
        self.stats_labels[1].setText(f"Min/Max Latency: {stats['min_latency']:.2f}/{stats['max_latency']:.2f} ms")
        self.stats_labels[2].setText(f"Jitter: {stats['jitter']:.2f} ms")
        self.stats_labels[3].setText(f"Packet Loss: {stats['packet_loss']:.1f}%")
        self.stats_labels[4].setText(f"Interface Drops/Errors: {stats['interface_drops']}/{stats['interface_errors']}")

def main():
    app = QApplication(sys.argv)
    
    # Create all monitor windows
    latency_monitor = LatencyMonitor()
    interface_monitor = InterfaceStatsMonitor()
    microburst_monitor = MicroburstMonitor()
    stats_dashboard = StatsDashboard()
    
    # Show all windows
    latency_monitor.show()
    interface_monitor.show()
    microburst_monitor.show()
    stats_dashboard.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 