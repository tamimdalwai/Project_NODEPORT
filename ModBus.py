import asyncio
import sys
import logging
import os
import pandas as pd
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.client import AsyncModbusTcpClient
import time
from openpyxl import Workbook, load_workbook
from datetime import datetime



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
# logging.getLogger("pymodbus").setLevel(logging.INFO)
logging.getLogger("pymodbus").setLevel(logging.WARNING)

# Configuration paths
SAVED_ADDRESS_FILE_PATH = "config/saveAddress.xlsx"
SELECTED_PLC_FILE = "config/selectedPlc.txt"
sampling_frequency = 1000

# Initialize plc_state dictionary
plc_state = {}


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


def get_coils(sheet_name):
    """Get coil addresses for selected PLC."""
    logger.info(f"COILS: {get_modbus_addresses_with_check(sheet_name)["Coils"]}")
    return get_modbus_addresses_with_check(sheet_name)["Coils"]


def get_input_bits(sheet_name):
    """Get input bit addresses for selected PLC."""
    logger.info(f"INPUT BITS: {get_modbus_addresses_with_check(sheet_name)["Input Bits"]}")
    return get_modbus_addresses_with_check(sheet_name)["Input Bits"]


def get_inputs_register(sheet_name):
    """Get input register addresses for selected PLC."""
    logger.info(f"INPUT REGISTERS: {get_modbus_addresses_with_check(sheet_name)["Analog Inputs"]}")
    return get_modbus_addresses_with_check(sheet_name)["Analog Inputs"]


def show_popup_and_wait(message):
    """Handle connection failures with user input."""
    logger.info(message)
    response = input("Retry? (y/n): ").strip().lower()
    return response == 'y'


async def check_connection(client, plc_id, retry_interval=5):
    """Verify Modbus connection with retry logic."""
    try:
        logger.info("Checking connection...")
        connection_ok = False

        # Try reading different register types
        for read_func, addresses in [
            (client.read_coils, get_coils(plc_id)),
            (client.read_discrete_inputs, get_input_bits(plc_id)),
            (client.read_input_registers, get_inputs_register(plc_id))
        ]:
            if addresses:
                logger.info(f"Check Connection: Addresses: {addresses}")
                # getLength =  addresses
                response = await read_func(address=0, count=len(addresses))
                if not response.isError():
                    connection_ok = True
                    break

        plc_state[plc_id] = {"connected": connection_ok}
        logger.info(f"PLC {plc_id} connected: {connection_ok}")
        return connection_ok

    except Exception as e:
        logger.error(f"Connection error: {e}")
        plc_state[plc_id] = {"connected": False}

        if not show_popup_and_wait(f"Connection failed: {e}"):
            logger.info("Connection attempts cancelled")
            exit(0)

        time.sleep(retry_interval)
        logger.info("Retrying connection...")
        return check_connection(client, plc_id, retry_interval)

async def append_to_excel(data):
    """Append Modbus data to separate Excel files based on PLC ID and register type."""
    logger.info(f"EXCEL DATA: {data}")
    plc_id = data["plc_id"]
    coil_states = data["coil_states"]
    input_status_states = data["input_status_states"]
    input_register_states = data["input_register_states"]

    # Create folder based on PLC ID if it doesn't exist
    folder_path = os.path.join("modbus_data", plc_id)
    os.makedirs(folder_path, exist_ok=True)

    # Define file paths for each register type
    coil_file = os.path.join(folder_path, "coil_states.xlsx")
    input_status_file = os.path.join(folder_path, "input_status_states.xlsx")
    input_register_file = os.path.join(folder_path, "input_register_states.xlsx")

    # Append data to each file asynchronously
    await asyncio.gather(
        _append_register_data(coil_file, "Coil States", coil_states),
        _append_register_data(input_status_file, "Input Status States", input_status_states),
        _append_register_data(input_register_file, "Input Register States", input_register_states, is_input_register=True)
    )

async def _append_register_data(file_path, sheet_name, data, is_input_register=False):
    """Helper function to append data to a specific Excel file."""
    if not data:  # Skip if data is empty
        logger.info(f"No data to append for {sheet_name}")
        return

    try:
        # Load or create the workbook
        if os.path.exists(file_path):
            wb = load_workbook(file_path)
            ws = wb.active
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            # Create headers
            addresses = [f"{addr:05}" for addr in sorted(data.keys())]
            ws.append(["Date", "Time"] + addresses)

        # Append data
        timestamp = datetime.now()
        date = timestamp.strftime("%Y-%m-%d")
        time = timestamp.strftime("%H:%M:%S")


        # For input registers and coil states, append values in order of addresses
        values = [data[addr] for addr in sorted(data.keys())]
        ws.append([date, time] + values)
        # Save the workbook
        wb.save(file_path)
        logger.info(f"Data appended to {file_path}")

    except Exception as e:
        logger.error(f"Error appending data to {file_path}: {e}")

async def read_registers(client, read_func, addresses, max_count=2000):
    """
    Generic register reading function with address grouping.
    Handles non-sequential addresses by splitting them into sequential ranges.
    Works for coils, discrete inputs, and input registers.
    """
    results = {}
    try:
        sorted_addrs = sorted(addresses)
        start = sorted_addrs[0]
        prev_addr = start

        for addr in sorted_addrs[1:]:
            # If the address is not sequential or exceeds max_count, read the current range
            if addr != prev_addr + 1 or (addr - start + 1) > max_count:
                count = prev_addr - start + 1
                read_address = start - 1  # Adjust for zero-based addressing

                # Handle input registers separately
                if read_func == client.read_input_registers:
                    response = await read_func(address=read_address, count=count)
                    if not response.isError():
                        results.update({
                            a: response.registers[i]
                            for i, a in enumerate(range(start, prev_addr + 1))
                            if a in addresses
                        })
                else:
                    # Handle coils and discrete inputs
                    response = await read_func(address=read_address, count=count)
                    if not response.isError():
                        results.update({
                            a: response.bits[i]
                            for i, a in enumerate(range(start, prev_addr + 1))
                            if a in addresses
                        })

                start = addr  # Start a new range

            prev_addr = addr

        # Read the last range
        count = prev_addr - start + 1
        read_address = start - 1  # Adjust for zero-based addressing

        if read_func == client.read_input_registers:
            response = await read_func(address=read_address, count=count)
            if not response.isError():
                results.update({
                    a: response.registers[i]
                    for i, a in enumerate(range(start, prev_addr + 1))
                    if a in addresses
                })
        else:
            response = await read_func(address=read_address, count=count)
            if not response.isError():
                results.update({
                    a: response.bits[i]
                    for i, a in enumerate(range(start, prev_addr + 1))
                    if a in addresses
                })
        await asyncio.sleep(sampling_frequency / 1000)
        return results

    except ModbusException as e:
        logger.error(f"Modbus error while reading registers: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error while reading registers: {e}")
        return {}


async def modbus_client_loop(plc_id, ip, port,sampling_frequency):
    """Main Modbus client loop."""
    logger.info(f"Starting Modbus client loop for PLC {plc_id} at {ip}:{port}")

    # Update the selected_plc value dynamically
    selected_plc = plc_id
    coils = get_coils(selected_plc)
    input_status = get_input_bits(selected_plc)
    input_register = get_inputs_register(selected_plc)
    sampling_frequency = sampling_frequency

    async with AsyncModbusTcpClient(ip, port=port) as client:
        while True:
            # Ensure the client is connected
            if not client.connected:
                logger.error("Client not connected. Attempting to reconnect...")
                if not await client.connect():
                    logger.error("Connection failed")
                    if not show_popup_and_wait("Connection failed - retry?"):
                        logger.info("User cancelled retry. Exiting...")
                        break
                    continue

            # Check connection status
            if not await check_connection(client, selected_plc):
                logger.warning(f"Connection check failed for PLC {selected_plc}. Retrying...")
                await asyncio.sleep(5)  # Wait before retrying
                continue

            try:
                # Read all registers in parallel
                coil_states, input_states, register_states = await asyncio.gather(
                    read_registers(client, client.read_coils, coils),
                    read_registers(client, client.read_discrete_inputs, input_status),
                    read_registers(client, client.read_input_registers, input_register, max_count=125)
                )

                # Log the results
                logger.debug(f"Coil States: {coil_states}")
                logger.debug(f"Input Status States: {input_states}")
                logger.debug(f"Input Register States: {register_states}")

                # Save results to Excel
                await append_to_excel({
                    "plc_id": selected_plc,
                    "coil_states": coil_states,
                    "input_status_states": input_states,
                    "input_register_states": register_states
                })

            except ModbusException as e:
                logger.error(f"Modbus error during register reading: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during register reading: {e}")

            # Wait for the next sampling interval
            await asyncio.sleep(3)

async def main():
    """Main async function."""
    await modbus_client_loop("192.168.0.130", 502)
    await modbus_client_loop("127.0.0.1", 503)


if __name__ == "__main__":
    asyncio.run(main())