const express = require('express');
const { connectProducer } = require('./kafka');
const { register } = require('./metrics');
const routes = require('./routes');

const app = express();
const PORT = process.env.PORT || 3002;

app.use(express.json());

app.use((req, res, next) => {
  console.log(`[event-service] ${req.method} ${req.path}`);
  next();
});

app.use('/', routes);

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

async function start() {
  await connectProducer();
  app.listen(PORT, () => {
    console.log(`[event-service] Running on port ${PORT}`);
  });
}

start().catch(console.error);
