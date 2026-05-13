"""
mqtt_handler.py
===============
Wrapper um den WebSocketMQTTClient.
Bindet eingehende Nachrichten an die NodeManager-Statusanzeige.
"""

import asyncio
import omni.usd

from .websocket_mqtt import WebSocketMQTTClient


class MQTTHandler:
    """Verbindet eingehende MQTT-Nachrichten mit dem NodeManager."""

    def __init__(self, node_manager, logger, loop, status_setter):
        self._nm = node_manager
        self._logger = logger
        self._loop = loop
        self._set_status = status_setter
        self._ws_mqtt = None

    # ---------------------------------------------------------------
    def start(self):
        """Startet die WebSocket-Verbindung."""
        self._logger.log("Starte WS-MQTT ...", "info")
        topics = [f"/PlcNode/Get/{n.get('node_id')}" for n in self._nm.nodes]

        async def _start():
            self._ws_mqtt = WebSocketMQTTClient(
                on_message_callback=self._on_message,
                topic_list=topics,
            )
            await self._ws_mqtt.connect()
            if self._ws_mqtt.connected:
                self._set_status("MQTT Verbunden (WS)")

        asyncio.ensure_future(_start())

    # ---------------------------------------------------------------
    def stop(self):
        """Trennt die Verbindung."""
        self._logger.log("WS-MQTT wird gestoppt ...", "info")
        if self._ws_mqtt:
            asyncio.ensure_future(self._ws_mqtt.disconnect())
            self._ws_mqtt = None
        self._set_status("MQTT Inaktiv")

    # ---------------------------------------------------------------
    def _on_message(self, topic, payload_raw):
        """
        Callback aus dem MQTT-Thread.
        Wir schieben die UI-Arbeit thread-safe in den Haupt-Loop.
        """
        payload = payload_raw.strip().lower()
        node_id = topic.split("/")[-1]
        val = payload in ("true", "1", "on")

        def handle():
            old = self._nm.node_values.get(node_id)
            if old != val:
                self._nm.node_values[node_id] = val
                self._nm.set_display(node_id, val)

                # Spezialfall: Stepper dreht weiter
                if node_id == "Start_Stepper_Set" and val:
                    self._stepper_increment()

            self._logger.log(f"WS-MQTT: {node_id} = {val}", "log")

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(handle)

    # ---------------------------------------------------------------
    def _stepper_increment(self):
        """Erhöht die Stepper-Zielposition um -60°."""
        prim_path = "/World/Production_Line/Drehscheibe/RevoluteJoint"
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            return

        attr = prim.GetAttribute("drive:angular:physics:targetPosition")
        if not attr.IsValid():
            attr = prim.GetAttribute("drive:angular:targetPosition")
        if attr.IsValid():
            cur = attr.Get() or 0.0
            new_val = cur - 60.0
            attr.Set(new_val)
            self._logger.log(f"Stepper dreht weiter auf {new_val}°", "ok")
