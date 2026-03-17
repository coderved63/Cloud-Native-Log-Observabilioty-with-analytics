from prometheus_client import Counter, Gauge

logs_processed_total = Counter(
    'logs_processed_total',
    'Total number of log messages processed',
    ['service', 'level']
)

logs_processing_errors_total = Counter(
    'logs_processing_errors_total',
    'Total number of log processing errors',
    ['reason']
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Estimated Kafka consumer lag',
    ['partition']
)
