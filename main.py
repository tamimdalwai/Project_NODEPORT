
import asyncio
import logging
import os
import sys
import threading
import numpy as np
import pandas as pd
import webview
from flask import Flask, send_from_directory
from threading import Lock

# Import your ModBus module components
from ModBus import modbus_client_loop, latest_modbus_data

# Configuration checks
if sys.version_info < (3, 8):
    raise RuntimeError("Python 3.8 or newer is required")

if sys.platform != 'win32':
    raise RuntimeError("This application requires Windows 10+ with WebView2 runtime")

# Initialize Flask app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Global state and locks
global_modbus_data = {}
data_lock = Lock()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modbus_client.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger('pywebview').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

class PlcClientManager:
    def __init__(self):
        self.active_plcs = {}
        self.lock = asyncio.Lock()

    async def start_plc(self, plc_config):
        async with self.lock:
            plc_name = plc_config["PLC"]
            if plc_name not in self.active_plcs:
                task = asyncio.create_task(self._plc_loop(plc_config))
                self.active_plcs[plc_name] = task
                logging.info(f"Started PLC {plc_name} client")

    async def stop_plc(self, plc_name):
        async with self.lock:
            if plc_name in self.active_plcs:
                task = self.active_plcs.pop(plc_name)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logging.info(f"Stopped PLC {plc_name} client")

    async def _plc_loop(self, plc_config):
        try:
            while True:
                await modbus_client_loop(
                    plc_config["PLC"],
                    plc_config["IP Address"],
                    plc_config["Port"],
                    plc_config["Sampling Frequency"]
                )
                await asyncio.sleep(plc_config["Sampling Frequency"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"PLC {plc_config['PLC']} error: {e}")

class WebViewBridge:
    def __init__(self, plc_configs, client_manager, loop):
        self.plc_configs = {p["PLC"]: p for p in plc_configs}
        self.client_manager = client_manager
        self.active_windows = {}
        self.loop = loop
        self.window_counter = 0

    def get_plc_list(self):
        return sorted(self.plc_configs.keys(), key=lambda x: int(x[3:]))

    def create_plc_window(self, plc_name):
        if plc_name in self.active_windows:
            return True

        config = self.plc_configs.get(plc_name)
        if not config:
            logging.error(f"Invalid PLC {plc_name}")
            return False

        try:
            self.window_counter += 1
            window = webview.create_window(
                f'PLC {plc_name} Monitoring ({self.window_counter})',
                url=f'/data?plc={plc_name}',
                js_api=self,
                width=1200,
                height=800
            )

            def on_closed():
                self.loop.call_soon_threadsafe(
                    self.loop.create_task,
                    self._handle_window_close(plc_name)
                )

            window.events.closed += on_closed
            self.active_windows[plc_name] = window

            self.loop.call_soon_threadsafe(
                self.loop.create_task,
                self.client_manager.start_plc(config)
            )
            return True
        except Exception as e:
            logging.error(f"Window creation failed: {e}")
            return False

    async def _handle_window_close(self, plc_name):
        if plc_name in self.active_windows:
            del self.active_windows[plc_name]
        await self.client_manager.stop_plc(plc_name)

    def get_plc_data(self, plc_name):
        try:
            with data_lock:
                data = global_modbus_data.get(plc_name, {})
            return {
                'coils': data.get('coil_states', {}),
                'input_bits': data.get('input_status_states', {}),
                'registers': data.get('input_register_states', {})
            }
        except Exception as e:
            logging.error(f"Error getting data for {plc_name}: {e}")
            return {}

# Flask routes
@app.route('/')
def index():
    return send_from_directory('templates', 'home.html')

@app.route('/data')
def data():
    return send_from_directory('templates', 'data.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/health')
def health_check():
    with data_lock:
        return {'status': 'ok', 'active_plcs': list(global_modbus_data.keys())}

def load_plc_config():
    plc_config_path = os.path.join('config', 'plc_data.xlsx')
    try:
        df = pd.read_excel(plc_config_path)
        df.replace({np.nan: None}, inplace=True)
        return df.to_dict('records')
    except Exception as e:
        logging.error(f"Error loading PLC config: {e}")
        return []

async def monitor_global_data():
    while True:
        with data_lock:
            global_modbus_data.clear()
            for plc, data in latest_modbus_data.items():
                global_modbus_data[plc] = data
        await asyncio.sleep(1)

async def main(client_manager):
    plc_data = load_plc_config()
    valid_plcs = [plc for plc in plc_data if plc["IP Address"] and plc["Port"] > 0]

    monitor_task = asyncio.create_task(monitor_global_data())

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        monitor_task.cancel()
        await monitor_task

def start_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Initialize async loop
    loop = asyncio.new_event_loop()

    # Load PLC config
    plc_config = load_plc_config()
    valid_plcs = [plc for plc in plc_config if plc.get("IP Address") and plc.get("Port", 0) > 0]

    # Create client manager
    client_manager = PlcClientManager()

    # Start Flask server
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Start async loop in separate thread
    def run_async():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main(client_manager))

    modbus_thread = threading.Thread(target=run_async, daemon=True)
    modbus_thread.start()

    # Create and start webview window
    bridge = WebViewBridge(valid_plcs, client_manager, loop)
    window = webview.create_window(
        'PLC Monitor',
        url='http://localhost:5000',
        js_api=bridge,
        width=400,
        height=200
    )

    try:
        webview.start(debug=True)
    except Exception as e:
        logging.error(f"Webview startup failed: {e}")
    finally:
        loop.call_soon_threadsafe(loop.stop)
        logging.info("Application shutdown complete")





# import asyncio
# import logging
# import os
# import sys
# import threading
# import numpy as np
# import pandas as pd
# import webview
# from flask import Flask, send_from_directory
#
# # Import your ModBus module components
# from ModBus import modbus_client_loop, latest_modbus_data
#
# # Initialize Flask app
# app = Flask(__name__)
# app.config['TEMPLATES_AUTO_RELOAD'] = True
#
# # Global state to store real-time Modbus data for all PLCs
# global_modbus_data = {}
#
# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("modbus_client.log"),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
#
# # class WebViewBridge:
# #     def __init__(self, plc_names):
# #         self.plc_names = plc_names
# #         self.active_windows = {}  # Track windows by PLC name
# #
# #     def get_plc_list(self):
# #         return sorted(self.plc_names, key=lambda x: int(x[3:]))
# #
# #     def create_plc_window(self, plc):
# #         if plc not in self.active_windows:
# #             window = webview.create_window(
# #                 f'PLC {plc} Monitoring',
# #                 url=f'/data?plc={plc}',
# #                 js_api=self,
# #                 width=1200,
# #                 height=800
# #             )
# #             self.active_windows[plc] = window
# #         return True
# #
# #     def get_plc_data(self, plc):
# #         if plc in global_modbus_data:
# #             data = global_modbus_data[plc]
# #             return {
# #                 'coils': data.get('coil_states', {}),
# #                 'input_bits': data.get('input_status_states', {}),
# #                 'registers': data.get('input_register_states', {})
# #             }
# #         return {}
#
#
# class WebViewBridge:
#     def __init__(self, plc_names):
#         self.plc_names = plc_names
#         self.active_windows = {}
#
#     def get_plc_list(self):
#         return sorted(self.plc_names, key=lambda x: int(x[3:]))
#
#     def create_plc_window(self, plc):
#         if plc not in self.active_windows:
#             window = webview.create_window(
#                 f'PLC {plc} Monitoring',
#                 url=f'/data?plc={plc}',
#                 js_api=self,
#                 width=1200,
#                 height=800
#             )
#             self.active_windows[plc] = window
#         return True
#
#     def get_plc_data(self, plc):
#         try:
#             data = global_modbus_data.get(plc, {})
#             return {
#                 'coils': data.get('coil_states', {}),
#                 'input_bits': data.get('input_status_states', {}),
#                 'registers': data.get('input_register_states', {})
#             }
#         except Exception as e:
#             logging.error(f"Error getting data for {plc}: {e}")
#             return {}
# ## Update Flask routes
# @app.route('/')
# def index():
#     return send_from_directory('templates', 'home.html')
#
# @app.route('/data')
# def data():
#     return send_from_directory('templates', 'data.html')
#
# @app.route('/static/<path:filename>')
# def serve_static(filename):
#     return send_from_directory('static', filename)
#
# def load_plc_config():
#     plc_config_path = os.path.join('config', 'plc_data.xlsx')
#     try:
#         df = pd.read_excel(plc_config_path)
#         df.replace({np.nan: None}, inplace=True)
#         return df.to_dict('records')
#     except Exception as e:
#         logging.error(f"Error loading PLC config: {e}")
#         return []
#
# async def run_plc_client(plc):
#     try:
#         while True:
#             await modbus_client_loop(
#                 plc["PLC"],
#                 plc["IP Address"],
#                 plc["Port"],
#                 plc["Sampling Frequency"]
#             )
#     except Exception as e:
#         logging.error(f"PLC {plc['PLC']} failed: {e}")
#
# # async def monitor_global_data():
# #     while True:
# #         global_modbus_data.update(latest_modbus_data)
# #         logging.info(f"Global modbus data: {global_modbus_data}")
# #
# #         await asyncio.sleep(1)
# from threading import Lock
# global_modbus_data = {}
# data_lock = Lock()  # Add this
#
# async def monitor_global_data():
#     while True:
#         with data_lock:
#             global_modbus_data.update(latest_modbus_data)
#         await asyncio.sleep(1)
# async def main():
#     plc_data = load_plc_config()
#     valid_plcs = [
#         plc for plc in plc_data
#         if plc["IP Address"] and plc["Port"] > 0
#     ]
#
#     if not valid_plcs:
#         logging.error("No valid PLCs found in config.")
#         return
#
#     tasks = [asyncio.create_task(run_plc_client(plc)) for plc in valid_plcs]
#     tasks.append(asyncio.create_task(monitor_global_data()))
#     await asyncio.gather(*tasks)
#
# def start_flask():
#     app.run(host='0.0.0.0', port=5000)
#
# if __name__ == "__main__":
#     # Load PLC configuration
#     plc_config = load_plc_config()
#     valid_plcs = [
#         plc["PLC"] for plc in plc_config
#         if plc.get("IP Address") and plc.get("Port", 0) > 0
#     ]
#
#     # Start Flask server in a thread
#     flask_thread = threading.Thread(target=start_flask, daemon=True)
#     flask_thread.start()
#
#     # Start Modbus client
#     modbus_thread = threading.Thread(
#         target=lambda: asyncio.run(main()),
#         daemon=True
#     )
#     modbus_thread.start()
#
#     # Create and start webview window
#     bridge = WebViewBridge(valid_plcs)
#     window = webview.create_window(
#         'PLC Monitor',
#         url='http://localhost:5000',
#         js_api=bridge,
#         width=400,
#         height=200
#     )
#     webview.start(debug=True)
#
#









# # main.py
# import asyncio
# import logging
# import os
# import sys
# import threading
#
# import numpy as np
# import pandas as pd
# import webview
#
# from ModBus import modbus_client_loop, latest_modbus_data
#
# # Global state to store real-time Modbus data for all PLCs
# global_modbus_data = {}
#
# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("modbus_client.log"),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
#
# def load_plc_config():
#     plc_config_path = 'config\\plc_data.xlsx'
#     """Load PLC configuration data"""
#     if not os.path.exists(plc_config_path):
#         print(f"Error: File '{plc_config_path}' not found.")
#         return []
#
#     try:
#         df = pd.read_excel(plc_config_path)
#         df.replace({np.nan: None}, inplace=True)
#         return df.to_dict('records')
#     except Exception as e:
#         print(f"Error loading PLC config: {e}")
#         return []
#
# async def run_plc_client(plc):
#     """Run the Modbus client loop for a single PLC indefinitely."""
#     try:
#         while True:
#             await modbus_client_loop(
#                 plc["PLC"],
#                 plc["IP Address"],
#                 plc["Port"],
#                 plc["Sampling Frequency"]
#             )
#     except Exception as e:
#         logging.error(f"PLC {plc['PLC']} failed: {e}")
#
# async def monitor_global_data():
#     """Periodically update global_modbus_data from ModBus.latest_modbus_data."""
#     while True:
#         global_modbus_data.update(latest_modbus_data)
#         logging.info(f"Current global data: {global_modbus_data}")
#         await asyncio.sleep(1)  # Update every 1 second
#
# async def main():
#     """Run all PLC client loops and data monitoring concurrently."""
#     plc_data = load_plc_config()
#     valid_plcs = [
#         plc for plc in plc_data
#         if plc["IP Address"] and plc["Port"] > 0
#     ]
#
#     if not valid_plcs:
#         logging.error("No valid PLCs found in config.")
#         return
#
#     # Create tasks for each PLC and the data monitor
#     tasks = [
#         asyncio.create_task(run_plc_client(plc))
#         for plc in valid_plcs
#     ]
#     tasks.append(asyncio.create_task(monitor_global_data()))
#
#     # Run all tasks indefinitely
#     await asyncio.gather(*tasks)
#
# ######
# #
# # class Bridge:
# #     def __init__(self,plc_names):
# #         self.current_plc = None
# #         self.data_window = None
# #         self.plc_names = plc_names  # Store pre-loaded PLC names
# #
# #     def get_plc_list(self):
# #         """Return sorted list of configured PLCs"""
# #         return sorted(
# #             self.plc_names,
# #             key=lambda x: int(x[3:])  # Sort by PLC number (PLC1, PLC2, etc)
# #         )
# #
# #     def create_data_window(self, plc):
# #         """Create new window for selected PLC data"""
# #         self.current_plc = plc
# #         self.data_window = webview.create_window(
# #             f'PLC {plc} Monitoring',
# #             html=data_window_html,
# #             js_api=Bridge(),
# #             width=1200,
# #             height=800
# #         )
# #
# #     def get_plc_data(self):
# #         """Get current data for selected PLC"""
# #         if self.current_plc in global_modbus_data:
# #             data = global_modbus_data[self.current_plc]
# #             return {
# #                 'coils': data.get('coil_states', {}),
# #                 'input_bits': data.get('input_status_states', {}),
# #                 'registers': data.get('input_register_states', {})
# #             }
# #         return {}
# #
# # def start_webview(plc_names):
# #     bridge = Bridge(plc_names)
# #     window = webview.create_window(
# #         'PLC Monitor',
# #         html=select_window_html,
# #         js_api=bridge,
# #         width=400,
# #         height=200
# #     )
# #     webview.start()
# #
# #
# # #######################
# #
# # if __name__ == "__main__":
# #     # Load PLC configuration first
# #     plc_config = load_plc_config()
# #     valid_plcs = [
# #         plc["PLC"] for plc in plc_config
# #         if plc.get("IP Address") and plc.get("Port", 0) > 0
# #     ]
# #
# #     # Start Modbus client
# #     def run_async_main():
# #         asyncio.run(main())
# #
# #     modbus_thread = threading.Thread(target=run_async_main, daemon=True)
# #     modbus_thread.start()
# #
# #     # Start UI with pre-loaded PLC names
# #     start_webview(valid_plcs)
#
#
# import os
# import webview
# from flask import Flask, send_from_directory
#
# # Add this at the top of your main.py
# app = Flask(__name__)
#
#
# @app.route('/static/<path:filename>')
# def static_files(filename):
#     return send_from_directory(os.path.join(app.root_path, 'static'), filename)
#
#
# @app.route('/')
# def select_window():
#     return send_from_directory('templates', 'select.html')
#
#
# @app.route('/data')
# def data_window():
#     return send_from_directory('templates', 'data.html')
#
#
# class Bridge:
#     def __init__(self, plc_names):
#         self.current_plc = None
#         self.plc_names = plc_names
#
#     def get_plc_list(self):
#         return sorted(self.plc_names, key=lambda x: int(x[3:]))
#
#     def create_data_window(self, plc):
#         self.current_plc = plc
#         webview.create_window(
#             f'PLC {plc} Monitoring',
#             url='/data',
#             js_api=self,
#             width=1200,
#             height=800
#         )
#
#     def get_plc_data(self):
#         """Get current data for selected PLC"""
#         if self.current_plc in global_modbus_data:
#             data = global_modbus_data[self.current_plc]
#             return {
#                 'coils': data.get('coil_states', {}),
#                 'input_bits': data.get('input_status_states', {}),
#                 'registers': data.get('input_register_states', {})
#             }
#         return {}
#     # ... rest of Bridge class remains the same
#
#
# def start_webview(plc_names):
#     bridge = Bridge(plc_names)
#     window = webview.create_window(
#         'PLC Monitor',
#         url='/',
#         js_api=bridge,
#         width=400,
#         height=200
#     )
#     webview.start()
#
#
# if __name__ == "__main__":
#     # Add this before starting webview
#     flask_thread = threading.Thread(target=app.run, daemon=True)
#     flask_thread.start()
#
#     # Rest of your existing main block
#     plc_config = load_plc_config()
#     valid_plcs = [
#         plc["PLC"] for plc in plc_config
#         if plc.get("IP Address") and plc.get("Port", 0) > 0
#     ]
#
#
#     # Start Modbus client
#     def run_async_main():
#         asyncio.run(main())
#
#
#     modbus_thread = threading.Thread(target=run_async_main, daemon=True)
#     modbus_thread.start()
#
#     start_webview(valid_plcs)
