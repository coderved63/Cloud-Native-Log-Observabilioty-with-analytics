import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m',  target: 100 },
    { duration: '30s', target: 200 },
    { duration: '1m',  target: 200 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed:   ['rate<0.20'],
  },
};

const headers = { 'Content-Type': 'application/json' };
const opts = { headers, timeout: '10s' };

export default function () {
  // === AUTH SERVICE ===

  // 1. Successful login (generates DEBUG + INFO)
  const loginRes = http.post(
    `${BASE_URL}:3001/login`,
    JSON.stringify({ username: 'user', password: 'pass' }),
    opts
  );
  check(loginRes, {
    'login status 200': (r) => r.status === 200,
    'login has token':   (r) => r.status === 200 && JSON.parse(r.body).token !== undefined,
  });
  sleep(0.5);

  // 2. Failed login - wrong password (generates DEBUG + ERROR)
  http.post(
    `${BASE_URL}:3001/login`,
    JSON.stringify({ username: 'user', password: 'wrongpass' }),
    opts
  );
  sleep(0.3);

  // 3. Missing credentials (generates ERROR)
  http.post(
    `${BASE_URL}:3001/login`,
    JSON.stringify({}),
    opts
  );
  sleep(0.3);

  // 4. Repeated failed logins for brute-force detection (generates WARNING)
  for (let i = 0; i < 4; i++) {
    http.post(
      `${BASE_URL}:3001/login`,
      JSON.stringify({ username: 'hacker', password: 'attempt' + i }),
      opts
    );
  }
  sleep(0.3);

  // 5. Stress-test user (generates CRITICAL randomly ~5%)
  http.post(
    `${BASE_URL}:3001/login`,
    JSON.stringify({ username: 'stress-test', password: 'pass' }),
    opts
  );
  sleep(0.3);

  // === EVENT SERVICE ===

  // 6. Get events (generates DEBUG + INFO)
  http.get(`${BASE_URL}:3002/events`, opts);
  sleep(0.3);

  // 7. Create event with valid data (generates DEBUG + INFO)
  http.post(
    `${BASE_URL}:3002/events`,
    JSON.stringify({
      name: `Event-${Math.random().toString(36).slice(2, 8)}`,
      date: '2026-06-01',
      venue: 'Mumbai',
    }),
    opts
  );
  sleep(0.3);

  // 8. Create event with past date (generates DEBUG + WARNING)
  http.post(
    `${BASE_URL}:3002/events`,
    JSON.stringify({ name: 'PastEvent', date: '2020-01-01', venue: 'Delhi' }),
    opts
  );
  sleep(0.3);

  // 9. Create event with missing fields (generates DEBUG + ERROR)
  http.post(
    `${BASE_URL}:3002/events`,
    JSON.stringify({ venue: 'Nowhere' }),
    opts
  );
  sleep(0.3);

  // === BOOKING SERVICE ===

  // 10. Get bookings (generates DEBUG + INFO)
  http.get(`${BASE_URL}:3003/bookings`, opts);
  sleep(0.3);

  // 11. Create booking (generates DEBUG + INFO)
  http.post(
    `${BASE_URL}:3003/bookings`,
    JSON.stringify({ eventId: '1', userId: `u${__ITER}` }),
    opts
  );
  sleep(0.3);

  // 12. Duplicate booking - same user+event (generates DEBUG + WARNING)
  http.post(
    `${BASE_URL}:3003/bookings`,
    JSON.stringify({ eventId: '1', userId: 'u1' }),
    opts
  );
  sleep(0.3);

  // 13. Missing booking fields (generates DEBUG + ERROR)
  http.post(
    `${BASE_URL}:3003/bookings`,
    JSON.stringify({}),
    opts
  );
  sleep(0.5);
}
