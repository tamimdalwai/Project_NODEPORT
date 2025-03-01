# import webview
# import pandas as pd
# import numpy as np
# import os
#
# try:
#     import openpyxl
# except ImportError:
#     print("Error: 'openpyxl' is required. Install it using: pip install openpyxl")
#     exit(1)
#
# class Api:
#     def __init__(self):
#         self.plc_config_path = 'plc_data.xlsx'
#         self.save_address_path = 'saveAddress.xlsx'
#
#     def _load_plc_config(self):
#         """Load PLC configuration data"""
#         if not os.path.exists(self.plc_config_path):
#             print(f"Error: File '{self.plc_config_path}' not found.")
#             return []
#
#         try:
#             df = pd.read_excel(self.plc_config_path)
#             df.replace({np.nan: None}, inplace=True)
#             return df.to_dict('records')
#         except Exception as e:
#             print(f"Error loading PLC config: {e}")
#             return []
#
#     def get_plc_list(self):
#         """Get list of available PLCs from config"""
#         config_data = self._load_plc_config()
#         return [item['PLC'] for item in config_data if 'PLC' in item]
#
#     def get_plc_data(self, plc_name):
#         """Get data for selected PLC from both files"""
#         config_data = self._load_plc_config()
#         print("Loaded PLC config data:", config_data)  # Debug
#
#         plc_info = next((item for item in config_data if item.get('PLC') == plc_name), None)
#         print(f"PLC info for {plc_name}:", plc_info)  # Debug
#
#         if not plc_info:
#             return {
#                 'sampling_frequency': 'N/A',
#                 'change_in_data': 'N/A',
#                 'register_data': []
#             }
#
#         try:
#             # Get register data from saveAddress
#             if not os.path.exists(self.save_address_path):
#                 print(f"Error: File '{self.save_address_path}' not found.")
#                 register_data = []
#             else:
#                 df = pd.read_excel(
#                     self.save_address_path,
#                     sheet_name=plc_name,
#                     usecols=[
#                         'PLC OUTPUT NO',
#                         'MODBUS ADDRESS (Coils)',
#                         'States (Coils)',
#                         'INPUT BIT NO',
#                         'MODBUS ADDRESS (Input Bits)',
#                         'States (Input Bits)',
#                         'PLC ANALOG INPUT SLOT',
#                         'MODBUS ADDRESS (Analog Inputs)',
#                         'Values'
#                     ]
#                 )
#                 register_data = df.replace({np.nan: None}).to_dict('records')
#                 print(f"Register data for {plc_name}:", register_data)  # Debug
#
#             return {
#                 'sampling_frequency': plc_info.get('Sampling Frequency', 'N/A'),
#                 'change_in_data': plc_info.get('Change in Data', 'N/A'),
#                 'register_data': register_data
#             }
#
#         except Exception as e:
#             print(f"Error loading data for {plc_name}: {str(e)}")
#             return {
#                 'sampling_frequency': 'N/A',
#                 'change_in_data': 'N/A',
#                 'register_data': []
#             }
# if __name__ == '__main__':
#     api = Api()
#     window = webview.create_window(
#         'PLC Monitor',
#         'web/home.html',
#         js_api=api,
#         width=1400,
#         height=800
#     )
#     webview.start()

import webview
import pandas as pd
import numpy as np
import os

try:
    import openpyxl
except ImportError:
    print("Error: 'openpyxl' is required. Install it using: pip install openpyxl")
    exit(1)

class Api:
    def __init__(self):
        self.plc_config_path = 'plc_data.xlsx'
        self.save_address_path = 'saveAddress.xlsx'

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

if __name__ == '__main__':
    api = Api()
    data  = api.get_plc_list()
    print(data)
    window = webview.create_window(
        'PLC Monitor',
        'web/home.html',
        js_api=api,
        width=1400,
        height=800
    )
    webview.start()