"""
Part 4 - Dealer/Router: Chat Client (DEALER)

Connects to the chat broker and lets the user join chatrooms and exchange
messages with other clients.

Commands (typed at the '> ' prompt):
  join  <room>          — join a chatroom
  leave <room>          — leave a chatroom
  msg   <room> <text>   — send a message to everyone in a room
  rooms                 — list joined rooms
  quit                  — disconnect and exit

Usage:
  python client.py Alice
  python client.py Bob
"""

import json
import sys
import threading

import zmq

BROKER_ADDRESS = "tcp://localhost:5580"
POLL_TIMEOUT_MS = 100


def main(display_name: str) -> None:
    context = zmq.Context()
    dealer = context.socket(zmq.DEALER)
    dealer.connect(BROKER_ADDRESS)

    print(f"Connected to broker as '{display_name}'")
    print("Commands: join <room> | leave <room> | msg <room> <text> | rooms | quit\n")

    joined_rooms: set[str] = set()
    running = threading.Event()
    running.set()

    def receive_loop() -> None:
        poller = zmq.Poller()
        poller.register(dealer, zmq.POLLIN)
        while running.is_set():
            try:
                events = dict(poller.poll(POLL_TIMEOUT_MS))
                if dealer in events:
                    data = dealer.recv()
                    msg = json.loads(data.decode())
                    _print_message(msg)
            except zmq.ZMQError:
                break

    recv_thread = threading.Thread(target=receive_loop, daemon=True)
    recv_thread.start()

    try:
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break

            if not line:
                continue

            if line.startswith("join "):
                room = line[5:].strip()
                if room:
                    _send(dealer, {"action": "join", "room": room, "name": display_name})
                    joined_rooms.add(room)

            elif line.startswith("leave "):
                room = line[6:].strip()
                if room:
                    _send(dealer, {"action": "leave", "room": room, "name": display_name})
                    joined_rooms.discard(room)

            elif line.startswith("msg "):
                rest = line[4:].strip()
                parts = rest.split(" ", 1)
                if len(parts) == 2:
                    room, content = parts
                    _send(dealer, {
                        "action": "message",
                        "room": room,
                        "name": display_name,
                        "content": content,
                    })
                else:
                    print("Usage: msg <room> <message text>")

            elif line == "rooms":
                if joined_rooms:
                    print("Joined rooms:", ", ".join(sorted(joined_rooms)))
                else:
                    print("(not in any room)")

            elif line == "quit":
                break

            else:
                print("Unknown command. Type join/leave/msg/rooms/quit")

    except KeyboardInterrupt:
        pass
    finally:
        running.clear()
        dealer.close()
        context.term()
        print(f"\n{display_name} disconnected.")


def _send(dealer: zmq.Socket, payload: dict) -> None:
    dealer.send(json.dumps(payload).encode())


def _print_message(msg: dict) -> None:
    action = msg.get("action")
    room = msg.get("room", "")
    if action == "joined":
        print(f"\n[System] {msg.get('message', '')}")
    elif action == "left":
        print(f"\n[System] {msg.get('message', '')}")
    elif action == "message":
        sender = msg.get("sender", "?")
        content = msg.get("content", "")
        print(f"\n[{room}] {sender}: {content}")
    print("> ", end="", flush=True)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Anonymous"
    main(name)
