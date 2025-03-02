# In your Api class (main.py)
from pymodbus.client import AsyncModbusTcpClient


class Api:
    latest_data = {}  # Class-level variable to store live values

    def __init__(self):
        self.plc_config_path = 'web/plc_data.xlsx'
        self.save_address_path = 'web/saveAddress.xlsx'
        self.static_plc_data = {}  # Cache for static config

    def get_plc_data(self, plc_name):
        # ... [existing config loading logic] ...

        # Merge with live data
        live_data = self.latest_data.get(plc_name, {})
        register_data = self._get_static_data(plc_name)  # Load from cache or Excel

        # Update each register with live values
        for row in register_data:
            coil_addr = row.get('MODBUS ADDRESS (Coils)')
            if coil_addr is not None:
                row['States (Coils)'] = live_data.get('coils', {}).get(int(coil_addr), 0)

            # Similar updates for input bits and registers
            input_bit = row.get('MODBUS ADDRESS (Input Bits)')
            if input_bit is not None:
                row['States (Input Bits)'] = live_data.get('input_bits', {}).get(int(input_bit), 0)

            analog = row.get('MODBUS ADDRESS (Analog Inputs)')
            if analog is not None:
                row['Values'] = live_data.get('input_registers', {}).get(int(analog), 0)

        return {
            'sampling_frequency': sampling,
            'change_in_data': change,
            'register_data': register_data
        }


# In modbus client (main_modbus.py)
async def modbus_client_loop(ip, port):
    async with AsyncModbusTcpClient(ip, port) as client:
        while True:
            # ... [read coil_states, input_status_states, input_register_states] ...

            # Update Api with latest values
            Api.latest_data[selectedPlc] = {
                'coils': coil_states,
                'input_bits': input_status_states,
                'input_registers': input_register_states
            }