"""
Part 3 - Push/Pull: Logger (PUSH)

Sends batches of warning/error log lines into the pipeline.
Multiple analyzers pull from the same socket and each processes a share
of the log entries (round-robin load distribution).

Usage:
  python logger.py
"""

import random
import time

import zmq

BIND_ADDRESS = "tcp://*:5570"
BATCH_INTERVAL = 3  # seconds between batches
MIN_BATCH = 3
MAX_BATCH = 8

LOG_TEMPLATES = [
    "WARNING: High CPU usage detected — value: {value}%",
    "ERROR:   Database connection failed — attempt: {value}",
    "WARNING: Memory usage above threshold — percentage: {value}%",
    "ERROR:   Request timeout — duration: {value}ms",
    "WARNING: Disk space low — remaining: {value}MB",
    "ERROR:   Service unavailable — code: {value}",
    "WARNING: Too many open file descriptors — count: {value}",
    "ERROR:   Authentication failed — user_id: {value}",
]


def make_log_line() -> str:
    template = random.choice(LOG_TEMPLATES)
    value = random.randint(1, 100)
    return template.format(value=value)


def main() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind(BIND_ADDRESS)

    print(f"Logger started — pushing logs on {BIND_ADDRESS}")
    print("(Start one or more analyzers to process the logs)\n")

    batch_num = 0
    try:
        while True:
            batch_num += 1
            batch_size = random.randint(MIN_BATCH, MAX_BATCH)
            print(f"── Batch #{batch_num}  ({batch_size} entries) ──────────────")
            for _ in range(batch_size):
                log_line = make_log_line()
                socket.send_string(log_line)
                print(f"  PUSH → {log_line}")
            time.sleep(BATCH_INTERVAL)
    except KeyboardInterrupt:
        print("\nLogger shutting down")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
