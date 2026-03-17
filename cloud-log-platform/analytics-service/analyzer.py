import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict


class LogAnalyzer:
    def __init__(self, db):
        self.db = db
        self.collection = db['logs']
        self.results = {
            'anomalies': [],
            'trends': {},
            'predictions': [],
            'health_scores': {},
            'patterns': [],
            'summary': {},
            'last_analysis': None,
        }

    def run_analysis(self):
        """Run all analyses. Called every 30 seconds by scheduler."""
        try:
            self._detect_anomalies()
            self._analyze_trends()
            self._make_predictions()
            self._calculate_health_scores()
            self._detect_patterns()
            self._build_summary()
            self.results['last_analysis'] = datetime.utcnow().isoformat()
            print(f"[analyzer] Analysis complete at {self.results['last_analysis']}")
        except Exception as e:
            print(f"[analyzer] Error during analysis: {e}")

    def _get_time_windows(self, minutes=30, window_size_minutes=1):
        """Get log counts grouped by time windows."""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        pipeline = [
            {'$match': {'timestamp': {'$gte': since.isoformat()}}},
            {'$group': {
                '_id': {
                    'level': '$level',
                    'minute': {'$substr': ['$timestamp', 0, 16]}  # group by minute
                },
                'count': {'$sum': 1}
            }}
        ]

        try:
            cursor = self.collection.aggregate(pipeline)
            results = list(cursor)
        except Exception:
            results = []

        # Build windows dict: {minute: {DEBUG: n, INFO: n, ...}}
        windows = defaultdict(lambda: {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0})
        for r in results:
            minute = r['_id'].get('minute', '')
            level = r['_id'].get('level', 'INFO')
            if level in windows[minute]:
                windows[minute][level] = r['count']

        return dict(windows)

    def _detect_anomalies(self):
        """Use Isolation Forest to detect anomalous time windows."""
        windows = self._get_time_windows(minutes=60)

        if len(windows) < 5:
            self.results['anomalies'] = []
            return

        # Build feature matrix
        timestamps = sorted(windows.keys())
        features = []
        for ts in timestamps:
            w = windows[ts]
            features.append([w['DEBUG'], w['INFO'], w['WARNING'], w['ERROR'], w['CRITICAL']])

        X = np.array(features)

        # Train Isolation Forest
        contamination = min(0.15, 2.0 / len(X))  # at least detect something
        model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        predictions = model.fit_predict(X)
        scores = model.decision_function(X)

        anomalies = []
        for i, (ts, pred, score) in enumerate(zip(timestamps, predictions, scores)):
            if pred == -1:  # anomaly
                w = windows[ts]
                # Determine what's unusual
                reasons = []
                if w['ERROR'] > 0:
                    reasons.append(f"{w['ERROR']} errors")
                if w['CRITICAL'] > 0:
                    reasons.append(f"{w['CRITICAL']} critical events")
                if w['WARNING'] > 0:
                    reasons.append(f"{w['WARNING']} warnings")
                if not reasons:
                    reasons.append("unusual log volume pattern")

                anomalies.append({
                    'timestamp': ts,
                    'anomaly_score': round(float(-score), 3),
                    'severity': 'HIGH' if w['CRITICAL'] > 0 or w['ERROR'] > 3 else 'MEDIUM',
                    'reason': ', '.join(reasons),
                    'log_counts': w,
                })

        # Sort by score descending, keep top 10
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        self.results['anomalies'] = anomalies[:10]

    def _analyze_trends(self):
        """Analyze log rate trends over recent time windows."""
        windows = self._get_time_windows(minutes=30)

        if len(windows) < 4:
            self.results['trends'] = {
                'error_trend': 'stable',
                'warning_trend': 'stable',
                'overall_trend': 'stable',
                'details': {},
            }
            return

        timestamps = sorted(windows.keys())
        mid = len(timestamps) // 2

        # Compare first half vs second half
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        trends = {}

        for level in levels:
            first_half = sum(windows[ts][level] for ts in timestamps[:mid])
            second_half = sum(windows[ts][level] for ts in timestamps[mid:])

            if first_half == 0:
                change_pct = 100.0 if second_half > 0 else 0.0
            else:
                change_pct = ((second_half - first_half) / first_half) * 100

            if change_pct > 20:
                direction = 'increasing'
            elif change_pct < -20:
                direction = 'decreasing'
            else:
                direction = 'stable'

            trends[level] = {
                'direction': direction,
                'change_percent': round(change_pct, 1),
                'recent_count': second_half,
                'previous_count': first_half,
            }

        self.results['trends'] = {
            'error_trend': trends.get('ERROR', {}).get('direction', 'stable'),
            'warning_trend': trends.get('WARNING', {}).get('direction', 'stable'),
            'overall_trend': 'increasing' if sum(
                1 for l in levels if trends.get(l, {}).get('direction') == 'increasing'
            ) > 2 else 'stable',
            'details': trends,
            'window_count': len(timestamps),
        }

    def _make_predictions(self):
        """Use Linear Regression to predict future error rates."""
        windows = self._get_time_windows(minutes=30)

        if len(windows) < 5:
            self.results['predictions'] = []
            return

        timestamps = sorted(windows.keys())

        predictions = []
        for level in ['ERROR', 'CRITICAL', 'WARNING']:
            counts = [windows[ts][level] for ts in timestamps]
            X = np.arange(len(counts)).reshape(-1, 1)
            y = np.array(counts)

            model = LinearRegression()
            model.fit(X, y)

            # Predict next 5 windows
            future_X = np.arange(len(counts), len(counts) + 5).reshape(-1, 1)
            future_y = model.predict(future_X)

            current_avg = np.mean(counts[-5:]) if len(counts) >= 5 else np.mean(counts)
            predicted_avg = np.mean(future_y)
            slope = float(model.coef_[0])

            if slope > 0.5:
                trend = 'increasing'
                risk = 'HIGH' if level in ('ERROR', 'CRITICAL') else 'MEDIUM'
            elif slope < -0.5:
                trend = 'decreasing'
                risk = 'LOW'
            else:
                trend = 'stable'
                risk = 'LOW'

            predictions.append({
                'level': level,
                'current_avg': round(float(current_avg), 2),
                'predicted_avg': round(float(max(0, predicted_avg)), 2),
                'trend': trend,
                'slope': round(slope, 3),
                'risk_level': risk,
                'confidence': round(float(model.score(X, y)), 3) if len(counts) > 2 else 0,
            })

        self.results['predictions'] = predictions

    def _calculate_health_scores(self):
        """Calculate per-service health scores."""
        since = datetime.utcnow() - timedelta(minutes=15)

        pipeline = [
            {'$match': {'timestamp': {'$gte': since.isoformat()}}},
            {'$group': {
                '_id': {'service': '$service', 'level': '$level'},
                'count': {'$sum': 1}
            }}
        ]

        try:
            cursor = self.collection.aggregate(pipeline)
            results = list(cursor)
        except Exception:
            results = []

        # Build per-service counts
        service_counts = defaultdict(lambda: {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0, 'total': 0})
        for r in results:
            svc = r['_id'].get('service', 'unknown')
            level = r['_id'].get('level', 'INFO')
            count = r['count']
            if level in service_counts[svc]:
                service_counts[svc][level] = count
            service_counts[svc]['total'] += count

        health_scores = {}
        for svc, counts in service_counts.items():
            total = counts['total']
            if total == 0:
                score = 100
            else:
                # Penalty: CRITICAL=-25, ERROR=-10, WARNING=-3 per occurrence (relative to total)
                penalty = (
                    counts['CRITICAL'] * 25 +
                    counts['ERROR'] * 10 +
                    counts['WARNING'] * 3
                ) / total * 10  # scale factor

                score = max(0, min(100, 100 - penalty))

            if score >= 80:
                status = 'healthy'
            elif score >= 50:
                status = 'degraded'
            else:
                status = 'critical'

            health_scores[svc] = {
                'score': round(score, 1),
                'status': status,
                'total_logs': total,
                'error_count': counts['ERROR'],
                'critical_count': counts['CRITICAL'],
                'warning_count': counts['WARNING'],
            }

        self.results['health_scores'] = health_scores

    def _detect_patterns(self):
        """Use TF-IDF to find recurring error patterns."""
        since = datetime.utcnow() - timedelta(minutes=30)

        try:
            error_logs = list(self.collection.find(
                {'level': {'$in': ['ERROR', 'CRITICAL']}, 'timestamp': {'$gte': since.isoformat()}},
                {'message': 1, 'service': 1, 'level': 1}
            ).limit(500))
        except Exception:
            error_logs = []

        if len(error_logs) < 3:
            self.results['patterns'] = []
            return

        messages = [log.get('message', '') for log in error_logs]

        # TF-IDF vectorization
        try:
            vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
            X = vectorizer.fit_transform(messages)

            # Cluster with KMeans
            n_clusters = min(5, len(messages))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)

            # Get top patterns per cluster
            patterns = []
            for cluster_id in range(n_clusters):
                cluster_msgs = [messages[i] for i in range(len(messages)) if clusters[i] == cluster_id]
                cluster_services = [error_logs[i].get('service', 'unknown') for i in range(len(error_logs)) if clusters[i] == cluster_id]

                if cluster_msgs:
                    # Get representative message (most common-ish)
                    patterns.append({
                        'pattern': cluster_msgs[0][:100],
                        'count': len(cluster_msgs),
                        'services': list(set(cluster_services)),
                        'severity': 'CRITICAL' if any(
                            error_logs[i].get('level') == 'CRITICAL' for i in range(len(error_logs)) if clusters[i] == cluster_id
                        ) else 'ERROR',
                    })

            patterns.sort(key=lambda x: x['count'], reverse=True)
            self.results['patterns'] = patterns[:5]

        except Exception as e:
            print(f"[analyzer] Pattern detection error: {e}")
            self.results['patterns'] = []

    def _build_summary(self):
        """Build overall analytics summary."""
        anomaly_count = len(self.results['anomalies'])
        high_risk_predictions = sum(1 for p in self.results['predictions'] if p['risk_level'] == 'HIGH')

        # Overall system status
        health_values = [h['score'] for h in self.results['health_scores'].values()]
        avg_health = sum(health_values) / len(health_values) if health_values else 100

        if avg_health >= 80 and anomaly_count == 0:
            system_status = 'healthy'
        elif avg_health >= 50:
            system_status = 'degraded'
        else:
            system_status = 'critical'

        self.results['summary'] = {
            'system_status': system_status,
            'avg_health_score': round(avg_health, 1),
            'total_anomalies': anomaly_count,
            'high_risk_predictions': high_risk_predictions,
            'active_patterns': len(self.results['patterns']),
            'services_monitored': len(self.results['health_scores']),
            'health_scores': self.results['health_scores'],
        }
