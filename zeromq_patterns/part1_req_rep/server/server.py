"""
Part 1 - Request-Reply: Server (REP)

Start multiple servers on different ports:
  python server.py 1 5550
  python server.py 2 5551
  python server.py 3 5552
"""

import sys
import time
import zmq


def main(server_id: str, port: int) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{port}")

    print(f"Server {server_id} listening on port {port}")

    try:
        while True:
            message = socket.recv_string()
            print(f"[Server {server_id}] Received: {message}")
            # Simulate some processing time
            time.sleep(0.1)
            reply = f"Reply from Server {server_id} (port {port})"
            socket.send_string(reply)
            print(f"[Server {server_id}] Sent reply: {reply}")
    except KeyboardInterrupt:
        print(f"\nServer {server_id} shutting down")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    srv_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    srv_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5550
    main(srv_id, srv_port)
