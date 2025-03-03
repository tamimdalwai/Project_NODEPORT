# main.py
import asyncio
import logging
import os
import sys
import threading

import numpy as np
import pandas as pd
import webview

from ModBus import modbus_client_loop, latest_modbus_data

# Global state to store real-time Modbus data for all PLCs
global_modbus_data = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modbus_client.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_plc_config():
    plc_config_path = 'config\\plc_data.xlsx'
    """Load PLC configuration data"""
    if not os.path.exists(plc_config_path):
        print(f"Error: File '{plc_config_path}' not found.")
        return []

    try:
        df = pd.read_excel(plc_config_path)
        df.replace({np.nan: None}, inplace=True)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading PLC config: {e}")
        return []

async def run_plc_client(plc):
    """Run the Modbus client loop for a single PLC indefinitely."""
    try:
        while True:
            await modbus_client_loop(
                plc["PLC"],
                plc["IP Address"],
                plc["Port"],
                plc["Sampling Frequency"]
            )
    except Exception as e:
        logging.error(f"PLC {plc['PLC']} failed: {e}")

async def monitor_global_data():
    """Periodically update global_modbus_data from ModBus.latest_modbus_data."""
    while True:
        global_modbus_data.update(latest_modbus_data)
        logging.info(f"Current global data: {global_modbus_data}")
        await asyncio.sleep(1)  # Update every 1 second

async def main():
    """Run all PLC client loops and data monitoring concurrently."""
    plc_data = load_plc_config()
    valid_plcs = [
        plc for plc in plc_data
        if plc["IP Address"] and plc["Port"] > 0
    ]

    if not valid_plcs:
        logging.error("No valid PLCs found in config.")
        return

    # Create tasks for each PLC and the data monitor
    tasks = [
        asyncio.create_task(run_plc_client(plc))
        for plc in valid_plcs
    ]
    tasks.append(asyncio.create_task(monitor_global_data()))

    # Run all tasks indefinitely
    await asyncio.gather(*tasks)

######
#
# class Bridge:
#     def __init__(self,plc_names):
#         self.current_plc = None
#         self.data_window = None
#         self.plc_names = plc_names  # Store pre-loaded PLC names
#
#     def get_plc_list(self):
#         """Return sorted list of configured PLCs"""
#         return sorted(
#             self.plc_names,
#             key=lambda x: int(x[3:])  # Sort by PLC number (PLC1, PLC2, etc)
#         )
#
#     def create_data_window(self, plc):
#         """Create new window for selected PLC data"""
#         self.current_plc = plc
#         self.data_window = webview.create_window(
#             f'PLC {plc} Monitoring',
#             html=data_window_html,
#             js_api=Bridge(),
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
#
# def start_webview(plc_names):
#     bridge = Bridge(plc_names)
#     window = webview.create_window(
#         'PLC Monitor',
#         html=select_window_html,
#         js_api=bridge,
#         width=400,
#         height=200
#     )
#     webview.start()
#
#
# #######################
#
# if __name__ == "__main__":
#     # Load PLC configuration first
#     plc_config = load_plc_config()
#     valid_plcs = [
#         plc["PLC"] for plc in plc_config
#         if plc.get("IP Address") and plc.get("Port", 0) > 0
#     ]
#
#     # Start Modbus client
#     def run_async_main():
#         asyncio.run(main())
#
#     modbus_thread = threading.Thread(target=run_async_main, daemon=True)
#     modbus_thread.start()
#
#     # Start UI with pre-loaded PLC names
#     start_webview(valid_plcs)


import os
import webview
from flask import Flask, send_from_directory

# Add this at the top of your main.py
app = Flask(__name__)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


@app.route('/')
def select_window():
    return send_from_directory('templates', 'select.html')


@app.route('/data')
def data_window():
    return send_from_directory('templates', 'data.html')


class Bridge:
    def __init__(self, plc_names):
        self.current_plc = None
        self.plc_names = plc_names

    def get_plc_list(self):
        return sorted(self.plc_names, key=lambda x: int(x[3:]))

    def create_data_window(self, plc):
        self.current_plc = plc
        webview.create_window(
            f'PLC {plc} Monitoring',
            url='/data',
            js_api=self,
            width=1200,
            height=800
        )

    def get_plc_data(self):
        """Get current data for selected PLC"""
        if self.current_plc in global_modbus_data:
            data = global_modbus_data[self.current_plc]
            return {
                'coils': data.get('coil_states', {}),
                'input_bits': data.get('input_status_states', {}),
                'registers': data.get('input_register_states', {})
            }
        return {}
    # ... rest of Bridge class remains the same


def start_webview(plc_names):
    bridge = Bridge(plc_names)
    window = webview.create_window(
        'PLC Monitor',
        url='/',
        js_api=bridge,
        width=400,
        height=200
    )
    webview.start()


if __name__ == "__main__":
    # Add this before starting webview
    flask_thread = threading.Thread(target=app.run, daemon=True)
    flask_thread.start()

    # Rest of your existing main block
    plc_config = load_plc_config()
    valid_plcs = [
        plc["PLC"] for plc in plc_config
        if plc.get("IP Address") and plc.get("Port", 0) > 0
    ]


    # Start Modbus client
    def run_async_main():
        asyncio.run(main())


    modbus_thread = threading.Thread(target=run_async_main, daemon=True)
    modbus_thread.start()

    start_webview(valid_plcs)