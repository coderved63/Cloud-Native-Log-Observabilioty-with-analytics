import os
import json
from prometheus_client import start_http_server
from consumer import LogConsumer
from storage import MongoStorage
from metrics_server import logs_processed_total, logs_processing_errors_total, kafka_consumer_lag

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
LOG_TOPIC = os.getenv('LOG_TOPIC', 'logs_topic')
METRICS_PORT = int(os.getenv('METRICS_PORT', '8000'))


def classify_level(level: str) -> str:
    level = level.upper()
    if level == 'WARN':
        return 'WARNING'
    if level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        return level
    return 'INFO'


def main():
    print(f"[main] Starting log processor")
    print(f"[main] Kafka={KAFKA_BROKER}, Mongo={MONGO_URI}, Topic={LOG_TOPIC}")

    start_http_server(METRICS_PORT)
    print(f"[main] Prometheus metrics server started on port {METRICS_PORT}")

    storage = MongoStorage(uri=MONGO_URI)

    consumer = LogConsumer(broker=KAFKA_BROKER, topic=LOG_TOPIC)
    consumer.connect()

    print("[main] Consuming logs...")
    for log_doc, partition, offset in consumer.consume():
        try:
            service = log_doc.get('service', 'unknown')
            level = classify_level(log_doc.get('level', 'INFO'))
            message = log_doc.get('message', '')
            timestamp = log_doc.get('timestamp', '')

            doc = {
                'service': service,
                'level': level,
                'message': message,
                'timestamp': timestamp,
            }

            inserted_id = storage.insert_log(doc)
            logs_processed_total.labels(service=service, level=level).inc()
            kafka_consumer_lag.labels(partition=str(partition)).set(0)

            print(f"[main] Stored log id={inserted_id} service={service} level={level}")

        except Exception as e:
            logs_processing_errors_total.labels(reason=type(e).__name__).inc()
            print(f"[main] Error processing log: {e}")


if __name__ == '__main__':
    main()
