import webview
import pandas as pd
import numpy as np
import os
import asyncio
from main_modbus import modbus_client_loop, read_selected_plc, get_coils, get_input_bits, get_inputs_register

try:
    import openpyxl
except ImportError:
    print("Error: 'openpyxl' is required. Install it using: pip install openpyxl")
    exit(1)

class Api:
    def __init__(self):
        self.plc_config_path = 'plc_data.xlsx'
        self.save_address_path = 'saveAddress.xlsx'
        self.modbus_data = {
            "coil_states": {},
            "input_status_states": {},
            "input_register_states": {}
        }

    def _load_plc_config(self):
        """Load PLC configuration data"""
        if not os.path.exists(self.plc_config_path):
            print(f"Error: File '{self.plc_config_path}' not found.")
            return []

        try:
            df = pd.read_excel(self.plc_config_path)
            df.replace({np.nan: None}, inplace=True)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading PLC config: {e}")
            return []

    def get_plc_list(self):
        """Get list of available PLCs from config"""
        config_data = self._load_plc_config()
        return list(set(item['PLC'] for item in config_data if 'PLC' in item))

    def get_plc_data(self, plc_name):
        """Get data for selected PLC from both files"""
        config_data = self._load_plc_config()
        print("Loaded PLC config data:", config_data)  # Debug

        plc_info = next((item for item in config_data if item.get('PLC') == plc_name), None)
        print(f"PLC info for {plc_name}:", plc_info)  # Debug

        if not plc_info:
            return {
                'sampling_frequency': 'N/A',
                'change_in_data': 'N/A',
                'register_data': []
            }

        try:
            # Get register data from saveAddress
            if not os.path.exists(self.save_address_path):
                print(f"Error: File '{self.save_address_path}' not found.")
                register_data = []
            else:
                df = pd.read_excel(
                    self.save_address_path,
                    sheet_name=plc_name,
                    usecols=[
                        'PLC OUTPUT NO',
                        'MODBUS ADDRESS (Coils)',
                        'States (Coils)',
                        'INPUT BIT NO',
                        'MODBUS ADDRESS (Input Bits)',
                        'States (Input Bits)',
                        'PLC ANALOG INPUT SLOT',
                        'MODBUS ADDRESS (Analog Inputs)',
                        'Values'
                    ]
                )
                register_data = df.replace({np.nan: None}).to_dict('records')
                print(f"Register data for {plc_name}:", register_data)  # Debug

            return {
                'sampling_frequency': plc_info.get('Sampling Frequency', 'N/A'),
                'change_in_data': plc_info.get('Change in Data', 'N/A'),
                'register_data': register_data
            }

        except Exception as e:
            print(f"Error loading data for {plc_name}: {str(e)}")
            return {
                'sampling_frequency': 'N/A',
                'change_in_data': 'N/A',
                'register_data': []
            }

    def create_plc_window(self, plc_name):
        # Create a new webview window for the PLC
        window = webview.create_window(
            f'{plc_name} Data',
            url='web/plc_window.html',  # Create a template HTML file
            js_api=self,
            width=1400,
            height=800
        )
        return True

    def get_modbus_data(self):
        """Return the latest Modbus data"""
        return self.modbus_data

    async def run_modbus_client(self):
        """Run the Modbus client loop in the background"""
        while True:
            try:
                # Fetch the latest Modbus data
                coil_states, input_status_states, input_register_states = await modbus_client_loop("127.0.0.1", 502)

                # Update the global modbus_data dictionary
                self.modbus_data["coil_states"] = coil_states
                self.modbus_data["input_status_states"] = input_status_states
                self.modbus_data["input_register_states"] = input_register_states

            except Exception as e:
                print(f"Error in Modbus client loop: {e}")

if __name__ == '__main__':
    api = Api()
    data = api.get_plc_list()
    print(data)

    # Start the Modbus client loop in the background
    asyncio.create_task(api.run_modbus_client())

    # Start the webview window
    window = webview.create_window(
        'PLC Monitor',
        'web/home.html',
        js_api=api,
        width=600,
        height=600
    )
    webview.start()