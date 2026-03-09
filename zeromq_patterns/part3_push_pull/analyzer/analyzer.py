"""
Part 3 - Push/Pull: Log Analyzer (PULL)

Connects to the logger's PUSH socket, receives log entries, and prints
a human-readable analysis.  Multiple analyzers can run in parallel; ZMQ
distributes log entries round-robin across all connected analyzers.

Usage:
  python analyzer.py 1
  python analyzer.py 2
"""

import re
import sys

import zmq

LOGGER_ADDRESS = "tcp://localhost:5570"


def _extract_value(log_line: str) -> int:
    """Return the last integer found in *log_line*, or 0 if none."""
    numbers = re.findall(r"\d+", log_line)
    return int(numbers[-1]) if numbers else 0


def analyze(log_line: str) -> str:
    """Return a human-readable verdict for a single log entry."""
    value = _extract_value(log_line)
    is_error = log_line.startswith("ERROR")

    if is_error:
        if value > 75:
            verdict = "🔴 CRITICAL   — Immediate action required!"
        elif value > 50:
            verdict = "🟠 HIGH       — Action required soon"
        else:
            verdict = "🟡 MEDIUM     — Monitor the situation"
    else:  # WARNING
        if value > 80:
            verdict = "🟠 ESCALATING — Approaching critical level"
        elif value > 50:
            verdict = "🟡 MODERATE   — Keep monitoring"
        else:
            verdict = "🟢 LOW        — Within acceptable range"

    return f"{verdict}\n         └─ {log_line}"


def main(analyzer_id: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect(LOGGER_ADDRESS)

    print(f"Analyzer {analyzer_id} started — pulling from {LOGGER_ADDRESS}\n")

    try:
        while True:
            log_line = socket.recv_string()
            result = analyze(log_line)
            print(f"[Analyzer {analyzer_id}] {result}\n")
    except KeyboardInterrupt:
        print(f"\nAnalyzer {analyzer_id} shutting down")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    aid = sys.argv[1] if len(sys.argv) > 1 else "1"
    main(aid)
