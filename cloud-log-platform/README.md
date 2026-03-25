# Cloud-Native Real-Time Log Processing and Observability Platform

A cloud-native microservices platform with real-time log processing, centralized observability, and auto-scaling capabilities. Built with Node.js, Python, Apache Kafka, MongoDB, Prometheus, Grafana, Docker, and Kubernetes.

## Architecture

```
        Users / k6 Load Generator
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
  +-----------+ +-----------+ +-----------+
  |   Auth    | |   Event   | |  Booking  |
  |  Service  | |  Service  | |  Service  |
  | (Node.js) | | (Node.js) | | (Node.js) |
  |  :3001    | |  :3002    | |  :3003    |
  +-----+-----+ +-----+-----+ +-----+-----+
        |              |              |
        |   (logs via Kafka Producer) |
        +------+-------+-------+-----+
               |               |
               v               v
        +------------+   +-----------+
        |   Apache   |   |Prometheus |
        |   Kafka    |   | (scrapes  |
        | (Zookeeper)|   |  /metrics)|
        +------+-----+   +-----+-----+
               |                |
               v                v
        +------------+   +-----------+
        |    Log     |   |  Grafana  |
        | Processor  |   | Dashboard |
        |  (Python)  |   |  :3000    |
        +------+-----+   +-----------+
               |
               v
        +------------+       +-----------+
        |  MongoDB   |<------| Analytics |
        | (Log Store)|       |  Service  |
        |  :27017    |       |  :5001    |
        +------------+       +-----+-----+
               ^                   |
               |             +-----+-----+
               +-------------|  Custom   |
                             | Dashboard |
                             |  :4000    |
                             +-----------+

  +-----------+
  | Frontend  |---> Auth Service (:3001)
  | Web App   |---> Event Service (:3002)
  |  :5000    |---> Booking Service (:3003)
  +-----------+
```

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Node.js 18 / Express | Microservices, Frontend, Dashboard |
| Python 3.11 / Flask | Log Processor, Analytics Service |
| Apache Kafka 7.5.0 | Message broker for log streaming |
| MongoDB 7.0 | Centralized log storage |
| scikit-learn / NumPy / Pandas | ML-based log analytics |
| Prometheus 2.47.0 | Metrics collection |
| Grafana 10.1.0 | Metrics visualization |
| Docker / Docker Compose | Containerization |
| Kubernetes / Minikube | Container orchestration |
| k6 | Load testing |

## Prerequisites

- Docker Desktop (with Docker Compose v2)
- Node.js >= 18 (for local development)
- Python 3.11 (for local development)
- k6 (for load testing)
- kubectl + Minikube (for Kubernetes deployment)

## Quick Start

```bash
cd cloud-log-platform
docker compose up --build
```

This starts all 12 services with proper dependency ordering. Wait ~60 seconds for Kafka and all services to be healthy.

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5000 | User-facing web app (Login, Events, Bookings) |
| Auth Service | http://localhost:3001 | User authentication with JWT |
| Event Service | http://localhost:3002 | Event management (CRUD) |
| Booking Service | http://localhost:3003 | Ticket booking system |
| Log Dashboard | http://localhost:4000 | Real-time log viewer with filters |
| Analytics Service | http://localhost:5001 | ML-powered log analytics (anomalies, predictions, patterns) |
| Log Processor | http://localhost:8000/metrics | Kafka consumer, writes to MongoDB |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Dashboards (admin / admin) |
| MongoDB | mongodb://localhost:27017 | Log storage |

## Project Structure

```
cloud-log-platform/
├── services/
│   ├── auth-service/          # Login API (port 3001)
│   │   └── src/
│   │       ├── index.js       # Express server, /metrics endpoint
│   │       ├── routes.js      # POST /login, GET /health
│   │       ├── kafka.js       # Kafka producer
│   │       ├── logger.js      # Structured log producer
│   │       └── metrics.js     # Prometheus counters
│   ├── event-service/         # Events API (port 3002)
│   │   └── src/               # Same structure as auth-service
│   └── booking-service/       # Bookings API (port 3003)
│       └── src/               # Same structure as auth-service
├── log-processor/             # Python Kafka consumer -> MongoDB
│   ├── main.py                # Entry point, log classification
│   ├── consumer.py            # Kafka consumer wrapper
│   ├── storage.py             # MongoDB insertion
│   └── metrics_server.py      # Prometheus metrics
├── analytics-service/         # ML-powered log analytics (port 5001)
│   ├── app.py                 # Flask API server, scheduler (runs every 30s)
│   ├── analyzer.py            # ML models (Isolation Forest, Linear Regression, KMeans)
│   └── requirements.txt       # scikit-learn, numpy, pandas, flask
├── dashboard/                 # Log dashboard UI (port 4000)
│   ├── server.js              # Express API (connects to MongoDB)
│   └── public/index.html      # Dashboard UI
├── frontend/                  # User-facing web app (port 5000)
│   ├── server.js              # Proxy to microservices
│   └── public/index.html      # Login, Events, Bookings UI
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml     # Scrape targets config
│   └── grafana/
│       ├── provisioning/      # Datasource + dashboard providers
│       └── dashboards/        # Pre-configured 6-panel dashboard
├── kubernetes/                # 14 K8s manifests
│   ├── namespace.yml
│   ├── configmap.yml
│   ├── *-deployment.yml       # Deployments + Services + HPAs
│   └── mongodb-pvc.yml       # Persistent storage
├── load-testing/
│   └── k6-load-test.js       # Load test script
└── docker-compose.yml         # Full platform orchestration
```

## API Reference

### Auth Service (port 3001)
```bash
# Login
curl -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Health check
curl http://localhost:3001/health
```

### Event Service (port 3002)
```bash
# List events
curl http://localhost:3002/events

# Create event
curl -X POST http://localhost:3002/events \
  -H "Content-Type: application/json" \
  -d '{"name":"Tech Summit","date":"2026-06-01","venue":"Mumbai"}'
```

### Booking Service (port 3003)
```bash
# List bookings
curl http://localhost:3003/bookings

# Create booking
curl -X POST http://localhost:3003/bookings \
  -H "Content-Type: application/json" \
  -d '{"eventId":"1","userId":"u1"}'
```

## How the Pipeline Works

1. **User performs an action** on the Frontend (login, create event, book ticket)
2. **Frontend proxies** the request to the respective microservice
3. **Microservice processes** the request and returns a response
4. **Microservice sends a structured log** to Kafka (`logs_topic`) and increments Prometheus metrics
5. **Log Processor consumes** the log from Kafka, classifies it (INFO/ERROR/WARNING), and stores it in MongoDB
6. **Log Dashboard** reads from MongoDB and displays logs in real-time (auto-refreshes every 5 seconds)
7. **Prometheus scrapes** metrics from all services every 15 seconds
8. **Grafana visualizes** the metrics as real-time graphs

End-to-end latency: a login on the Frontend appears on the Log Dashboard within **2-3 seconds** and on Grafana within **15 seconds**.

## Load Testing

```bash
# Run load test (200 virtual users over 3.5 minutes)
k6 run load-testing/k6-load-test.js

# Against a specific host
k6 run -e BASE_URL=http://192.168.49.2 load-testing/k6-load-test.js
```

**Load profile:** Ramps from 0 -> 50 -> 100 -> 200 virtual users, each performing login + create event + create booking.

**Expected results:**
- Average response time: 30-50ms
- P95 latency: < 250ms
- Error rate: < 5%
- Peak throughput: ~150-200 req/sec

## Kubernetes Deployment

```bash
# 1. Start minikube
minikube start

# 2. Build images inside minikube's Docker daemon
eval $(minikube docker-env)
docker build -t auth-service:latest ./services/auth-service
docker build -t event-service:latest ./services/event-service
docker build -t booking-service:latest ./services/booking-service
docker build -t log-processor:latest ./log-processor
docker build -t dashboard:latest ./dashboard
docker build -t frontend:latest ./frontend
docker build -t analytics-service:latest ./analytics-service

# 3. Apply manifests
kubectl apply -f kubernetes/namespace.yml
kubectl apply -f kubernetes/

# 4. Check status
kubectl get pods -n cloud-log-platform

# 5. Access services
minikube service grafana -n cloud-log-platform
minikube service frontend -n cloud-log-platform
minikube service dashboard -n cloud-log-platform
```

**Auto-scaling:** Auth, Event, and Booking services have HPA configured (2-5 replicas, 70% CPU threshold).

## Monitoring

### Grafana Dashboard (pre-configured)
Access at http://localhost:3000 (admin / admin). The dashboard includes 6 panels:

1. **HTTP Request Rate** - Requests/sec per service
2. **HTTP Error Rate** - Errors/sec per service
3. **Logs Processed per Second** - Log processor throughput
4. **Total Kafka Messages Sent** - Messages produced to Kafka
5. **CPU Usage by Service** - CPU utilization percentage
6. **Log Processing Errors** - Processing failure rate

### Custom Log Dashboard
Access at http://localhost:4000. Features:
- Live log stream with auto-refresh (5s)
- Filter by service and severity level
- Service health status (UP/DOWN)
- Log distribution charts (by service and level)
- Color-coded severity badges

## ML-Powered Analytics Service

The Analytics Service (port 5001) runs **machine learning models** on log data every 30 seconds to provide intelligent insights.

### ML Models Used

| Model | Library | Purpose |
|-------|---------|---------|
| **Isolation Forest** | scikit-learn | Detects anomalous time windows (unusual spikes in errors/warnings) |
| **Linear Regression** | scikit-learn | Predicts future error rates and identifies trending issues |
| **TF-IDF + KMeans** | scikit-learn | Clusters error messages to find recurring failure patterns |

### Analytics Endpoints

```bash
# Overall system summary (health scores, anomaly count, status)
curl http://localhost:5001/api/analytics/summary

# Detected anomalies (Isolation Forest results)
curl http://localhost:5001/api/analytics/anomalies

# Log rate trends (increasing/decreasing/stable per level)
curl http://localhost:5001/api/analytics/trends

# Error rate predictions (Linear Regression forecasts)
curl http://localhost:5001/api/analytics/predictions

# Per-service health scores (0-100, weighted by error severity)
curl http://localhost:5001/api/analytics/health-score

# Recurring error patterns (TF-IDF + KMeans clusters)
curl http://localhost:5001/api/analytics/patterns
```

### How It Works

1. **Every 30 seconds**, the analyzer reads logs from MongoDB
2. **Anomaly Detection** — groups logs into 1-minute time windows, builds a feature matrix (counts per severity level), and runs Isolation Forest to flag unusual windows
3. **Trend Analysis** — compares first-half vs second-half of recent logs to detect if errors/warnings are increasing or decreasing
4. **Predictions** — fits Linear Regression on error counts over time, predicts the next 5 time windows, and assigns risk levels (HIGH/MEDIUM/LOW)
5. **Health Scores** — calculates a 0-100 score per service based on error penalties (CRITICAL: -25, ERROR: -10, WARNING: -3 per occurrence)
6. **Pattern Detection** — extracts error/critical log messages, vectorizes with TF-IDF, clusters with KMeans, and reports the top 5 recurring failure patterns

The Dashboard (port 4000) consumes these analytics endpoints to display insights alongside live logs.

## Database

**MongoDB 7.0** stores all processed logs.

```
Database: logs_db
Collection: logs

Document schema:
{
  "service":   "auth-service | event-service | booking-service",
  "level":     "INFO | ERROR | WARNING",
  "message":   "Description of the event",
  "timestamp": "2026-03-15T12:30:45.123Z"
}
```
