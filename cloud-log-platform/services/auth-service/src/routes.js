const express = require('express');
const router = express.Router();
const logger = require('./logger');
const { httpRequestsTotal, httpErrorsTotal, kafkaMessagesSentTotal } = require('./metrics');

const VALID_USERS = { admin: 'admin123', user: 'pass', 'stress-test': 'pass' };

// Track failed login attempts for brute-force detection
const failedAttempts = {};

router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'auth-service' });
});

router.post('/login', async (req, res) => {
  const { username, password } = req.body || {};

  await logger.debug(`Login request received for user: ${username || 'unknown'}`);
  kafkaMessagesSentTotal.inc({ service: 'auth-service' });

  if (!username || !password) {
    httpErrorsTotal.inc({ route: '/login', service: 'auth-service' });
    httpRequestsTotal.inc({ method: 'POST', route: '/login', status_code: '400', service: 'auth-service' });
    await logger.error('Login attempt with missing credentials');
    kafkaMessagesSentTotal.inc({ service: 'auth-service' });
    return res.status(400).json({ error: 'Username and password required' });
  }

  if (VALID_USERS[username] !== password) {
    // Track failed attempts
    failedAttempts[username] = (failedAttempts[username] || 0) + 1;

    httpErrorsTotal.inc({ route: '/login', service: 'auth-service' });
    httpRequestsTotal.inc({ method: 'POST', route: '/login', status_code: '401', service: 'auth-service' });
    await logger.error(`Failed login attempt for user: ${username}`);
    kafkaMessagesSentTotal.inc({ service: 'auth-service' });

    // Brute-force detection
    if (failedAttempts[username] > 3) {
      await logger.warn(`Possible brute-force attack detected for user: ${username} (${failedAttempts[username]} failed attempts)`);
      kafkaMessagesSentTotal.inc({ service: 'auth-service' });
    }

    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Reset failed attempts on success
  failedAttempts[username] = 0;

  // Simulate random critical error for stress-test user (5% chance)
  if (username === 'stress-test' && Math.random() < 0.05) {
    await logger.critical('Authentication system error: token generation failed due to internal failure');
    kafkaMessagesSentTotal.inc({ service: 'auth-service' });
    httpErrorsTotal.inc({ route: '/login', service: 'auth-service' });
    httpRequestsTotal.inc({ method: 'POST', route: '/login', status_code: '500', service: 'auth-service' });
    return res.status(500).json({ error: 'Internal server error' });
  }

  const token = Buffer.from(`${username}:${Date.now()}`).toString('base64');
  httpRequestsTotal.inc({ method: 'POST', route: '/login', status_code: '200', service: 'auth-service' });
  await logger.info(`User ${username} logged in successfully`);
  kafkaMessagesSentTotal.inc({ service: 'auth-service' });
  res.json({ token, message: 'Login successful' });
});

router.get('/validate', async (req, res) => {
  const token = req.headers.authorization;
  await logger.debug('Token validation request received');
  kafkaMessagesSentTotal.inc({ service: 'auth-service' });

  if (!token) {
    await logger.warn('Token validation attempted without authorization header');
    kafkaMessagesSentTotal.inc({ service: 'auth-service' });
    httpRequestsTotal.inc({ method: 'GET', route: '/validate', status_code: '401', service: 'auth-service' });
    return res.status(401).json({ valid: false, error: 'No token provided' });
  }

  await logger.info('Token validated successfully');
  kafkaMessagesSentTotal.inc({ service: 'auth-service' });
  httpRequestsTotal.inc({ method: 'GET', route: '/validate', status_code: '200', service: 'auth-service' });
  res.json({ valid: true });
});

module.exports = router;
