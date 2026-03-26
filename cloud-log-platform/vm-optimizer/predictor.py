import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


class VMPredictor:
    """Predicts future CPU and memory usage per VM using Linear Regression."""

    def __init__(self):
        self.predictions = {}

    def predict_all(self, vm_data, top_n=20):
        """Run predictions for top N most active VMs."""
        self.predictions = {}

        # Sort VMs by data points (most data = most interesting)
        sorted_vms = sorted(vm_data.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]

        results = []
        for vm_name, df in sorted_vms:
            pred = self._predict_vm(vm_name, df)
            if pred:
                results.append(pred)

        self.predictions = results
        return results

    def _predict_vm(self, vm_name, df):
        """Predict CPU and memory for a single VM."""
        if len(df) < 10:
            return None

        # Use last 100 data points for prediction
        recent = df.tail(100).copy()
        recent = recent.reset_index(drop=True)

        X = np.arange(len(recent)).reshape(-1, 1)

        predictions = {}
        for metric, col in [('cpu', 'cpu_usage_mhz'), ('memory', 'memory_usage_kb')]:
            y = recent[col].values

            model = LinearRegression()
            model.fit(X, y)

            # Predict next 12 intervals (1 hour at 5-min intervals)
            future_X = np.arange(len(recent), len(recent) + 12).reshape(-1, 1)
            future_y = model.predict(future_X)
            future_y = np.maximum(future_y, 0)  # no negative values

            slope = float(model.coef_[0])
            r2 = float(model.score(X, y))

            if slope > 0.5:
                trend = 'increasing'
            elif slope < -0.5:
                trend = 'decreasing'
            else:
                trend = 'stable'

            predictions[metric] = {
                'current_avg': round(float(np.mean(y[-12:])), 2),
                'predicted_avg': round(float(np.mean(future_y)), 2),
                'predicted_max': round(float(np.max(future_y)), 2),
                'trend': trend,
                'slope': round(slope, 4),
                'confidence': round(max(0, r2), 3),
            }

        # Capacity info
        cpu_cap = float(recent['cpu_capacity_mhz'].mean())
        mem_cap = float(recent['memory_provisioned_kb'].mean())

        cpu_predicted_util = (predictions['cpu']['predicted_avg'] / cpu_cap * 100) if cpu_cap > 0 else 0
        mem_predicted_util = (predictions['memory']['predicted_avg'] / mem_cap * 100) if mem_cap > 0 else 0

        # Risk assessment
        if cpu_predicted_util > 90 or mem_predicted_util > 90:
            risk = 'HIGH'
        elif cpu_predicted_util > 70 or mem_predicted_util > 70:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'

        return {
            'vm_name': vm_name,
            'cpu_prediction': predictions['cpu'],
            'memory_prediction': predictions['memory'],
            'predicted_cpu_utilization': round(cpu_predicted_util, 1),
            'predicted_memory_utilization': round(mem_predicted_util, 1),
            'risk_level': risk,
        }
