"""
logger.py
=========
Kapselt die Log-Anzeige im UI. Trennt Logging-Logik vom Hauptmodul.
Thread-sicher (wichtig für MQTT-Callbacks aus Fremd-Threads).
"""

import asyncio
from datetime import datetime
import omni.ui as ui

from .constants import (
    MAX_LOG_LINES, CLR_TEXT_FAINT, CLR_ACCENT,
    CLR_RED, CLR_GREEN
)


class Logger:
    """Verwaltet eine Liste von Log-Einträgen und rendert sie in einen UI-Container."""

    def __init__(self, log_container, loop):
        # UI-Container (ui.VStack), in den die Zeilen gezeichnet werden
        self._log_container = log_container
        # asyncio-Loop, um aus Fremd-Threads thread-safe nachzuladen
        self._loop = loop
        # Liste von Tupeln (timestamp, message, level)
        self._log_lines = []

    # ---------------------------------------------------------------
    def log(self, message, level="log"):
        """Fügt eine Log-Zeile hinzu und triggert das Neuzeichnen."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_lines.append((ts, message, level))

        # Liste begrenzen
        if len(self._log_lines) > MAX_LOG_LINES:
            self._log_lines = self._log_lines[-MAX_LOG_LINES:]

        # Thread-sicheres Rebuild: falls in async-Loop -> direkt,
        # sonst über call_soon_threadsafe.
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(asyncio.create_task, self._rebuild())
        except RuntimeError:
            # Kein Loop -> nur Konsole
            print(f"[MazeRunner] [{ts}] {message}")

    # ---------------------------------------------------------------
    async def _rebuild(self):
        """Zeichnet alle Log-Zeilen im Container neu."""
        # Kleines Yield, damit UI Zeit hat
        await asyncio.sleep(0.01)
        self._log_container.clear()

        color_map = {
            "log":   CLR_TEXT_FAINT,
            "info":  CLR_ACCENT,
            "error": CLR_RED,
            "ok":    CLR_GREEN,
        }
        with self._log_container:
            for ts, msg, level in self._log_lines:
                clr = color_map.get(level, CLR_TEXT_FAINT)
                ui.Label(
                    f"  {ts}   {msg}",
                    style={"font_size": 10, "color": clr},
                    height=14,
                )

    # ---------------------------------------------------------------
    def clear(self):
        """Leert das Log."""
        self._log_lines = []
        asyncio.ensure_future(self._rebuild())
