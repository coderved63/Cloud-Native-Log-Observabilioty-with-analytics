import json
import time
from kafka import KafkaConsumer


class LogConsumer:
    def __init__(self, broker: str, topic: str, group_id: str = 'log-processor-group'):
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.consumer = None

    def connect(self, max_retries: int = 10, initial_delay: float = 5.0):
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                self.consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=[self.broker],
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id=self.group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                )
                print(f"[consumer] Connected to Kafka broker {self.broker}, topic={self.topic}")
                return
            except Exception as e:
                print(f"[consumer] Connection attempt {attempt} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 1.5, 30.0)
        raise RuntimeError(f"Could not connect to Kafka after {max_retries} attempts")

    def consume(self):
        for message in self.consumer:
            yield message.value, message.partition, message.offset

    def close(self):
        if self.consumer:
            self.consumer.close()
            print("[consumer] Kafka consumer closed")
