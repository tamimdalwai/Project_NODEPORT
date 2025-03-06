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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modbus_client.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger instances
logger = logging.getLogger("ModbusClient")
logging.getLogger("pymodbus").setLevel(logging.WARNING)

# Configuration checks
if sys.version_info < (3, 8):
    raise RuntimeError("Python 3.8 or newer is required")

if sys.platform != 'win32':
    raise RuntimeError("This application requires Windows 10+ with WebView2 runtime")

SAVED_ADDRESS_FILE_PATH = "config/saveAddress.xlsx"


def get_modbus_addresses_with_check(sheet_name):
    """Read Modbus addresses from Excel sheet."""
    try:
        df = pd.read_excel(SAVED_ADDRESS_FILE_PATH, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return {"Coils": [], "Input Bits": [], "Analog Inputs": []}

    if df.empty:
        logger.warning(f"Sheet '{sheet_name}' is empty")
        return {"Coils": [], "Input Bits": [], "Analog Inputs": []}

    # Extract and adjust addresses
    coils = df['MODBUS ADDRESS (Coils)'].dropna().astype(int).tolist()
    input_bits = [addr - 10000 for addr in
                  df['MODBUS ADDRESS (Input Bits)'].dropna().astype(int).tolist()]
    analog_inputs = [addr - 30000 for addr in
                     df['MODBUS ADDRESS (Analog Inputs)'].dropna().astype(int).tolist()]

    return {
        "Coils": coils,
        "Input Bits": input_bits,
        "Analog Inputs": analog_inputs
    }


# def get_coils(sheet_name):
#     """Get coil addresses for selected PLC."""
#     coils = get_modbus_addresses_with_check(sheet_name)["Coils"]
#     logger.info(f"COILS: {coils}")
#     return coils
#
#
# def get_input_bits(sheet_name):
#     """Get input bit addresses for selected PLC."""
#     input_bits = get_modbus_addresses_with_check(sheet_name)["Input Bits"]
#     logger.info(f"INPUT BITS: {input_bits}")
#     return input_bits
#
#
# def get_inputs_register(sheet_name):
#     """Get input register addresses for selected PLC."""
#     analog_inputs = get_modbus_addresses_with_check(sheet_name)["Analog Inputs"]
#     logger.info(f"INPUT REGISTERS: {analog_inputs}")
#     return analog_inputs
#
# field_data = {}
# def get_data_for_Plc(sheet_name,plc_id):
#      field_data[plc_id] = {
#         "coil_states": get_coils(sheet_name),
#         "input_status_states": get_input_bits(sheet_name),
#         "input_register_states": get_inputs_register(sheet_name)
#      }
#      return field_data


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

    # def create_plc_window(self, plc_name):
    #     if plc_name in self.active_windows:
    #         return True
    #
    #     config = self.plc_configs.get(plc_name)
    #     if not config:
    #         logging.error(f"Invalid PLC {plc_name}")
    #         return False
    #
    #     try:
    #         self.window_counter += 1
    #         window = webview.create_window(
    #             f'PLC {plc_name} Monitoring ({self.window_counter})',
    #             url=f'/data?plc={plc_name}',
    #             js_api=self,  # Ensure this is correctly set
    #             width=1200,
    #             height=800
    #         )
    #
    #         def on_closed():
    #             self.loop.call_soon_threadsafe(
    #                 self.loop.create_task,
    #                 self._handle_window_close(plc_name)
    #             )
    #
    #         window.events.closed += on_closed
    #         self.active_windows[plc_name] = window
    #
    #         self.loop.call_soon_threadsafe(
    #             self.loop.create_task,
    #             self.client_manager.start_plc(config)
    #         )
    #         return True
    #     except Exception as e:
    #         logging.error(f"Window creation failed: {e}")
    #         return False
    # In main.py's WebViewBridge class
    # In WebViewBridge class
    # def get_plc_config(self, plc_name):
    #     config = self.plc_configs.get(plc_name, {})
    #     # excel_data = self.get_modbus_addresses_with_check(plc_name)  # Load from plc_data.xlsx
    #     return {
    #         'addresses': [
    #             {
    #                 'output_no': row['PLC Output No'],
    #                 'coil': row['MODBUS ADDRESS (Coils)'],
    #                 'input_bit_no': row['INPUT BIT NO'],
    #                 'input_bit': row['MODBUS ADDRESS (Input Bits)'],
    #                 'analog_slot': row['PLC ANALOG INPUT SLOT'],
    #                 'register': row['MODBUS ADDRESS (Analog Inputs)']
    #             }
    #             for _, row in excel_data.iterrows()
    #         ]
    #     }
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
                url=f'http://localhost:5000/data?plc={plc_name}',  # Ensure correct URL
                js_api=bridge,  # Pass the bridge instance to the child window
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

    # def get_modbus_addresses_with_check(self, sheet_name):
    #     """Read Modbus addresses from Excel sheet."""
    #     try:
    #         df = pd.read_excel(SAVED_ADDRESS_FILE_PATH, sheet_name=sheet_name)
    #     except Exception as e:
    #         logger.error(f"Error reading Excel file: {e}")
    #         return {"Coils": [], "Input Bits": [], "Analog Inputs": []}
    #
    #     if df.empty:
    #         logger.warning(f"Sheet '{sheet_name}' is empty")
    #         return {"Coils": [], "Input Bits": [], "Analog Inputs": []}
    #
    #     # Extract and adjust addresses
    #     coils = df['MODBUS ADDRESS (Coils)'].dropna().astype(int).tolist()
    #     input_bits = [addr - 10000 for addr in
    #                   df['MODBUS ADDRESS (Input Bits)'].dropna().astype(int).tolist()]
    #     analog_inputs = [addr - 30000 for addr in
    #                      df['MODBUS ADDRESS (Analog Inputs)'].dropna().astype(int).tolist()]
    #
    #     return {
    #         "Coils": coils,
    #         "Input Bits": input_bits,
    #         "Analog Inputs": analog_inputs
    #     }

    def get_plc_data(self, plc_name):
        # get_modbus_addresses_with_check(plc_name)
        # logging.info(f"modbus address: {get_modbus_addresses_with_check(plc_name)}")
        try:
            with data_lock:
                data = global_modbus_data.get(plc_name, {})
                logging.info(f"select plc data: {data} ")
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


# In main.py
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
        webview.start()
        # webview.start(debug=True)
    except Exception as e:
        logging.error(f"Webview startup failed: {e}")
    finally:
        loop.call_soon_threadsafe(loop.stop)
        logging.info("Application shutdown complete")
