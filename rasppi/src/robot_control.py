# robot_control.py
# Handles serial communication with the robot's MCU (ESP32).

import serial
import logging
import time
import threading

# --- Globals ---
ser = None
# Lock to prevent multiple threads from writing to the serial port simultaneously.
serial_lock = threading.Lock() 

# --- Configuration ---
# You may need to change this depending on how your Raspberry Pi recognizes the ESP32.
# Common values are '/dev/ttyUSB0' or '/dev/ttyACM0'.
# Use 'ls /dev/tty*' on your Pi to check.
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

def initialize_serial():
    """
    Initializes the serial connection to the MCU.
    Attempts to connect and retries if it fails.
    """
    global ser
    while ser is None:
        try:
            with serial_lock:
                logging.info(f"Attempting to connect to MCU on {SERIAL_PORT} at {BAUD_RATE} baud...")
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2) # Wait for the connection to establish
                if ser.is_open:
                    logging.info("Serial connection to MCU established successfully.")
                else:
                    logging.error("Serial port is not open after initialization.")
                    ser = None # Reset for retry
                    time.sleep(5) # Wait before retrying
        except serial.SerialException as e:
            logging.error(f"Failed to connect to MCU on {SERIAL_PORT}: {e}")
            logging.info("Will retry in 5 seconds...")
            ser = None # Ensure ser is None so the loop continues
            time.sleep(5)
        except Exception as e:
            logging.critical(f"An unexpected error occurred during serial initialization: {e}")
            ser = None
            time.sleep(5)


def send_command_to_mcu(command: str):
    """
    Sends a command string to the MCU over the serial port.

    Args:
        command (str): The command to send (e.g., 'start_sweep', 'stop_sweep').
    """
    global ser
    if ser and ser.is_open:
        with serial_lock:
            try:
                # Commands should be terminated with a newline character
                # for easy parsing on the ESP32 side (e.g., using readStringUntil('\n'))
                full_command = (command + '\n').encode('utf-8')
                ser.write(full_command)
                ser.flush() # Wait until all data is written
                logging.info(f"Sent command to MCU: '{command}'")
            except serial.SerialException as e:
                logging.error(f"Error writing to serial port: {e}. Connection might be lost.")
                # Attempt to re-establish connection
                ser.close()
                ser = None
                initialize_serial() # This will block and retry
            except Exception as e:
                logging.error(f"An unexpected error occurred while sending command: {e}")
    else:
        logging.warning(f"Command '{command}' not sent. Serial connection not available.")
        if ser is None:
             # If connection was never established or was lost, try to initialize it again
             logging.info("Attempting to re-initialize serial connection...")
             # Run in a separate thread to avoid blocking the main application logic
             threading.Thread(target=initialize_serial, daemon=True).start()

# --- Initialize on module load ---
# We'll start the initialization in a background thread so it doesn't block the main app at startup.
initialization_thread = threading.Thread(target=initialize_serial, daemon=True)
initialization_thread.start()
