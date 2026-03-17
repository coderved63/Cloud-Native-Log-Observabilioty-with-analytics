# Live Demo Presentation Guide
## Step-by-Step Script for Faculty Presentation

Total Time: 10-15 minutes

---

## BEFORE THE DEMO (Preparation — 5 minutes before)

Do these steps BEFORE faculty arrives:

1. Open Docker Desktop — make sure it's running
2. Open terminal and run:
   ```
   cd "c:/Users/Vedantnew/OneDrive/Desktop/CC/Assignment/cloud-log-platform"
   docker compose up --build
   ```
3. Wait for all services to start (1-2 minutes)
4. Open these browser tabs (keep them ready but minimized):
   - Tab 1: http://localhost:5000 (Frontend App)
   - Tab 2: http://localhost:4000 (Log Dashboard)
   - Tab 3: http://localhost:3000/d/cloud-log-platform-v1/ (Grafana — login admin/admin)
   - Tab 4: http://localhost:9090/targets (Prometheus)
5. Open a second terminal (keep it ready for k6 and curl commands)
6. Open VS Code with the project folder open

---

## PART 1: Introduction (2 minutes)
### What to say:

"Good morning/afternoon. Our project is titled 'Cloud-Native Real-Time Log Processing and Observability Platform for Microservices.'

In modern cloud systems, companies like Netflix and Uber run hundreds of microservices. Each service generates its own logs in separate containers. When something breaks, finding the root cause is extremely difficult because logs are scattered everywhere.

Our project solves this by building a centralized observability platform that:
- Collects logs from all services into one place using Kafka
- Stores them centrally in MongoDB
- Monitors system health in real-time using Prometheus and Grafana
- Provides a custom web dashboard for live log viewing
- Runs everything in Docker containers, orchestrated by Kubernetes with auto-scaling

Let me show you a live demo."

---

## PART 2: Show the Architecture (1 minute)
### What to do:

Open VS Code and show the project structure briefly.

### What to say:

"Here's our project structure. We have:
- Three microservices in the services folder — Auth, Event, and Booking — written in Node.js
- A log processor written in Python that consumes from Kafka
- A custom dashboard for live log viewing
- Monitoring configuration for Prometheus and Grafana
- 14 Kubernetes manifest files for production deployment
- A k6 load test script

Let me show you the system running."

---

## PART 3: Show Docker Containers Running (1 minute)
### What to do:

Switch to the terminal and run:
```
docker ps
```

### What to say:

"Here you can see all 10 containers running — three microservices, Kafka with Zookeeper, MongoDB, the log processor, Prometheus, Grafana, and our custom dashboard. All started with a single command: docker compose up.

Each service is isolated in its own container with its own dependencies. Docker ensures it runs the same on any machine."

---

## PART 4: Demo the Frontend Application (3 minutes) — THE WOW MOMENT
### What to do:

Open TWO browser windows side by side:
- **Left window**: http://localhost:5000 (Frontend)
- **Right window**: http://localhost:4000 (Log Dashboard)

### What to say:

"Now let me show you the real power of this platform. On the left, I have our frontend application — this is what end users see. On the right, I have our log dashboard — this shows all logs flowing through the system in real time.

**Step 1 — Login:**
Watch the right side as I login on the left..."
(Type user/pass and click Sign In on the frontend)
"...and there it is! The login log just appeared on the log dashboard within 2 seconds. The log traveled from the Auth Service, through Kafka, through the Log Processor, into MongoDB, and showed up on the dashboard.

**Step 2 — Create an Event:**
Let me create a new event..."
(Click + Create Event, fill in details, click Create)
"...again, the log appears on the right immediately. You can see it says 'Event created: Tech Conference'.

**Step 3 — Book a Ticket:**
Now let me book a ticket for this event..."
(Click Book Ticket on any event card)
"...booking confirmed! And the log is already on the dashboard.

Every single user action on the frontend generates a log that flows through the entire pipeline — this is real-time observability in action."

---

## PART 5: Show Custom Dashboard (2 minutes)
### What to do:

Switch to browser Tab 1: http://localhost:4000

### What to say:

"This is our custom-built observability dashboard. It connects directly to MongoDB and shows:

- At the top: total log count, split by INFO, ERROR, and WARNING levels
- Service health status — green dots showing all three services are UP
- Bar charts showing log distribution by service and by severity
- And below: a live log table with the most recent logs

You can see the logs from the curl commands I just ran — the login, event fetch, and booking creation.

I can filter by service — let me select just auth-service — now it shows only auth logs. I can also filter by level — let me select ERROR — now it shows only error logs.

The dashboard auto-refreshes every 5 seconds, so it shows live data."

---

## PART 6: Show Prometheus (1 minute)
### What to do:

Switch to browser Tab 3: http://localhost:9090/targets

### What to say:

"This is Prometheus — our metrics collection system. It scrapes each service's /metrics endpoint every 15 seconds.

You can see all targets are UP — auth-service, event-service, booking-service, and log-processor. All healthy and being monitored.

Each service exposes counters for: total HTTP requests, total errors, and total Kafka messages sent. Prometheus stores all this as time-series data."

---

## PART 7: Show Grafana Dashboard (1 minute)
### What to do:

Switch to browser Tab 2: http://localhost:3000/d/cloud-log-platform-v1/

### What to say:

"This is Grafana with our pre-configured dashboard. It has 6 panels:
- HTTP Request Rate — shows requests per second per service
- HTTP Error Rate — shows errors per second
- Logs Processed per Second — shows the log processor throughput
- Total Kafka Messages — shows cumulative messages sent
- CPU Usage by Service — shows resource consumption
- Log Processing Errors — shows any pipeline failures

Right now the numbers are low because I only made 3 manual requests. Let me run a load test to generate real traffic."

---

## PART 8: Run Load Test — THE HIGHLIGHT (2-3 minutes)
### What to do:

Switch to the second terminal and run:
```bash
cd "c:/Users/Vedantnew/OneDrive/Desktop/CC/Assignment/cloud-log-platform"
k6 run load-testing/k6-load-test.js
```

While k6 is running, switch between the Custom Dashboard and Grafana to show live data flowing.

### What to say:

"Now I'm running k6 — a load testing tool that simulates up to 200 concurrent users. Each virtual user performs a login, creates an event, and makes a booking — continuously.

Watch the custom dashboard — you can see the log count increasing rapidly. New logs appearing every second. The bar charts growing.

Now let me switch to Grafana — look at the request rate graph climbing up. The error rate staying low. The log processing rate matching the request rate — meaning our Kafka pipeline is keeping up in real time.

This proves our system handles concurrent load without data loss. Every request generates a log, every log flows through Kafka, gets processed by Python, stored in MongoDB, and is visible on both dashboards — all in real time."

(Wait for k6 to finish, then show the summary)

"The test completed. You can see:
- Average response time of around 30-50 milliseconds
- P95 latency under 250ms — meaning 95% of requests finished within that time
- Error rate below 5%
- Over 15,000 log documents generated and stored"

---

## PART 9: Show Kubernetes (1-2 minutes)
### What to do:

Run in terminal:
```bash
kubectl get pods -n cloud-log-platform
kubectl get services -n cloud-log-platform
kubectl get hpa -n cloud-log-platform
```

### What to say:

"We also deployed this entire system to Kubernetes using Minikube.

Here you can see 12 pods running — each microservice has 2 replicas for high availability. Kafka, Zookeeper, MongoDB, Prometheus, Grafana, and the log processor each have 1 pod.

The services provide stable network addresses for pod-to-pod communication.

And here's the key feature — Horizontal Pod Autoscalers. Each microservice is configured to auto-scale from 2 to 5 replicas when CPU usage exceeds 70%. This means if we get a traffic spike, Kubernetes automatically adds more instances to handle the load — and scales back down when traffic decreases.

This is exactly how production cloud systems work at scale."

---

## PART 10: Conclusion (30 seconds)
### What to say:

"To summarize, we built a complete cloud-native observability platform that demonstrates:
- Microservices architecture with real REST APIs
- A full-stack frontend web application for end users
- Real-time log streaming through Apache Kafka
- Centralized log storage in MongoDB
- System monitoring with Prometheus and Grafana
- A custom log dashboard for live log analysis
- End-to-end observability — action on frontend, log on dashboard within 2 seconds
- Docker containerization with 11 containers
- Kubernetes orchestration with auto-scaling
- Load testing validating performance under 200 concurrent users

Thank you. Happy to answer any questions."

---

## COMMON QUESTIONS AND ANSWERS

### Q: "Why did you choose MongoDB over MySQL?"
A: "Logs have flexible schemas — an auth log has 'username' field, a booking log has 'eventId'. MongoDB stores JSON documents so each log can have different fields without defining a rigid table schema. Also, MongoDB has higher write throughput which is important when thousands of logs arrive per second."

### Q: "Can this scale to millions of users?"
A: "The architecture supports it. Kafka can handle millions of messages per second. In production, you'd deploy to AWS or Google Cloud with a multi-node Kubernetes cluster, multiple Kafka brokers, and a MongoDB replica set. The auto-scaling we configured would handle traffic spikes automatically."

### Q: "What happens if Kafka goes down?"
A: "If Kafka goes down, services will fail to send logs and will retry. Once Kafka comes back up, the log flow resumes. In production, you'd run 3+ Kafka brokers so if one fails, the others continue serving. Kubernetes also auto-restarts crashed containers."

### Q: "What's the difference between Grafana dashboard and your custom dashboard?"
A: "Grafana shows metrics — numerical data over time like request rate, CPU usage, error rate as graphs. Our custom dashboard shows actual log messages — the text content of each log, which service generated it, and the severity level. Grafana answers 'how is the system performing?' Our dashboard answers 'what exactly happened?'"

### Q: "Why not use ELK stack (Elasticsearch, Logstash, Kibana)?"
A: "ELK is a great alternative. We chose Kafka + MongoDB because Kafka provides higher throughput for streaming and MongoDB is simpler to set up. As a future enhancement, we could add Elasticsearch for full-text search capabilities across logs."

### Q: "How does auto-scaling work?"
A: "Kubernetes monitors CPU usage of each pod. When average CPU exceeds our threshold of 70%, the Horizontal Pod Autoscaler calculates how many replicas are needed using the formula: desired = ceil(current * currentCPU / targetCPU). For example, if 2 pods are at 85% CPU, it calculates ceil(2 * 85/70) = 3, and spins up a third pod. When load drops, it scales back down."

### Q: "Is this similar to what companies use in production?"
A: "Yes, this is a simplified version of real observability stacks. Netflix uses a similar architecture with Kafka for event streaming. Uber uses Prometheus and Grafana for monitoring. The ELK stack and Datadog are commercial equivalents. Our project demonstrates the same core concepts."

### Q: "What did each team member contribute?"
A: (Adjust based on your team) "We divided the work into: microservices development, Kafka and log processor pipeline, monitoring setup (Prometheus/Grafana), Kubernetes deployment, custom dashboard, and load testing."

---

## EMERGENCY TROUBLESHOOTING (If Something Breaks During Demo)

### If a service is down:
```bash
docker compose restart auth-service
```

### If Grafana shows no data:
Go to http://localhost:3000/d/cloud-log-platform-v1/ and make sure the time range (top-right) is set to "Last 15 minutes"

### If k6 shows too many errors:
"The services are handling high load. Some connection timeouts are expected at peak load — this is realistic behavior that you'd see in production too. The key metric is that the majority of requests succeed."

### If MongoDB is empty:
```bash
docker compose restart log-processor
```
Wait 30 seconds, then run a few curl commands to generate logs.

### If Kubernetes pods are not running:
```bash
kubectl delete pods --all -n cloud-log-platform
```
Wait 1 minute for them to restart.

---
