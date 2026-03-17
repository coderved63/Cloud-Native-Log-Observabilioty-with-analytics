const express = require('express');
const router = express.Router();
const logger = require('./logger');
const { httpRequestsTotal, httpErrorsTotal, kafkaMessagesSentTotal } = require('./metrics');

const bookings = [
  { id: 'b1', eventId: '1', userId: 'u1', status: 'confirmed' },
  { id: 'b2', eventId: '2', userId: 'u2', status: 'confirmed' },
];

router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'booking-service' });
});

router.get('/bookings', async (req, res) => {
  await logger.debug(`Retrieving booking list, total: ${bookings.length}`);
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });

  httpRequestsTotal.inc({ method: 'GET', route: '/bookings', status_code: '200', service: 'booking-service' });
  await logger.info('Booking list fetched');
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });
  res.json({ bookings });
});

router.post('/bookings', async (req, res) => {
  const { eventId, userId } = req.body || {};

  await logger.debug(`Processing booking request for event ${eventId || 'unknown'} by user ${userId || 'unknown'}`);
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });

  if (!eventId || !userId) {
    httpErrorsTotal.inc({ route: '/bookings', service: 'booking-service' });
    httpRequestsTotal.inc({ method: 'POST', route: '/bookings', status_code: '400', service: 'booking-service' });
    await logger.error('Booking failed: missing eventId or userId');
    kafkaMessagesSentTotal.inc({ service: 'booking-service' });
    return res.status(400).json({ error: 'eventId and userId are required' });
  }

  // Check for duplicate booking
  const duplicate = bookings.find(b => b.eventId === eventId && b.userId === userId);
  if (duplicate) {
    await logger.warn(`Duplicate booking attempt: user ${userId} already booked event ${eventId}`);
    kafkaMessagesSentTotal.inc({ service: 'booking-service' });
  }

  // Critical if system overloaded
  if (bookings.length > 100) {
    await logger.critical(`Booking system overloaded: ${bookings.length} active bookings, degraded performance expected`);
    kafkaMessagesSentTotal.inc({ service: 'booking-service' });
  }

  const booking = {
    id: 'b' + Math.random().toString(36).slice(2, 8),
    eventId,
    userId,
    status: 'confirmed',
    createdAt: new Date().toISOString(),
  };
  bookings.push(booking);

  httpRequestsTotal.inc({ method: 'POST', route: '/bookings', status_code: '201', service: 'booking-service' });
  await logger.info(`Booking created for event ${eventId} by user ${userId}`);
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });
  res.status(201).json({ booking, message: 'Booking created successfully' });
});

router.get('/bookings/:id', async (req, res) => {
  const { id } = req.params;
  await logger.debug(`Looking up booking: ${id}`);
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });

  const booking = bookings.find(b => b.id === id);
  if (!booking) {
    await logger.warn(`Booking not found: ${id}`);
    kafkaMessagesSentTotal.inc({ service: 'booking-service' });
    httpRequestsTotal.inc({ method: 'GET', route: '/bookings/:id', status_code: '404', service: 'booking-service' });
    return res.status(404).json({ error: 'Booking not found' });
  }

  httpRequestsTotal.inc({ method: 'GET', route: '/bookings/:id', status_code: '200', service: 'booking-service' });
  await logger.info(`Booking retrieved: ${id}`);
  kafkaMessagesSentTotal.inc({ service: 'booking-service' });
  res.json({ booking });
});

module.exports = router;
