"""
Part 4 - Dealer/Router: Chat Broker (ROUTER)

Manages chatrooms and routes messages between clients.

Protocol (all frames are JSON-encoded strings):

  Client → Broker  (single frame after the empty DEALER delimiter):
    {"action": "join",    "room": "<name>", "name": "<display_name>"}
    {"action": "leave",   "room": "<name>", "name": "<display_name>"}
    {"action": "message", "room": "<name>", "name": "<display_name>", "content": "<text>"}

  Broker → Client  (single frame):
    {"action": "joined",  "room": "<name>", "message": "<info>"}
    {"action": "left",    "room": "<name>", "message": "<info>"}
    {"action": "message", "room": "<name>", "sender": "<name>",       "content": "<text>"}

Usage:
  python broker.py
"""

import json

import zmq

BIND_ADDRESS = "tcp://*:5580"


def main() -> None:
    context = zmq.Context()
    router = context.socket(zmq.ROUTER)
    router.bind(BIND_ADDRESS)

    print(f"Chat broker started on {BIND_ADDRESS}")

    # client_id (bytes) → set of room names
    client_rooms: dict[bytes, set[str]] = {}
    # room name → set of client_ids
    room_clients: dict[str, set[bytes]] = {}

    try:
        while True:
            # ROUTER receives: [identity, empty, data]  (DEALER auto-adds empty)
            frames = router.recv_multipart()
            if len(frames) < 2:
                continue

            client_id = frames[0]
            try:
                payload = json.loads(frames[-1].decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            action = payload.get("action")
            room = payload.get("room", "")
            display_name = payload.get("name", client_id.hex()[:8])

            if action == "join":
                client_rooms.setdefault(client_id, set()).add(room)
                room_clients.setdefault(room, set()).add(client_id)
                print(f"  JOIN  [{room}] ← {display_name}")
                _send(router, client_id, {
                    "action": "joined",
                    "room": room,
                    "message": f"You joined '{room}'",
                })
                # Notify other members
                _broadcast(router, room_clients[room] - {client_id}, {
                    "action": "message",
                    "room": room,
                    "sender": "System",
                    "content": f"{display_name} joined the room",
                })

            elif action == "leave":
                client_rooms.get(client_id, set()).discard(room)
                room_clients.get(room, set()).discard(client_id)
                print(f"  LEAVE [{room}] ← {display_name}")
                _send(router, client_id, {
                    "action": "left",
                    "room": room,
                    "message": f"You left '{room}'",
                })
                _broadcast(router, room_clients.get(room, set()), {
                    "action": "message",
                    "room": room,
                    "sender": "System",
                    "content": f"{display_name} left the room",
                })

            elif action == "message":
                content = payload.get("content", "")
                print(f"  MSG   [{room}] {display_name}: {content}")
                recipients = room_clients.get(room, set())
                _broadcast(router, recipients, {
                    "action": "message",
                    "room": room,
                    "sender": display_name,
                    "content": content,
                })

    except KeyboardInterrupt:
        print("\nBroker shutting down")
    finally:
        router.close()
        context.term()


def _send(router: zmq.Socket, client_id: bytes, payload: dict) -> None:
    router.send_multipart([client_id, json.dumps(payload).encode()])


def _broadcast(router: zmq.Socket, recipients: set[bytes], payload: dict) -> None:
    encoded = json.dumps(payload).encode()
    for recipient_id in recipients:
        router.send_multipart([recipient_id, encoded])


if __name__ == "__main__":
    main()
