import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from data_loader import BitbrainsDataLoader
from predictor import VMPredictor
from classifier import VMClassifier
from placement import VMPlacementOptimizer

app = Flask(__name__)
CORS(app)

PORT = int(os.getenv('PORT', '5002'))
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017')
DATA_DIR = os.getenv('DATA_DIR', '/app/data')

# MongoDB for storing analysis results
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['vm_analytics']

# Prometheus metrics
vm_analysis_runs = Counter('vm_analysis_runs_total', 'Total VM analysis runs')
vm_count_gauge = Gauge('vm_total_count', 'Total VMs loaded')
hosts_needed_gauge = Gauge('vm_hosts_needed', 'Optimal hosts needed')
avg_cpu_gauge = Gauge('vm_avg_cpu_utilization', 'Average CPU utilization across all VMs')
avg_mem_gauge = Gauge('vm_avg_memory_utilization', 'Average memory utilization across all VMs')
anomaly_count_gauge = Gauge('vm_anomaly_count', 'Number of anomalous VMs detected')

# Initialize components
loader = BitbrainsDataLoader(data_dir=DATA_DIR)
predictor = VMPredictor()
classifier = VMClassifier()
placement_optimizer = VMPlacementOptimizer()

# Global results store
results = {
    'summary': {},
    'predictions': [],
    'clusters': {},
    'placement': {},
    'anomalies': [],
    'efficiency': {},
    'last_analysis': None,
}


def run_analysis():
    """Run complete VM analysis pipeline."""
    global results

    try:
        print("[vm-optimizer] Loading VM data...")
        loader.load_all()

        if loader.vm_count == 0:
            print("[vm-optimizer] No VM data found. Skipping analysis.")
            return

        vm_summaries = loader.get_vm_summary()

        print(f"[vm-optimizer] Running analysis on {loader.vm_count} VMs...")

        # 1. Predict future usage
        preds = predictor.predict_all(loader.vm_data, top_n=20)
        results['predictions'] = preds

        # 2. Classify workloads
        clusters = classifier.classify_workloads(vm_summaries)
        results['clusters'] = clusters

        # 3. Detect anomalies
        anomalies = classifier.detect_anomalies(vm_summaries)
        results['anomalies'] = anomalies

        # 4. Optimize placement
        placement = placement_optimizer.optimize(vm_summaries)
        results['placement'] = placement

        # 5. Efficiency analysis
        efficiency = placement_optimizer.get_efficiency_analysis(vm_summaries)
        results['efficiency'] = efficiency

        # 6. Build summary
        avg_cpu = sum(s['avg_cpu_utilization'] for s in vm_summaries) / len(vm_summaries)
        avg_mem = sum(s['avg_memory_utilization'] for s in vm_summaries) / len(vm_summaries)

        results['summary'] = {
            'total_vms': loader.vm_count,
            'avg_cpu_utilization': round(avg_cpu, 1),
            'avg_memory_utilization': round(avg_mem, 1),
            'total_hosts_needed': placement.get('total_hosts_needed', 0),
            'hosts_saved': placement.get('hosts_saved', 0),
            'consolidation_ratio': placement.get('consolidation_ratio', 0),
            'anomalous_vms': len(anomalies),
            'high_risk_vms': sum(1 for p in preds if p['risk_level'] == 'HIGH'),
            'overprovisioned_vms': efficiency.get('overprovisioned_count', 0),
            'underprovisioned_vms': efficiency.get('underprovisioned_count', 0),
            'cluster_distribution': clusters.get('summary', {}),
        }

        from datetime import datetime
        results['last_analysis'] = datetime.utcnow().isoformat()

        # Update Prometheus gauges
        vm_analysis_runs.inc()
        vm_count_gauge.set(loader.vm_count)
        hosts_needed_gauge.set(placement.get('total_hosts_needed', 0))
        avg_cpu_gauge.set(round(avg_cpu, 1))
        avg_mem_gauge.set(round(avg_mem, 1))
        anomaly_count_gauge.set(len(anomalies))

        # Store results in MongoDB
        db['results'].replace_one(
            {'_id': 'latest'},
            {**results, '_id': 'latest'},
            upsert=True
        )

        print(f"[vm-optimizer] Analysis complete: {loader.vm_count} VMs, "
              f"{placement.get('total_hosts_needed', 0)} hosts needed, "
              f"{len(anomalies)} anomalies")

    except Exception as e:
        print(f"[vm-optimizer] Error during analysis: {e}")


# Routes
@app.route('/api/vm/summary', methods=['GET'])
def get_summary():
    return jsonify(results.get('summary', {}))


@app.route('/api/vm/predictions', methods=['GET'])
def get_predictions():
    return jsonify({
        'predictions': results.get('predictions', []),
        'total': len(results.get('predictions', [])),
        'last_analysis': results.get('last_analysis'),
    })


@app.route('/api/vm/clusters', methods=['GET'])
def get_clusters():
    return jsonify(results.get('clusters', {}))


@app.route('/api/vm/placement', methods=['GET'])
def get_placement():
    return jsonify(results.get('placement', {}))


@app.route('/api/vm/anomalies', methods=['GET'])
def get_anomalies():
    return jsonify({
        'anomalies': results.get('anomalies', []),
        'total': len(results.get('anomalies', [])),
        'last_analysis': results.get('last_analysis'),
    })


@app.route('/api/vm/efficiency', methods=['GET'])
def get_efficiency():
    return jsonify(results.get('efficiency', {}))


@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'vm-optimizer',
        'vms_loaded': loader.vm_count,
        'last_analysis': results.get('last_analysis'),
    })


# Run initial analysis on startup
print(f"[vm-optimizer] Starting VM Optimizer service on port {PORT}")
print(f"[vm-optimizer] Data directory: {DATA_DIR}")
run_analysis()

# Schedule re-analysis every 60 seconds
scheduler = BackgroundScheduler()
scheduler.add_job(run_analysis, 'interval', seconds=60)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
