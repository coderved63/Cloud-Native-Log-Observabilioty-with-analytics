const express = require('express');
const router = express.Router();
const logger = require('./logger');
const { httpRequestsTotal, httpErrorsTotal, kafkaMessagesSentTotal } = require('./metrics');

const events = [
  { id: '1', name: 'Tech Conference 2026', date: '2026-04-10', venue: 'Mumbai' },
  { id: '2', name: 'Cloud Summit', date: '2026-05-15', venue: 'Pune' },
  { id: '3', name: 'DevOps Day', date: '2026-06-20', venue: 'Bangalore' },
];

router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'event-service' });
});

router.get('/events', async (req, res) => {
  await logger.debug(`Fetching event list, current count: ${events.length}`);
  kafkaMessagesSentTotal.inc({ service: 'event-service' });

  // Warn if event list is growing large
  if (events.length > 10) {
    await logger.warn(`Event list growing large: ${events.length} events in memory`);
    kafkaMessagesSentTotal.inc({ service: 'event-service' });
  }

  httpRequestsTotal.inc({ method: 'GET', route: '/events', status_code: '200', service: 'event-service' });
  await logger.info('Event list fetched');
  kafkaMessagesSentTotal.inc({ service: 'event-service' });
  res.json({ events });
});

router.post('/events', async (req, res) => {
  const { name, date, venue } = req.body || {};

  await logger.debug('Validating event creation payload');
  kafkaMessagesSentTotal.inc({ service: 'event-service' });

  if (!name || !date) {
    httpErrorsTotal.inc({ route: '/events', service: 'event-service' });
    httpRequestsTotal.inc({ method: 'POST', route: '/events', status_code: '400', service: 'event-service' });
    await logger.error('Event creation failed: missing name or date');
    kafkaMessagesSentTotal.inc({ service: 'event-service' });
    return res.status(400).json({ error: 'name and date are required' });
  }

  // Warn if event date is in the past
  if (new Date(date) < new Date()) {
    await logger.warn(`Event created with past date: ${date}`);
    kafkaMessagesSentTotal.inc({ service: 'event-service' });
  }

  // Critical if storage capacity exceeded
  if (events.length > 50) {
    await logger.critical(`Event storage capacity exceeded: ${events.length} events in memory, potential memory leak`);
    kafkaMessagesSentTotal.inc({ service: 'event-service' });
  }

  const newEvent = {
    id: Math.random().toString(36).slice(2, 10),
    name,
    date,
    venue: venue || 'TBD',
  };
  events.push(newEvent);

  httpRequestsTotal.inc({ method: 'POST', route: '/events', status_code: '201', service: 'event-service' });
  await logger.info(`Event created: ${name}`);
  kafkaMessagesSentTotal.inc({ service: 'event-service' });
  res.status(201).json({ event: newEvent, message: 'Event created successfully' });
});

router.delete('/events/:id', async (req, res) => {
  const { id } = req.params;
  await logger.debug(`Delete request for event id: ${id}`);
  kafkaMessagesSentTotal.inc({ service: 'event-service' });

  const index = events.findIndex(e => e.id === id);
  if (index === -1) {
    await logger.warn(`Attempted to delete non-existent event: ${id}`);
    kafkaMessagesSentTotal.inc({ service: 'event-service' });
    httpRequestsTotal.inc({ method: 'DELETE', route: '/events/:id', status_code: '404', service: 'event-service' });
    return res.status(404).json({ error: 'Event not found' });
  }

  events.splice(index, 1);
  await logger.info(`Event deleted: ${id}`);
  kafkaMessagesSentTotal.inc({ service: 'event-service' });
  httpRequestsTotal.inc({ method: 'DELETE', route: '/events/:id', status_code: '200', service: 'event-service' });
  res.json({ message: 'Event deleted' });
});

module.exports = router;
