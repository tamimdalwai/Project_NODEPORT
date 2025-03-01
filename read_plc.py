import os
import pandas as pd
import logging

# Set up logging
log_file_path = "logs/read_plc_log.log"
logging.basicConfig(
    filename=log_file_path,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
saved_address_file_path = r"config\saveAddress.xlsx"
# Function to read the selected PLC from the text file and print it to the console




def read_selected_plc():
    """Function to read the selected PLC from the text file and log it."""
    selected_plc = "config/selectedPlc.txt"

    # Check if the file exists
    if os.path.exists(selected_plc):
        try:
            with open(selected_plc, "r") as file:
                selected_plc = file.read().strip()  # Read and strip any extra whitespace/newlines
                logging.info(f"Selected PLC: {selected_plc}")
                return selected_plc
        except Exception as e:
            logging.error(f"Error reading the file: {e}")
    else:
        logging.warning("The file 'selectedPlc.txt' does not exist.")


# Function to check and get Modbus addresses from the Excel sheet
def get_modbus_addresses_with_check(saved_address_file_path, sheet_name):
    try:
        df = pd.read_excel(saved_address_file_path, sheet_name=sheet_name)
    except ValueError as ve:
        logging.error(f"Sheet '{sheet_name}' does not exist or is empty: {ve}")
        return f"Sheet '{sheet_name}' does not exist or is empty."
    except FileNotFoundError as fnf_error:
        logging.error(f"File '{saved_address_file_path}' not found: {fnf_error}")
        return f"File '{saved_address_file_path}' not found."

    if df.empty:
        logging.warning(f"Sheet '{sheet_name}' is empty.")
        return f"Sheet '{sheet_name}' is empty."

    # Extract the non-null addresses from each relevant column
    coils_addresses = df['MODBUS ADDRESS (Coils)'].dropna()
    input_bits_addresses = df['MODBUS ADDRESS (Input Bits)'].dropna()
    analog_inputs_addresses = df['MODBUS ADDRESS (Analog Inputs)'].dropna()

    if coils_addresses.empty and input_bits_addresses.empty and analog_inputs_addresses.empty:
        logging.info(f"No addresses found in sheet '{sheet_name}'.")
        return f"No addresses found in sheet '{sheet_name}'."

    # Log the counts and return a dictionary with the counts of each address type
    logging.info(f"Addresses found in sheet '{sheet_name}': Coils: {len(coils_addresses)}, Input Bits: {len(input_bits_addresses)}, Analog Inputs: {len(analog_inputs_addresses)}")
    return {
        "Coils": len(coils_addresses),
        "Input Bits": len(input_bits_addresses),
        "Analog Inputs": len(analog_inputs_addresses)
    }


# Helper function to get the number of coils
def get_coils(saved_address_file_path, sheet_name):
    modbus_addresses = get_modbus_addresses_with_check(saved_address_file_path, sheet_name)
    if isinstance(modbus_addresses, str):
        logging.error(modbus_addresses)
        return 0
    return modbus_addresses.get("Coils", 0)



# Helper function to get the number of input bits
def get_input_bits(saved_address_file_path, sheet_name):
    modbus_addresses = get_modbus_addresses_with_check(saved_address_file_path, sheet_name)
    if isinstance(modbus_addresses, str):
        logging.error(modbus_addresses)
        return 0
    return modbus_addresses.get("Input Bits", 0)


# Helper function to get the number of analog inputs
def get_analog_inputs(saved_address_file_path, sheet_name):
    modbus_addresses = get_modbus_addresses_with_check(saved_address_file_path, sheet_name)
    if isinstance(modbus_addresses, str):
        logging.error(modbus_addresses)
        return 0
    return modbus_addresses.get("Analog Inputs", 0)




