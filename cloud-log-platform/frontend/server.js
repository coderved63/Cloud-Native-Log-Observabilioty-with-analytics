const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

const AUTH_URL = process.env.AUTH_URL || 'http://auth-service:3001';
const EVENT_URL = process.env.EVENT_URL || 'http://event-service:3002';
const BOOKING_URL = process.env.BOOKING_URL || 'http://booking-service:3003';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Proxy API calls to microservices
app.post('/api/login', async (req, res) => {
  try {
    const resp = await fetch(`${AUTH_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });
    const data = await resp.json();
    res.status(resp.status).json(data);
  } catch (e) {
    res.status(500).json({ error: 'Auth service unavailable' });
  }
});

app.get('/api/events', async (req, res) => {
  try {
    const resp = await fetch(`${EVENT_URL}/events`);
    const data = await resp.json();
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Event service unavailable' });
  }
});

app.post('/api/events', async (req, res) => {
  try {
    const resp = await fetch(`${EVENT_URL}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });
    const data = await resp.json();
    res.status(resp.status).json(data);
  } catch (e) {
    res.status(500).json({ error: 'Event service unavailable' });
  }
});

app.get('/api/bookings', async (req, res) => {
  try {
    const resp = await fetch(`${BOOKING_URL}/bookings`);
    const data = await resp.json();
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Booking service unavailable' });
  }
});

app.post('/api/bookings', async (req, res) => {
  try {
    const resp = await fetch(`${BOOKING_URL}/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });
    const data = await resp.json();
    res.status(resp.status).json(data);
  } catch (e) {
    res.status(500).json({ error: 'Booking service unavailable' });
  }
});

app.listen(PORT, () => {
  console.log(`[frontend] Running on http://localhost:${PORT}`);
});
