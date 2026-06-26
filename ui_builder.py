"""
ui_builder.py
=============
Baut das Hauptfenster der Extension auf.
Die Builder-Klasse liefert die UI-Elemente, die der Extension-Controller
für die Anbindung an Logik benötigt.
"""

import omni.ui as ui

from .constants import (
    CLR_BG_DARK, CLR_BG_MID, CLR_BG_HEADER, CLR_BORDER,
    CLR_TEXT, CLR_TEXT_DIM, CLR_TEXT_FAINT,
    CLR_GREEN, CLR_RED,
)


class UIBuilder:
    """Erzeugt das Window-Layout und liefert Referenzen auf die UI-Widgets."""

    def __init__(self):
        self.window = None
        self.status_label = None
        self.sim_btn = None
        self.node_count_label = None
        self.list_container = None
        self.log_container = None
        self.btn_gesamt = None

    # ---------------------------------------------------------------
    def build(self, on_refresh, on_restart, on_toggle_sim,
              on_clear_log, on_gesamt):
        """
        Baut das gesamte Fenster auf. Die Callbacks werden für die
        Toolbar/Buttons benötigt und in extension.py implementiert.
        """
        self.window = ui.Window("Maze Runner", width=880, height=520)
        self.window.deferred_dock_in("Property")

        with self.window.frame:
            with ui.VStack(spacing=0):
                self._build_header()
                ui.Line(style={"color": CLR_BORDER}, height=1)

                self._build_toolbar(on_refresh, on_restart, on_toggle_sim)
                ui.Line(style={"color": CLR_BORDER}, height=1)

                self._build_column_headers()
                ui.Line(style={"color": CLR_BORDER}, height=1)

                # Node-Liste
                with ui.ScrollingFrame(style={"background_color": CLR_BG_MID}):
                    self.list_container = ui.VStack(spacing=0)

                ui.Line(style={"color": CLR_BORDER}, height=1)
                self._build_gesamt_button(on_gesamt)
                ui.Line(style={"color": CLR_BORDER}, height=1)

                self._build_log_header(on_clear_log)
                with ui.ScrollingFrame(height=110,
                                       style={"background_color": 0xFF080C14}):
                    self.log_container = ui.VStack(spacing=0)

    # ---------------------------------------------------------------
    def _build_header(self):
        """Titel-/Statusleiste oben."""
        with ui.ZStack(height=50):
            ui.Rectangle(style={"background_color": CLR_BG_DARK})
            with ui.HStack():
                ui.Spacer(width=14)
                with ui.VStack(spacing=1):
                    ui.Spacer(height=9)
                    ui.Label("MAZE RUNNER",
                             style={"font_size": 17, "color": CLR_TEXT}, height=22)
                    ui.Label("Web-API Control Center",
                             style={"font_size": 11, "color": CLR_TEXT_DIM}, height=14)
                ui.Spacer()
                with ui.VStack(width=180, spacing=1):
                    ui.Spacer(height=10)
                    self.status_label = ui.Label(
                        "SIM-Modus aktiv",
                        style={"font_size": 11, "color": CLR_GREEN},
                        height=16, alignment=ui.Alignment.RIGHT,
                    )
                ui.Spacer(width=14)

    # ---------------------------------------------------------------
    def _build_toolbar(self, on_refresh, on_restart, on_toggle_sim):
        """Toolbar mit Buttons (Refresh, Restart, SIM↔LIVE)."""
        with ui.ZStack(height=34):
            ui.Rectangle(style={"background_color": CLR_BG_MID})
            with ui.HStack(spacing=6):
                ui.Spacer(width=10)

                btn_ref = ui.Button("Refresh JSON", width=120, height=24)
                btn_ref.set_style({
                    "background_color": 0xFF1A2E48,
                    "border_radius": 3, "font_size": 11, "color": CLR_TEXT,
                })
                btn_ref.set_clicked_fn(on_refresh)

                btn_rst = ui.Button("Restart Extension", width=130, height=24)
                btn_rst.set_style({
                    "background_color": 0xFF2A1520,
                    "border_radius": 3, "font_size": 11, "color": CLR_RED,
                })
                btn_rst.set_clicked_fn(on_restart)

                self.sim_btn = ui.Button("→ LIVE", width=90, height=24)
                self.sim_btn.set_style({
                    "background_color": 0xFF0D2A0D,
                    "border_radius": 3, "font_size": 11, "color": CLR_GREEN,
                })
                self.sim_btn.set_clicked_fn(on_toggle_sim)

                ui.Spacer()
                self.node_count_label = ui.Label(
                    "", style={"font_size": 10, "color": CLR_TEXT_FAINT},
                    width=70, alignment=ui.Alignment.RIGHT,
                )
                ui.Spacer(width=14)

    # ---------------------------------------------------------------
    def _build_column_headers(self):
        """Kopfzeile der Node-Liste."""
        with ui.ZStack(height=22):
            ui.Rectangle(style={"background_color": CLR_BG_HEADER})
            with ui.HStack():
                ui.Spacer(width=14)
                ui.Label("Node",   style={"font_size": 10, "color": CLR_TEXT_FAINT}, width=180)
                ui.Label("Mode",   style={"font_size": 10, "color": CLR_TEXT_FAINT}, width=90)
                ui.Label("Status", style={"font_size": 10, "color": CLR_TEXT_FAINT}, width=100)
                ui.Spacer()
                ui.Label("Action", style={"font_size": 10, "color": CLR_TEXT_FAINT},
                         width=80, alignment=ui.Alignment.CENTER)
                ui.Spacer(width=14)

    # ---------------------------------------------------------------
    def _build_gesamt_button(self, on_gesamt):
        """Großer Start-Button für den Gesamtprozess."""
        with ui.ZStack(height=34):
            ui.Rectangle(style={"background_color": CLR_BG_MID})
            with ui.HStack(spacing=6):
                ui.Spacer(width=10)
                self.btn_gesamt = ui.Button("▶ Gesamtprozess", width=150, height=24)
                self.btn_gesamt.set_style({
                    "background_color": 0xFF0D2A0D,
                    "border_radius": 3, "font_size": 11, "color": CLR_GREEN,
                })
                self.btn_gesamt.set_clicked_fn(on_gesamt)
                ui.Spacer()

    # ---------------------------------------------------------------
    def _build_log_header(self, on_clear_log):
        """Kopfzeile des Log-Bereichs."""
        with ui.ZStack(height=22):
            ui.Rectangle(style={"background_color": CLR_BG_DARK})
            with ui.HStack():
                ui.Spacer(width=14)
                ui.Label("Log", style={"font_size": 10, "color": CLR_TEXT_FAINT}, width=40)
                ui.Spacer()
                btn_clr = ui.Button("Clear", width=48, height=16)
                btn_clr.set_style({
                    "background_color": 0xFF152030,
                    "border_radius": 2, "font_size": 9, "color": CLR_TEXT_FAINT,
                })
                btn_clr.set_clicked_fn(on_clear_log)
                ui.Spacer(width=14)
