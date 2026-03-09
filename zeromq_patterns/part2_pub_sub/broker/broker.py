"""
Part 2 - Pub/Sub: Broker (XSUB → XPUB)

Acts as a message broker between sensors (publishers) and the dashboard (subscriber).
Uses ZMQ's built-in proxy for efficient message forwarding with subscription forwarding.

  Frontend (XSUB) binds on port 5560 — sensors connect here.
  Backend  (XPUB) binds on port 5561 — dashboard connects here.

Usage:
  python broker.py
"""

import zmq


def main() -> None:
    context = zmq.Context()

    # Sensors publish to the frontend
    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://*:5560")

    # Dashboard subscribes from the backend
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://*:5561")

    print("Pub/Sub broker started")
    print("  Frontend (sensors  → broker) : tcp://*:5560")
    print("  Backend  (broker → dashboard): tcp://*:5561")

    try:
        # proxy forwards messages and subscription notifications automatically
        zmq.proxy(frontend, backend)
    except KeyboardInterrupt:
        print("\nBroker shutting down")
    finally:
        frontend.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()
