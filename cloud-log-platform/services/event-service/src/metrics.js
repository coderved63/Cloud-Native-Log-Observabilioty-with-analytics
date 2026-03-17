const client = require('prom-client');

client.collectDefaultMetrics({ prefix: 'event_service_' });

const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code', 'service'],
});

const httpErrorsTotal = new client.Counter({
  name: 'http_errors_total',
  help: 'Total number of HTTP errors',
  labelNames: ['route', 'service'],
});

const kafkaMessagesSentTotal = new client.Counter({
  name: 'kafka_messages_sent_total',
  help: 'Total Kafka messages sent',
  labelNames: ['service'],
});

module.exports = {
  register: client.register,
  httpRequestsTotal,
  httpErrorsTotal,
  kafkaMessagesSentTotal,
};
