"""
api_client.py
=============
Kapselt alle REST-API-Aufrufe gegen den DigitalTwinService.
- SET (Toggle und Impuls)
- Initial Polling aller Nodes
"""

import asyncio
import aiohttp

from .constants import API_URL_GET, API_URL_SET, API_KEY


class APIClient:
    """Asynchroner HTTP-Client für die DigitalTwin-API."""

    def __init__(self, node_manager, logger, status_setter):
        self._nm = node_manager        # Zugriff auf node_values / Labels
        self._logger = logger
        self._set_status = status_setter   # Callable(str, color) für Statusbar

    # ---------------------------------------------------------------
    async def send_set(self, node_id, value, sim_mode):
        """Setzt einen Boolean-Wert via API. Im SIM-Modus nur lokal."""
        if sim_mode:
            self._nm.node_values[node_id] = value
            self._nm.set_display(node_id, value)
            return

        headers = {"X-API-KEY": API_KEY, "accept": "application/json"}
        params = {
            "NodeName": node_id,
            "Value":    str(value).lower(),
            "user":     "admin",
            "apiKey":   API_KEY,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL_SET, params=params, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5), ssl=False
                ) as resp:
                    if resp.status == 200:
                        self._nm.node_values[node_id] = value
                        self._nm.set_display(node_id, value)
                        self._logger.log(f"Set OK: {node_id} = {value}", "ok")
                    else:
                        self._logger.log(f"Set Fehler {resp.status}: {node_id}", "error")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.log(f"Set Exception: {node_id} | {e}", "error")

    # ---------------------------------------------------------------
    async def send_impulse(self, node_id, sim_mode):
        """Sendet einen Impuls (true → 300ms warten → false)."""
        if sim_mode:
            return

        headers = {"X-API-KEY": API_KEY, "accept": "application/json"}
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "NodeName": node_id, "Value": "true",
                    "user": "admin", "apiKey": API_KEY,
                }
                async with session.post(
                    API_URL_SET, params=params, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5), ssl=False
                ) as resp:
                    if resp.status == 200:
                        self._logger.log(f"Impulse API true: {node_id}", "ok")

                await asyncio.sleep(0.3)

                params["Value"] = "false"
                async with session.post(
                    API_URL_SET, params=params, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5), ssl=False
                ) as resp:
                    if resp.status == 200:
                        self._logger.log(f"Impulse API reset: {node_id}", "log")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.log(f"Impulse API Fehler: {node_id} | {e}", "error")

    # ---------------------------------------------------------------
    async def initial_poll(self, sim_mode):
        """Holt einmalig alle Node-Werte, damit die UI nach LIVE-Wechsel stimmt."""
        if sim_mode:
            return

        self._set_status("Initial Polling...")
        self._logger.log("Initial Polling aller Nodes gestartet...", "info")

        headers = {"X-API-KEY": API_KEY, "accept": "application/json"}
        try:
            async with aiohttp.ClientSession() as session:
                for node in self._nm.nodes:
                    node_id = node.get("node_id")
                    if not node_id:
                        continue

                    params = {
                        "NodeName": node_id, "user": "admin", "apiKey": API_KEY,
                    }
                    try:
                        async with session.get(
                            API_URL_GET, params=params, headers=headers,
                            timeout=aiohttp.ClientTimeout(total=3), ssl=False
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                raw = (
                                    str(data.get("value", "")).lower()
                                    if isinstance(data, dict) else str(data).lower()
                                )
                                val = raw in ("true", "1", "on")
                                self._nm.node_values[node_id] = val
                                self._nm.set_display(node_id, val)
                                self._logger.log(f"Poll: {node_id} = {val}", "ok")
                            else:
                                self._logger.log(
                                    f"Poll Fehler {resp.status}: {node_id}", "error"
                                )
                    except Exception as e:
                        self._logger.log(f"Poll Exception: {node_id} | {e}", "error")

            self._set_status("MQTT Verbunden")
            self._logger.log("Initial Polling abgeschlossen ✅", "ok")
        except Exception as e:
            self._set_status("Polling Fehler")
            self._logger.log(f"Initial Poll Gesamtfehler: {e}", "error")
