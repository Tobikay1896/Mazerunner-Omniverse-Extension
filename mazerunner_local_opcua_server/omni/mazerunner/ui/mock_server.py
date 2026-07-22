import asyncio
import json
import os
import logging
from asyncua import Server, ua

# Nur kritische Fehler loggen
logging.basicConfig(level=logging.ERROR)

async def main():
    server = Server()
    await server.init()
    
    current_dir = os.path.dirname(__file__)
    json_path = os.path.join(current_dir, "nodes_db.json")
    
    if not os.path.exists(json_path):
        print(f"FEHLER: Datei nicht gefunden: {json_path}")
        return

    with open(json_path, "r") as f:
        config = json.load(f)

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("MazeRunner-SPS-Simulator")
    
    idx = await server.register_namespace("http://mazerunner.simulation")
    obj = await server.nodes.objects.add_object(idx, "SPS_Variables")

    opc_vars = []
    used_ids = set()

    print("--------------------------------------------------")
    print("MOCK SERVER: INITIALISIERUNG")
    print("--------------------------------------------------")

    for node in config["nodes"]:
        n_id = node["node_id"]
        name = node["display_name"]
        
        if n_id in used_ids:
            continue

        is_ds = "DS_" in name
        
        # Wir nutzen Double statt Float, um BadTypeMismatch zu vermeiden
        if is_ds:
            # Initialwert 0.0 erzwingt Double-Typ im Server
            var = await obj.add_variable(n_id, name, 0.0)
        else:
            var = await obj.add_variable(n_id, name, False)
        
        await var.set_writable()
        
        opc_vars.append({
            "node": var, 
            "name": name, 
            "is_ds": is_ds,
            "id": n_id
        })
        used_ids.add(n_id)
        
        dtype = "DOUBLE/FLOAT" if is_ds else "BOOL"
        print(f"[{dtype}] Registriert: {name:20} | ID: {n_id:10}")

    print("--------------------------------------------------")
    print("SIMULATION GESTARTET (Schrittkette läuft...)")
    print("--------------------------------------------------")

    async with server:
        while True:
            for item in opc_vars:
                try:
                    # 1. Einschalten / Wert setzen
                    if item["is_ds"]:
                        target_val = 90.0
                        # Nutze VariantType.Double passend zum Initialwert 0.0
                        await item["node"].write_value(ua.Variant(target_val, ua.VariantType.Double))
                        print(f">>> SET: {item['name']} -> {target_val}°")
                    else:
                        await item["node"].write_value(True)
                        print(f">>> SET: {item['name']} -> TRUE")
                    
                    await asyncio.sleep(2.0)
                    
                    # 2. RESET
                    if item["is_ds"]:
                        await item["node"].write_value(ua.Variant(0.0, ua.VariantType.Double))
                        print(f"<<< RESET: {item['name']} -> 0.0°")
                    else:
                        await item["node"].write_value(False)
                        print(f"<<< RESET: {item['name']} -> FALSE")
                    
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"FEHLER bei Node {item['name']}: {e}")
                    continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMock-Server beendet.")