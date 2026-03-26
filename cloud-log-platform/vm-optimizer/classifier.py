import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest


class VMClassifier:
    """Classifies VMs into workload types and detects anomalies."""

    WORKLOAD_LABELS = {
        0: 'cpu-intensive',
        1: 'memory-intensive',
        2: 'balanced',
        3: 'idle',
    }

    def __init__(self):
        self.clusters = {}
        self.anomalies = []

    def classify_workloads(self, vm_summaries):
        """Cluster VMs into workload types using KMeans."""
        if len(vm_summaries) < 4:
            return []

        # Build feature matrix
        features = []
        vm_names = []
        for s in vm_summaries:
            features.append([
                s['avg_cpu_utilization'],
                s['max_cpu_utilization'],
                s['avg_memory_utilization'],
                s['max_memory_utilization'],
                s['avg_disk_io'],
                s['avg_network_io'],
            ])
            vm_names.append(s['vm_name'])

        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # KMeans clustering
        n_clusters = min(4, len(vm_summaries))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # Determine cluster labels based on centroids
        centroids = scaler.inverse_transform(kmeans.cluster_centers_)
        cluster_labels = self._label_clusters(centroids)

        results = []
        for i, (vm_name, label) in enumerate(zip(vm_names, labels)):
            results.append({
                'vm_name': vm_name,
                'cluster_id': int(label),
                'workload_type': cluster_labels[label],
                'avg_cpu_utilization': round(features[i][0], 1),
                'avg_memory_utilization': round(features[i][2], 1),
            })

        # Build cluster summary
        cluster_summary = {}
        for cid in range(n_clusters):
            members = [r for r in results if r['cluster_id'] == cid]
            cluster_summary[cluster_labels[cid]] = {
                'count': len(members),
                'avg_cpu': round(float(centroids[cid][0]), 1),
                'avg_memory': round(float(centroids[cid][2]), 1),
            }

        self.clusters = {
            'vms': results,
            'summary': cluster_summary,
            'total_vms': len(results),
        }
        return self.clusters

    def _label_clusters(self, centroids):
        """Assign meaningful labels to clusters based on centroid values."""
        labels = {}
        for i, c in enumerate(centroids):
            cpu_util = c[0]  # avg CPU utilization
            mem_util = c[2]  # avg memory utilization

            if cpu_util < 10 and mem_util < 10:
                labels[i] = 'idle'
            elif cpu_util > mem_util * 1.5:
                labels[i] = 'cpu-intensive'
            elif mem_util > cpu_util * 1.5:
                labels[i] = 'memory-intensive'
            else:
                labels[i] = 'balanced'

        # Deduplicate labels
        seen = {}
        for k, v in labels.items():
            if v in seen.values():
                labels[k] = f"{v}-{k}"
            seen[k] = v

        return labels

    def detect_anomalies(self, vm_summaries):
        """Use Isolation Forest to detect VMs with anomalous resource usage."""
        if len(vm_summaries) < 5:
            return []

        features = []
        vm_names = []
        for s in vm_summaries:
            features.append([
                s['avg_cpu_utilization'],
                s['max_cpu_utilization'],
                s['avg_memory_utilization'],
                s['max_memory_utilization'],
                s['avg_disk_io'],
                s['avg_network_io'],
            ])
            vm_names.append(s['vm_name'])

        X = np.array(features)

        contamination = min(0.1, 3.0 / len(X))
        model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        predictions = model.fit_predict(X)
        scores = model.decision_function(X)

        anomalies = []
        for i, (vm_name, pred, score) in enumerate(zip(vm_names, predictions, scores)):
            if pred == -1:
                s = vm_summaries[i]

                # Determine anomaly type
                reasons = []
                if s['avg_cpu_utilization'] > 80:
                    reasons.append(f"high CPU ({s['avg_cpu_utilization']:.0f}%)")
                elif s['avg_cpu_utilization'] < 2:
                    reasons.append(f"near-zero CPU ({s['avg_cpu_utilization']:.1f}%)")
                if s['avg_memory_utilization'] > 80:
                    reasons.append(f"high memory ({s['avg_memory_utilization']:.0f}%)")
                elif s['avg_memory_utilization'] < 2:
                    reasons.append(f"near-zero memory ({s['avg_memory_utilization']:.1f}%)")
                if s['avg_disk_io'] > np.mean([f[4] for f in features]) * 3:
                    reasons.append("unusually high disk I/O")
                if not reasons:
                    reasons.append("unusual resource pattern")

                severity = 'HIGH' if s['avg_cpu_utilization'] > 90 or s['avg_memory_utilization'] > 90 else 'MEDIUM'

                anomalies.append({
                    'vm_name': vm_name,
                    'anomaly_score': round(float(-score), 3),
                    'severity': severity,
                    'reason': ', '.join(reasons),
                    'avg_cpu_utilization': round(s['avg_cpu_utilization'], 1),
                    'avg_memory_utilization': round(s['avg_memory_utilization'], 1),
                    'recommendation': 'scale up' if s['avg_cpu_utilization'] > 80 else 'consider decommission' if s['avg_cpu_utilization'] < 5 else 'investigate',
                })

        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        self.anomalies = anomalies
        return anomalies
