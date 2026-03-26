const express = require('express');
const path = require('path');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 4000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://mongodb:27017';
const ANALYTICS_URL = process.env.ANALYTICS_URL || 'http://analytics-service:5001';
const VM_OPTIMIZER_URL = process.env.VM_OPTIMIZER_URL || 'http://vm-optimizer:5002';

let db;

async function connectDB() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  db = client.db('logs_db');
  console.log('[dashboard] Connected to MongoDB');
}

app.use(express.static(path.join(__dirname, 'public')));

// API: Get recent logs with optional filters
app.get('/api/logs', async (req, res) => {
  const { service, level, limit = 100 } = req.query;
  const filter = {};
  if (service && service !== 'all') filter.service = service;
  if (level && level !== 'all') filter.level = level.toUpperCase();

  const logs = await db.collection('logs')
    .find(filter)
    .sort({ _id: -1 })
    .limit(parseInt(limit))
    .toArray();

  res.json(logs);
});

// API: Get stats
app.get('/api/stats', async (req, res) => {
  const total = await db.collection('logs').countDocuments();

  const byService = await db.collection('logs').aggregate([
    { $group: { _id: '$service', count: { $sum: 1 } } }
  ]).toArray();

  const byLevel = await db.collection('logs').aggregate([
    { $group: { _id: '$level', count: { $sum: 1 } } }
  ]).toArray();

  const recent = await db.collection('logs')
    .find()
    .sort({ _id: -1 })
    .limit(1)
    .toArray();

  res.json({
    total,
    byService: byService.reduce((acc, s) => { acc[s._id] = s.count; return acc; }, {}),
    byLevel: byLevel.reduce((acc, l) => { acc[l._id] = l.count; return acc; }, {}),
    lastLog: recent[0] || null
  });
});

// API: Service health check
app.get('/api/health', async (req, res) => {
  const services = [
    { name: 'auth-service', url: 'http://auth-service:3001/health' },
    { name: 'event-service', url: 'http://event-service:3002/health' },
    { name: 'booking-service', url: 'http://booking-service:3003/health' },
    { name: 'analytics-service', url: `${ANALYTICS_URL}/health` },
    { name: 'vm-optimizer', url: `${VM_OPTIMIZER_URL}/health` },
  ];

  const results = await Promise.all(services.map(async (svc) => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const resp = await fetch(svc.url, { signal: controller.signal });
      clearTimeout(timeout);
      return { name: svc.name, status: resp.ok ? 'UP' : 'DOWN' };
    } catch {
      return { name: svc.name, status: 'DOWN' };
    }
  }));

  res.json(results);
});

// API: Proxy analytics endpoints
app.get('/api/analytics/:endpoint', async (req, res) => {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const resp = await fetch(`${ANALYTICS_URL}/api/analytics/${req.params.endpoint}`, {
      signal: controller.signal
    });
    clearTimeout(timeout);
    const data = await resp.json();
    res.json(data);
  } catch (e) {
    res.status(503).json({ error: 'Analytics service unavailable' });
  }
});

// API: Proxy VM optimizer endpoints
app.get('/api/vm/:endpoint', async (req, res) => {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const resp = await fetch(`${VM_OPTIMIZER_URL}/api/vm/${req.params.endpoint}`, {
      signal: controller.signal
    });
    clearTimeout(timeout);
    const data = await resp.json();
    res.json(data);
  } catch (e) {
    res.status(503).json({ error: 'VM Optimizer service unavailable' });
  }
});

async function start() {
  await connectDB();
  app.listen(PORT, () => {
    console.log(`[dashboard] Running on http://localhost:${PORT}`);
  });
}

start().catch(console.error);
