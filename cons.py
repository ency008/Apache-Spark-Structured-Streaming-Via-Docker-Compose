from kafka import KafkaConsumer
import json

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'odom',  # The Kafka topic to subscribe to
    bootstrap_servers=['172.18.0.4:9092'],
    auto_offset_reset='earliest',  # Start reading at the earliest available message
    enable_auto_commit=True,
    group_id='my-group',  # Consumer group id
    value_deserializer=lambda message: json.loads(message.decode('utf-8'))
)

# Consume messages
for message in consumer:
    print(f"Received message: {message.value}")

    # If you want to stop after receiving a message, you can break the loop
    # break
