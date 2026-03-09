"""
Part 1 - Request-Reply: Client (REQ)

Sends requests to multiple servers with a 1-second timeout per server.
If a server does not respond within 1 second, the client tries the next one.

Usage:
  python client.py
"""

import zmq

SERVER_ADDRESSES = [
    "tcp://localhost:5550",
    "tcp://localhost:5551",
    "tcp://localhost:5552",
]

TIMEOUT_MS = 1000  # 1 second


def send_request(request: str) -> None:
    context = zmq.Context()

    print(f"Sending request: '{request}'")

    for index, address in enumerate(SERVER_ADDRESSES):
        print(f"  Trying server {index + 1} at {address} ...")

        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)
        socket.connect(address)
        socket.send_string(request)

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        events = dict(poller.poll(TIMEOUT_MS))

        if socket in events and events[socket] == zmq.POLLIN:
            reply = socket.recv_string()
            print(f"  Received reply: {reply}")
            socket.close()
            context.term()
            return

        print(f"  No reply from server {index + 1} within {TIMEOUT_MS}ms, trying next...")
        socket.close()

    print("No server responded to the request.")
    context.term()


def main() -> None:
    requests = [
        "What is the time?",
        "Hello!",
        "Ping",
    ]
    for req in requests:
        send_request(req)
        print()


if __name__ == "__main__":
    main()
