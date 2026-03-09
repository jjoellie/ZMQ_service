"""
Part 2 - Pub/Sub: Temperature Sensor (PUB)

Publishes temperature readings to the broker.

Usage:
  python temperature_sensor.py 1
  python temperature_sensor.py 2
"""

import random
import sys
import time

import zmq

TOPIC = "temperature"
BROKER_ADDRESS = "tcp://localhost:5560"
PUBLISH_INTERVAL = 2  # seconds


def main(sensor_id: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect(BROKER_ADDRESS)

    # Brief pause so the broker and subscribers can set up
    time.sleep(0.5)

    print(f"Temperature sensor {sensor_id} started — publishing to {BROKER_ADDRESS}")

    try:
        while True:
            temperature = round(random.uniform(15.0, 35.0), 1)
            message = f"{TOPIC} {sensor_id} {temperature}"
            socket.send_string(message)
            print(f"[Temp Sensor {sensor_id}] Published: {temperature}°C")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print(f"\nTemperature sensor {sensor_id} shutting down")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else "1"
    main(sid)
