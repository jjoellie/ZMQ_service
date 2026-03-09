"""
Part 2 - Pub/Sub: Dashboard (SUB) with Tkinter UI

Subscribes to sensor data from the broker and displays the most recent
X seconds of readings.  The topic (e.g. "temperature" or "humidity") and
the time window can be changed live through the GUI.

Usage:
  python dashboard.py
"""

import threading
import time
from collections import deque
from datetime import datetime
from typing import Deque, Optional, Tuple

import tkinter as tk
from tkinter import ttk

import zmq

BROKER_ADDRESS = "tcp://localhost:5561"
AVAILABLE_TOPICS = ["temperature", "humidity"]
DEFAULT_TOPIC = "temperature"
DEFAULT_WINDOW_SECONDS = 30
POLL_TIMEOUT_MS = 100
UI_REFRESH_MS = 1000


class Dashboard:
    """Real-time sensor dashboard with topic selection and time-window filtering."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sensor Dashboard")
        self.root.geometry("640x520")
        self.root.resizable(True, True)

        self.context = zmq.Context()
        self.socket: Optional[zmq.Socket] = None  # set by _connect_socket

        self.current_topic: str = DEFAULT_TOPIC
        self.time_window: int = DEFAULT_WINDOW_SECONDS
        # (timestamp, sensor_id, value)
        self.data: Deque[Tuple[float, str, str]] = deque()

        self._socket_lock = threading.Lock()
        self.running = True

        self._setup_ui()
        self._connect_socket(DEFAULT_TOPIC)
        self._start_receiver()
        self._schedule_ui_refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # ── Control bar ──────────────────────────────────────────────
        ctrl = tk.Frame(self.root, pady=6)
        ctrl.pack(fill=tk.X, padx=10)

        tk.Label(ctrl, text="Topic:").pack(side=tk.LEFT)
        self.topic_var = tk.StringVar(value=DEFAULT_TOPIC)
        topic_cb = ttk.Combobox(
            ctrl,
            textvariable=self.topic_var,
            values=AVAILABLE_TOPICS,
            state="readonly",
            width=14,
        )
        topic_cb.pack(side=tk.LEFT, padx=(4, 16))
        topic_cb.bind("<<ComboboxSelected>>", self._on_topic_change)

        tk.Label(ctrl, text="Show last (s):").pack(side=tk.LEFT)
        self.window_var = tk.StringVar(value=str(DEFAULT_WINDOW_SECONDS))
        tk.Entry(ctrl, textvariable=self.window_var, width=6).pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="Apply", command=self._on_window_apply).pack(side=tk.LEFT)

        # ── Status label ──────────────────────────────────────────────
        self.status_var = tk.StringVar(value=f"Subscribed to: {DEFAULT_TOPIC}")
        tk.Label(self.root, textvariable=self.status_var, fg="blue").pack(
            anchor=tk.W, padx=10
        )

        # ── Data area ─────────────────────────────────────────────────
        tk.Label(
            self.root, text="Received readings (newest first):", font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, padx=10, pady=(4, 0))

        text_frame = tk.Frame(self.root)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            text_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)

    # ------------------------------------------------------------------
    # Socket management
    # ------------------------------------------------------------------

    def _connect_socket(self, topic: str) -> None:
        """(Re-)connect the SUB socket and subscribe to *topic*."""
        with self._socket_lock:
            if self.socket is not None:
                self.socket.close()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(BROKER_ADDRESS)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        print(f"Dashboard subscribed to: {topic}")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_topic_change(self, _event: object = None) -> None:
        new_topic = self.topic_var.get()
        if new_topic == self.current_topic:
            return
        self.current_topic = new_topic
        self.data.clear()
        self.status_var.set(f"Subscribed to: {new_topic}")
        self._connect_socket(new_topic)

    def _on_window_apply(self) -> None:
        try:
            value = int(self.window_var.get())
            if value > 0:
                self.time_window = value
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Background receiver thread
    # ------------------------------------------------------------------

    def _start_receiver(self) -> None:
        t = threading.Thread(target=self._receive_loop, daemon=True)
        t.start()

    def _receive_loop(self) -> None:
        poller = zmq.Poller()
        while self.running:
            with self._socket_lock:
                sock = self.socket
            poller.register(sock, zmq.POLLIN)
            try:
                events = dict(poller.poll(POLL_TIMEOUT_MS))
                if sock in events:
                    raw = sock.recv_string()
                    # expected format: "<topic> <sensor_id> <value>"
                    parts = raw.split(" ", 2)
                    if len(parts) == 3:
                        _topic, sensor_id, value = parts
                        self.data.append((time.time(), sensor_id, value))
            except zmq.ZMQError:
                pass
            finally:
                poller.unregister(sock)

    # ------------------------------------------------------------------
    # UI refresh
    # ------------------------------------------------------------------

    def _schedule_ui_refresh(self) -> None:
        self._refresh_display()
        self.root.after(UI_REFRESH_MS, self._schedule_ui_refresh)

    def _refresh_display(self) -> None:
        cutoff = time.time() - self.time_window
        # Discard old entries
        self.data = deque(entry for entry in self.data if entry[0] >= cutoff)

        unit = "°C" if self.current_topic == "temperature" else "%"
        lines = []
        for timestamp, sensor_id, value in reversed(list(self.data)):
            ts_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            lines.append(
                f"[{ts_str}]  Sensor {sensor_id:>4}  →  {value}{unit}"
            )

        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, "\n".join(lines) if lines else "(no data yet)")
        self.text_area.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def on_close(self) -> None:
        self.running = False
        if self.socket is not None:
            self.socket.close()
        self.context.term()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = Dashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
