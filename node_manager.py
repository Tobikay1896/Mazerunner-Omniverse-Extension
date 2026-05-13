"""
node_manager.py
===============
Verwaltet:
- Laden der Nodes aus nodes_db.json
- Speicherung von Node-Werten (node_values)
- Status-Anzeige in den UI-Labels
- USD-Attributzugriff (lesen/schreiben)
"""

import os
import json
import omni.usd
import omni.ui as ui
from pxr import Sdf

from .constants import (
    CLR_BG_ROW_A, CLR_BG_ROW_B, CLR_TEXT, CLR_TEXT_DIM, CLR_TEXT_FAINT,
    CLR_ACCENT, CLR_ORANGE, CLR_RED, CLR_GREEN
)


class NodeManager:
    """Lädt und verwaltet alle Maschinen-Nodes der Extension."""

    def __init__(self, json_path, logger):
        self.json_path = json_path
        self._logger = logger

        # Datenhaltung
        self.nodes = []                  # Liste aus JSON
        self.node_labels = {}            # node_id -> ui.Label
        self.node_values = {}            # node_id -> bool
        self._impulse_positions = {}     # node_id -> float (akkumulierte Schritte)
        self._impulse_armed = {}         # node_id -> bool
        self._velocity_running = {}      # node_id -> bool

        # Container für die UI-Liste (von außen gesetzt)
        self.list_container = None
        self.node_count_label = None
        self._node_buttons = []

    # ---------------------------------------------------------------
    def load(self, on_button_clicked):
        """
        Lädt die nodes_db.json und baut die Zeilen im UI auf.
        `on_button_clicked(node_id)` wird beim Klick aufgerufen.
        """
        if self.list_container is None:
            return

        # UI/Datenstrukturen zurücksetzen
        self.list_container.clear()
        self.node_labels.clear()
        self._impulse_positions.clear()
        self._impulse_armed.clear()
        self._velocity_running.clear()
        self._node_buttons = []

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.nodes = json.load(f).get("nodes", [])
        except Exception as e:
            self._logger.log(f"JSON Fehler: {e}", "error")
            return

        self._logger.log(f"JSON geladen: {len(self.nodes)} Nodes", "info")
        if self.node_count_label:
            self.node_count_label.text = f"{len(self.nodes)} Nodes"

        # Initialwerte je nach Mode
        for node in self.nodes:
            node_id = node.get("node_id", "")
            mode = node.get("mode", "toggle")
            if mode == "impulse":
                self._impulse_positions[node_id] = 0.0
                self._impulse_armed[node_id] = True
            elif mode == "velocity_impulse":
                self._velocity_running[node_id] = False
                self._impulse_armed[node_id] = True

        # Mode-Anzeige-Mapping
        mode_labels = {
            "toggle":           ("TOGGLE",  CLR_TEXT_DIM),
            "impulse":          ("STEP",    CLR_ACCENT),
            "velocity_impulse": ("VEL-IMP", CLR_ORANGE),
        }

        # Zeilen im UI aufbauen
        with self.list_container:
            for idx, node in enumerate(self.nodes):
                node_id = node.get("node_id", "")
                display = node.get("display_name", node_id)
                mode = node.get("mode", "toggle")
                row_bg = CLR_BG_ROW_A if idx % 2 == 0 else CLR_BG_ROW_B
                mode_text, mode_color = mode_labels.get(mode, ("?", CLR_TEXT_FAINT))

                with ui.ZStack(height=32):
                    ui.Rectangle(style={"background_color": row_bg})
                    with ui.HStack():
                        ui.Spacer(width=14)
                        ui.Label(display, style={"font_size": 12, "color": CLR_TEXT}, width=180)
                        ui.Label(mode_text, style={"font_size": 10, "color": mode_color}, width=90)
                        lbl = ui.Label("  FALSE",
                                       style={"font_size": 12, "color": CLR_RED}, width=100)
                        self.node_labels[node_id] = lbl
                        ui.Spacer()

                        btn_text = "Trigger" if mode in ("impulse", "velocity_impulse") else "Toggle"
                        btn = ui.Button(btn_text, width=70, height=22)
                        btn.set_style({
                            "background_color": 0xFF1A2840,
                            "border_radius": 3,
                            "font_size": 11,
                            "color": CLR_TEXT_DIM,
                        })
                        btn.set_clicked_fn(lambda n=node_id: on_button_clicked(n))
                        self._node_buttons.append(btn)
                        ui.Spacer(width=14)

        # Default-Werte
        for node in self.nodes:
            node_id = node.get("node_id")
            if node_id:
                self.node_values[node_id] = False

    # ---------------------------------------------------------------
    def find(self, node_id):
        """Sucht eine Node-Definition nach node_id."""
        for node in self.nodes:
            if node.get("node_id") == node_id:
                return node
        return None

    # ---------------------------------------------------------------
    def set_display(self, node_id, val):
        """Aktualisiert das Status-Label + setzt USD-Attribut entsprechend."""
        label = self.node_labels.get(node_id)
        if not label:
            return

        if val:
            label.text = "  TRUE"
            label.set_style({"font_size": 12, "color": CLR_GREEN})
        else:
            label.text = "  FALSE"
            label.set_style({"font_size": 12, "color": CLR_RED})

        # USD synchron halten
        try:
            stage = omni.usd.get_context().get_stage()
            if not stage:
                return
            node = self.find(node_id)
            if node:
                target_val = float(node.get("target_value", 1.0))
                self.set_usd_attr(stage, node, target_val if val else 0.0)
        except Exception as e:
            self._logger.log(f"[Display→USD] Fehler bei {node_id}: {e}", "error")

    # ---------------------------------------------------------------
    def apply_usd_for_node(self, node_id, val):
        """Schreibt den passenden USD-Wert (target_value oder 0)."""
        stage = omni.usd.get_context().get_stage()
        if not stage:
            return
        node = self.find(node_id)
        if not node:
            return
        target_val = float(node.get("target_value", 1.0))
        self.set_usd_attr(stage, node, target_val if val else 0.0)

    # ---------------------------------------------------------------
    def set_usd_attr(self, stage, node, value):
        """Setzt das USD-Attribut eines Knotens (mit Fallback-Attribut-Name)."""
        p_path = node.get("prim_path")
        if not p_path:
            return

        prim = stage.GetPrimAtPath(p_path)
        if not prim or not prim.IsValid():
            return

        attr_name = node.get("attribute", "drive:angular:physics:targetPosition")
        attr = prim.GetAttribute(attr_name)

        # Fallback: ohne ":physics:" probieren
        if not attr or not attr.IsValid():
            alt = attr_name.replace(":physics:", ":")
            attr = prim.GetAttribute(alt)
            if attr and attr.IsValid():
                attr_name = alt

        if not attr or not attr.IsValid():
            return

        try:
            attr.Set(value)
            # Default zusätzlich im Layer-Spec speichern
            layer = stage.GetEditTarget().GetLayer()
            prim_spec = layer.GetPrimAtPath(p_path)
            if prim_spec:
                sdf_attr = prim_spec.attributes.get(attr_name)
                if sdf_attr:
                    sdf_attr.default = value
        except Exception as e:
            self._logger.log(f"USD Fehler: {p_path} | {e}", "error")
