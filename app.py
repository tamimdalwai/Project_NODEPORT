import webview
import pandas as pd
import numpy as np
import os
import asyncio
from main import global_modbus_data

print(global_modbus_data)

class Api:
    def __init__(self):
        self.plc_config_path = 'config\\plc_data.xlsx'
        self.save_address_path = 'config\\saveAddress.xlsx'

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
        """Get real-time data for selected PLC"""
        if plc_name not in global_modbus_data:
            return {
                'coil_states': {},
                'input_status_states': {},
                'input_register_states': {}
            }

        return global_modbus_data[plc_name]

    def create_plc_window(self, plc_name):
        """Create a new webview window for the PLC"""
        window = webview.create_window(
            f'{plc_name} Data',
            url='web/plc_window.html',
            js_api=self,
            width=1400,
            height=800
        )
        return True

if __name__ == '__main__':
    api = Api()
    data = api.get_plc_list()
    print(data)

    # Start the webview window
    window = webview.create_window(
        'PLC Monitor',
        'web/home.html',
        js_api=api,
        width=600,
        height=600
    )
    webview.start()