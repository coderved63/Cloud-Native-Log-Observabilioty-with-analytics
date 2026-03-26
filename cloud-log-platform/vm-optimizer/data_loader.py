import os
import glob
import pandas as pd
import numpy as np


class BitbrainsDataLoader:
    """Loads and parses GWA Bitbrains VM trace files."""

    COLUMNS = [
        'timestamp', 'cpu_cores', 'cpu_capacity_mhz', 'cpu_usage_mhz',
        'memory_provisioned_kb', 'memory_usage_kb',
        'disk_io_throughput', 'network_io_throughput'
    ]

    def __init__(self, data_dir='/app/data'):
        self.data_dir = data_dir
        self.vm_data = {}
        self.combined_df = None
        self.vm_count = 0

    def load_all(self, max_vms=None):
        """Load all VM trace files from the data directory."""
        files = sorted(glob.glob(os.path.join(self.data_dir, '*.csv')) +
                        glob.glob(os.path.join(self.data_dir, '**/*.csv'), recursive=True))

        if not files:
            # Try tab-delimited txt files (Bitbrains original format)
            files = sorted(glob.glob(os.path.join(self.data_dir, '*.txt')) +
                            glob.glob(os.path.join(self.data_dir, '**/*.txt'), recursive=True))

        if max_vms:
            files = files[:max_vms]

        print(f"[data_loader] Found {len(files)} VM trace files")

        all_frames = []
        for filepath in files:
            vm_name = os.path.splitext(os.path.basename(filepath))[0]
            df = self._parse_file(filepath, vm_name)
            if df is not None and len(df) > 0:
                self.vm_data[vm_name] = df
                all_frames.append(df)

        self.vm_count = len(self.vm_data)

        if all_frames:
            self.combined_df = pd.concat(all_frames, ignore_index=True)
            print(f"[data_loader] Loaded {self.vm_count} VMs, {len(self.combined_df)} total rows")
        else:
            self.combined_df = pd.DataFrame(columns=self.COLUMNS + ['vm_name'])
            print("[data_loader] No VM data loaded")

        return self.combined_df

    def _parse_file(self, filepath, vm_name):
        """Parse a single Bitbrains trace file."""
        try:
            # Try semicolon+tab delimiter first (Bitbrains format)
            df = pd.read_csv(filepath, sep=';\t', header=None, engine='python')
            if df.shape[1] < 8:
                # Try just semicolon
                df = pd.read_csv(filepath, sep=';', header=None, engine='python')
            if df.shape[1] < 8:
                # Try comma
                df = pd.read_csv(filepath, sep=',', header=None, engine='python')

            # Handle files with more columns by taking first 8
            if df.shape[1] >= 8:
                df = df.iloc[:, :8]
                df.columns = self.COLUMNS
            else:
                return None

            # Convert timestamp from ms to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
            df['vm_name'] = vm_name

            # Convert numeric columns
            for col in self.COLUMNS[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Calculate utilization percentages
            df['cpu_utilization_pct'] = np.where(
                df['cpu_capacity_mhz'] > 0,
                (df['cpu_usage_mhz'] / df['cpu_capacity_mhz']) * 100,
                0
            )
            df['memory_utilization_pct'] = np.where(
                df['memory_provisioned_kb'] > 0,
                (df['memory_usage_kb'] / df['memory_provisioned_kb']) * 100,
                0
            )

            df.dropna(subset=['timestamp'], inplace=True)
            return df

        except Exception as e:
            print(f"[data_loader] Error parsing {filepath}: {e}")
            return None

    def get_vm_summary(self):
        """Get summary statistics for all VMs."""
        if self.combined_df is None or self.combined_df.empty:
            return {}

        summaries = []
        for vm_name, df in self.vm_data.items():
            summaries.append({
                'vm_name': vm_name,
                'cpu_cores': int(df['cpu_cores'].mode().iloc[0]) if len(df) > 0 else 0,
                'cpu_capacity_mhz': float(df['cpu_capacity_mhz'].mean()),
                'avg_cpu_usage_mhz': float(df['cpu_usage_mhz'].mean()),
                'avg_cpu_utilization': float(df['cpu_utilization_pct'].mean()),
                'max_cpu_utilization': float(df['cpu_utilization_pct'].max()),
                'avg_memory_provisioned_mb': float(df['memory_provisioned_kb'].mean() / 1024),
                'avg_memory_usage_mb': float(df['memory_usage_kb'].mean() / 1024),
                'avg_memory_utilization': float(df['memory_utilization_pct'].mean()),
                'max_memory_utilization': float(df['memory_utilization_pct'].max()),
                'avg_disk_io': float(df['disk_io_throughput'].mean()),
                'avg_network_io': float(df['network_io_throughput'].mean()),
                'data_points': len(df),
            })

        return summaries

    def get_latest_snapshot(self):
        """Get the most recent data point for each VM."""
        if self.combined_df is None or self.combined_df.empty:
            return pd.DataFrame()

        return self.combined_df.sort_values('timestamp').groupby('vm_name').last().reset_index()
