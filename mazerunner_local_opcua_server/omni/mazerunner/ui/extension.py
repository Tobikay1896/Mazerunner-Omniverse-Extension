import omni.ext
import omni.ui as ui
import omni.usd
import os
import json
import asyncio
from asyncua import Client

class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        ext_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self.json_path = os.path.join(ext_path, "omni", "mazerunner", "ui", "nodes_db.json")
        
        self._window = ui.Window("Maze Runner - OPC UA Live Monitor", width=750, height=450)
        self._window.deferred_dock_in("Property")

        self.node_labels = {}
        self.nodes = []
        self._is_running = True 
        self._update_task = None

        with self._window.frame:
            with ui.VStack(spacing=5, m=10):
                with ui.HStack(height=35):
                    ui.Label("OPC UA Live-Monitor", style={"font_size": 18, "color": 0xFF00BFFF})
                    ui.Spacer()
                    ui.Button("REFRESH", width=100, height=30, clicked_fn=self.load_nodes_from_json)
                
                ui.Separator(height=10)
                
                with ui.HStack(height=20):
                    ui.Label("Variable", width=150, style={"color": 0xFFAAAAAA})
                    ui.Label("IP", width=110, style={"color": 0xFFAAAAAA})
                    ui.Label("Node-ID", width=100, style={"color": 0xFFAAAAAA})
                    ui.Label("Zustand (Wert)", width=150, style={"color": 0xFFAAAAAA})

                ui.Separator(height=2)

                with ui.ScrollingFrame():
                    self._list_container = ui.VStack(spacing=8)

        self.load_nodes_from_json()
        self._update_task = asyncio.ensure_future(self.auto_update_loop())

    def load_nodes_from_json(self):
        if not hasattr(self, "_list_container"): return
        self._list_container.clear()
        self.node_labels = {} 
        
        if not os.path.exists(self.json_path): return
        try:
            with open(self.json_path, 'r') as f:
                self.nodes = json.load(f).get("nodes", [])
        except Exception as e:
            print(f"JSON Error: {e}")
            return

        with self._list_container:
            for node in self.nodes:
                with ui.HStack(height=24):
                    ui.Label(str(node.get('display_name', 'Unknown')), width=150)
                    ui.Label(str(node.get('server_ip', '0.0.0.0')), width=110, style={"color": 0xFF888888})
                    ui.Label(str(node.get('node_id', '')), width=100, style={"color": 0xFFBBBBBB})
                    
                    lbl = ui.Label("-", width=150)
                    self.node_labels[f"{node['server_ip']}_{node['node_id']}"] = lbl

    async def auto_update_loop(self):
        await asyncio.sleep(1.0)
        while getattr(self, "_is_running", False):
            try:
                await self.update_all_servers()
                await asyncio.sleep(0.5) 
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Loop Error: {e}")
                await asyncio.sleep(1.0)

    async def update_all_servers(self):
        if not self.node_labels: return
        
        stage = omni.usd.get_context().get_stage()
        ip_groups = {}
        for node in self.nodes:
            ip_groups.setdefault(node['server_ip'], []).append(node)

        for ip, nodes in ip_groups.items():
            client = await self.get_client(ip)
            
            if not client:
                # Alle Nodes dieser IP auf OFFLINE setzen
                for n in nodes:
                    lbl = self.node_labels.get(f"{ip}_{n['node_id']}")
                    if lbl:
                        lbl.text = "OFFLINE"
                        lbl.set_style({"color": 0xFF0000FF})
                continue

            # Daten lesen OHNE danach zu disconnecten
            for n in nodes:
                key = f"{ip}_{n['node_id']}"
                label = self.node_labels.get(key)
                if not label: continue
                
                try:
                    var_node = client.get_node(n['node_id'])
                    val = await var_node.read_value()
                    
                    # UI Update
                    if isinstance(val, bool):
                        label.text = "TRUE" if val else "FALSE"
                        label.set_style({"color": 0xFF00FF00 if val else 0xFFFFFFFF})
                    else:
                        label.text = f"{val:.2f}" if isinstance(val, (float, int)) else str(val)
                        label.set_style({"color": 0xFFFFFF00})
                    
                    # Physik Update
                    p_path = n.get("prim_path")
                    if p_path and stage:
                        prim = stage.GetPrimAtPath(p_path)
                        if prim and prim.IsValid():
                            attr = prim.GetAttribute(n.get("attribute", "xformOp:translate"))
                            if attr:
                                # Nutze Gf.Vec3d oder passenden Typ falls nötig
                                attr.Set(val * n.get("target_value", 1.0))

                except Exception as e:
                    label.text = "READ ERR"
                    label.set_style({"color": 0xFF00AAFF})

    def on_shutdown(self):
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
        self.node_labels = {}
        if self._window:
            self._window.destroy()
            self._window = None