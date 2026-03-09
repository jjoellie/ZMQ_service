"""
Part 2 - Pub/Sub: Humidity Sensor (PUB)

Publishes humidity readings to the broker.

Usage:
  python humidity_sensor.py
"""

import random
import time

import zmq

TOPIC = "humidity"
BROKER_ADDRESS = "tcp://localhost:5560"
PUBLISH_INTERVAL = 3  # seconds


def main() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect(BROKER_ADDRESS)

    # Brief pause so the broker and subscribers can set up
    time.sleep(0.5)

    print(f"Humidity sensor started — publishing to {BROKER_ADDRESS}")

    try:
        while True:
            humidity = round(random.uniform(30.0, 90.0), 1)
            message = f"{TOPIC} 1 {humidity}"
            socket.send_string(message)
            print(f"[Humidity Sensor] Published: {humidity}%")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nHumidity sensor shutting down")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
