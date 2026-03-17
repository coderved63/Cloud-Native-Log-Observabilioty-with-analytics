# Cloud-Native Real-Time Log Processing and Observability Platform

## Prerequisites
- Docker Desktop (with Docker Compose v2)
- Node.js >= 18 (for local development)
- Python 3.11 (for local development)
- k6 (for load testing)
- kubectl + minikube (for Kubernetes deployment)

## Quick Start (Docker Compose)

```bash
cd cloud-log-platform
docker compose up --build
```

### Service URLs
| Service         | URL                        |
|-----------------|----------------------------|
| Auth Service    | http://localhost:3001       |
| Event Service   | http://localhost:3002       |
| Booking Service | http://localhost:3003       |
| Log Processor   | http://localhost:8000/metrics |
| Prometheus      | http://localhost:9090       |
| Grafana         | http://localhost:3000       |
| MongoDB         | mongodb://localhost:27017   |

Grafana credentials: `admin / admin`

## API Reference

### Auth Service (port 3001)
```bash
# Login
curl -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Health
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

## Load Testing (k6)

```bash
# Default (localhost)
k6 run load-testing/k6-load-test.js

# Against a specific host
k6 run -e BASE_URL=http://192.168.49.2 load-testing/k6-load-test.js
```

Load stages: 100 → 500 → 1000 virtual users over ~3.5 minutes.

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

# 3. Apply manifests
kubectl apply -f kubernetes/namespace.yml
kubectl apply -f kubernetes/

# 4. Check status
kubectl get pods -n cloud-log-platform

# 5. Access Grafana
minikube service grafana -n cloud-log-platform
```

## Project Structure
```
cloud-log-platform/
├── services/
│   ├── auth-service/       # Login API, port 3001
│   ├── event-service/      # Events API, port 3002
│   └── booking-service/    # Bookings API, port 3003
├── log-processor/          # Python Kafka consumer → MongoDB
├── monitoring/
│   ├── prometheus/         # Scrape config
│   └── grafana/            # Dashboards and datasources
├── kubernetes/             # K8s manifests
├── load-testing/           # k6 load test script
└── docker-compose.yml
```
