import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=["172.18.0.4:9092"],
    value_serializer=lambda message: json.dumps(message).encode('utf-8')
)

count = 0

# Generate and send messages in a loop with a 2-second interval
while True:
    # Generate random values based on the pattern
    messages = {
        "id": count,
        "posex": float("{0:.5f}".format(random.uniform(0.9, 1.7))),  # Similar to the range [0.9, 1.7]
        "posey": float("{0:.5f}".format(random.uniform(2.2, 2.4))),  # Similar to the range [2.2, 2.4]
        "posez": float("{0:.5f}".format(0.0)),                      # Always 0.0
        "orientx": float("{0:.5f}".format(0.0)),                    # Always 0.0
        "orienty": float("{0:.5f}".format(0.0)),                    # Always 0.0
        "orientz": float("{0:.5f}".format(random.uniform(-1.0, -0.8))),  # Similar to the range [-1.0, -0.8]
        "orientw": float("{0:.5f}".format(random.uniform(0.2, 0.45)))   # Similar to the range [0.2, 0.45]
    }

    # Print and send the message
    print(f"Producing message {datetime.now()} Message :\n {str(messages)}")
    producer.send("rosmsgs", messages)

    # Increment the message id
    count += 1

    # Wait for 2 seconds before sending the next message
    time.sleep(0.2)
