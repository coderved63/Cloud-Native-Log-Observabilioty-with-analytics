const { Kafka } = require('kafkajs');

const SERVICE_NAME = 'auth-service';
const KAFKA_BROKER = process.env.KAFKA_BROKER || 'localhost:9092';
const TOPIC = process.env.LOG_TOPIC || 'logs_topic';

const kafka = new Kafka({
  clientId: SERVICE_NAME,
  brokers: [KAFKA_BROKER],
  retry: { retries: 10, initialRetryTime: 3000 },
});

const producer = kafka.producer();

async function connectProducer() {
  let retries = 0;
  while (retries < 10) {
    try {
      await producer.connect();
      console.log(`[${SERVICE_NAME}] Kafka producer connected`);
      return;
    } catch (err) {
      retries++;
      console.error(`[${SERVICE_NAME}] Kafka connect attempt ${retries} failed: ${err.message}`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  console.error(`[${SERVICE_NAME}] Could not connect to Kafka after ${retries} retries`);
}

async function sendLog(level, message) {
  try {
    const logEvent = {
      service: SERVICE_NAME,
      level,
      message,
      timestamp: new Date().toISOString(),
    };
    await producer.send({
      topic: TOPIC,
      messages: [{ value: JSON.stringify(logEvent) }],
    });
  } catch (err) {
    console.error(`[${SERVICE_NAME}] Failed to send log to Kafka: ${err.message}`);
  }
}

module.exports = { connectProducer, sendLog };
