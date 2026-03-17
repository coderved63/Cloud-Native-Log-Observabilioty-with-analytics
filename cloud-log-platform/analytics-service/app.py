import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from analyzer import LogAnalyzer

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017')
PORT = int(os.getenv('PORT', '5001'))

# Connect to MongoDB
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['logs_db']

# Initialize analyzer
analyzer = LogAnalyzer(db)

# Run analysis every 30 seconds
scheduler = BackgroundScheduler()
scheduler.add_job(analyzer.run_analysis, 'interval', seconds=30)
scheduler.start()

# Run initial analysis
print("[app] Running initial analysis...")
analyzer.run_analysis()


@app.route('/api/analytics/summary', methods=['GET'])
def get_summary():
    return jsonify(analyzer.results.get('summary', {}))


@app.route('/api/analytics/anomalies', methods=['GET'])
def get_anomalies():
    return jsonify({
        'anomalies': analyzer.results.get('anomalies', []),
        'total': len(analyzer.results.get('anomalies', [])),
        'last_analysis': analyzer.results.get('last_analysis'),
    })


@app.route('/api/analytics/trends', methods=['GET'])
def get_trends():
    return jsonify(analyzer.results.get('trends', {}))


@app.route('/api/analytics/predictions', methods=['GET'])
def get_predictions():
    return jsonify({
        'predictions': analyzer.results.get('predictions', []),
        'last_analysis': analyzer.results.get('last_analysis'),
    })


@app.route('/api/analytics/health-score', methods=['GET'])
def get_health_score():
    return jsonify(analyzer.results.get('health_scores', {}))


@app.route('/api/analytics/patterns', methods=['GET'])
def get_patterns():
    return jsonify({
        'patterns': analyzer.results.get('patterns', []),
        'total': len(analyzer.results.get('patterns', [])),
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'analytics-service',
        'last_analysis': analyzer.results.get('last_analysis'),
    })


if __name__ == '__main__':
    print(f"[app] Analytics service starting on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)
