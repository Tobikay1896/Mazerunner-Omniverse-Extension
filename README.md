# Maze Runner — Omniverse Extension

Projektarbeit von Tobias Küster (1690767)  
Hochschule Hannover – Fakultät II, Maschinenbau und Bioverfahrenstechnik  
Betreut von: Prof. Diersen, Dr. Yübo Wang, Herrn Ernst

---

## Was ist diese Extension?

Diese Erweiterung für **NVIDIA Isaac Sim (Omniverse)** ist das Steuerungs-Panel für den
Digitalen Zwilling der Anlage **Maze Runner**.

Der Maze Runner ist eine physikalische Produktionslinie, die an der Hochschule Hannover
aufgebaut und über die **Digital Twin App der Hochschule Rhein-Main**
(`digitaltwinservice.de`) betrieben wird.
Die Extension verbindet die Isaac-Sim-Simulation mit der realen Anlage: sie überträgt
Schalt- und Stellbefehle per REST-API an den DigitalTwinService und empfängt
Echtzeit-Statusmeldungen via MQTT über WebSocket.

---

## Betriebsmodi

| Modus | Beschreibung |
|-------|-------------|
| **SIM** | Nur lokale Simulation in Isaac Sim. Kein Netzwerkzugriff. |
| **LIVE** | Befehle gehen per REST-API an die reale Anlage; MQTT liefert Live-Rückmeldungen. |

Umschalten mit dem **→ LIVE / → SIM**-Button in der Toolbar.

---

## Voraussetzungen

### API-Key setzen

In [constants.py](constants.py) muss der API-Key der Hochschule Rhein-Main eingetragen sein:

```python
API_KEY = "dein-api-key-hier"
```

Ohne gültigen Key schlagen alle REST-API-Aufrufe im LIVE-Modus fehl.

### Python-Abhängigkeiten

Die folgenden Pakete werden in der Omniverse-Umgebung benötigt und können über
`pip install` im eingebetteten Python installiert werden:

```
aiohttp
websockets
```

---

## Installation in Isaac Sim

1. Den Ordner `omni.mazerunner.API` in ein lokales Extension-Verzeichnis kopieren,
   das Isaac Sim kennt (z. B. `~/Documents/Kit/apps/Isaac-Sim/exts/`).
2. Isaac Sim öffnen → **Window → Extensions** → Suche nach `mazerunner.API` → Enable.
3. Das Fenster **Maze Runner** dockt sich automatisch in den Property-Bereich ein.

---

## Bedienung

### Steuerfeld

| Element | Funktion |
|---------|----------|
| **Refresh JSON** | Lädt `nodes_db.json` neu (z. B. nach Konfigurationsänderungen). |
| **Restart Extension** | Startet die Extension komplett neu, ohne Isaac Sim zu beenden. |
| **→ LIVE / → SIM** | Wechsel zwischen Simulationsmodus und Live-Anbindung. |
| **▶ Gesamtprozess** | Startet den vollautomatischen Produktionsablauf (nur SIM). |

### Node-Liste

Jede Zeile entspricht einem Maschinenelement aus `nodes_db.json`:

- **TOGGLE** – schaltet einen Aktor ein/aus (z. B. BM ausfahren)
- **STEP** – inkrementiert eine Zielposition um einen festen Winkelschritt (z. B. Drehscheibe)
- **VEL-IMP** – setzt eine Geschwindigkeit für eine definierte Dauer
- **ROUTINE** – startet eine vordefinierte Bewegungssequenz (z. B. BA_Start)

### Simulation starten

1. USD-Szene `MazeRunnerDigiTwin.usd` öffnen.
2. Im SIM-Modus auf **▶ Play** drücken.
3. Buttons in der Node-Liste oder **▶ Gesamtprozess** verwenden.

---

## Projektstruktur

| Datei | Zuständigkeit |
|-------|--------------|
| `extension.py` | Einstiegspunkt; verbindet alle Komponenten |
| `ui_builder.py` | Aufbau des Omniverse-Fensters |
| `node_manager.py` | Laden der Nodes aus JSON; USD-Attributzugriff |
| `api_client.py` | REST-API-Aufrufe (GET/SET) gegen digitaltwinservice.de |
| `mqtt_handler.py` | MQTT-Subscriptions und Callback-Verarbeitung |
| `websocket_mqtt.py` | Minimaler MQTT-Client über WebSocket-Transport |
| `suction_gripper.py` | Physikalisches Greifen via FixedJoint (USD/Physics) |
| `timeline_handler.py` | Reaktion auf Play/Stop der Omniverse-Timeline |
| `routines.py` | Vordefinierte automatisierte Abläufe (Gesamtprozess, BA_Start) |
| `logger.py` | Thread-sicherer Log-Bereich im UI |
| `constants.py` | Zentrale Konfiguration (API-Key, URLs, Farben, USD-Pfade) |
| `nodes_db.json` | Konfiguration aller steuerbaren Maschinen-Nodes |
