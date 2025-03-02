import asyncio
import logging
import os
import sys

import numpy as np
import pandas as pd
from ModBus import modbus_client_loop, logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modbus_client.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Suppress pymodbus error logs
logging.getLogger("pymodbus").setLevel(logging.INFO)


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

def get_plc_data():
    """Get list of available PLCs from config"""
    return load_plc_config()
    # return list(set(item['PLC'] for item in config_data if 'PLC' in item))

def filter_plc_data(plc_data):
    """Filter out invalid PLC entries."""
    return [
        plc for plc in plc_data
        if plc["IP Address"] and plc["Port"] > 0  # Only include PLCs with valid IP and port
    ]

async def run_plc_client(plc):
    """Run the Modbus client loop for a single PLC."""
    try:
        await modbus_client_loop(plc["PLC"], plc["IP Address"], plc["Port"],plc["Sampling Frequency"])
    except Exception as e:
        logger.error(f"Error running Modbus client for PLC {plc['PLC']}: {e}")

async def run_client_loops():
    """Run multiple Modbus client loops concurrently."""
    plc_data = get_plc_data()
    filtered_plc_data = filter_plc_data(plc_data)
    if not filtered_plc_data:
        print("No valid PLC data found.")
        return

    # Create a list of tasks for each PLC
    tasks = [run_plc_client(plc) for plc in filtered_plc_data]

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(run_client_loops())