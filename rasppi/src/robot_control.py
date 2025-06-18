# robot_control.py
# Handles serial communication with the robot's MCU (ESP32), including sending and receiving data.

import serial
import logging
import time
import threading
from queue import Queue

# --- Globals ---
ser = None
# Lock to prevent multiple threads from writing to the serial port simultaneously.
serial_lock = threading.Lock() 
# Thread-safe queue for incoming messages from the MCU.
incoming_message_queue = Queue()
# Global handle for the reader thread
reader_thread = None

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

def _serial_reader_thread():
    """
    Private function to run in a background thread.
    Continuously reads from the serial port and puts messages in a queue.
    """
    global ser
    logging.info("Serial reader thread started.")
    while True:
        if ser and ser.is_open:
            try:
                # Read a line from the serial port, which blocks until a newline is received or timeout occurs
                line = ser.readline()
                if line:
                    # Decode from bytes to string and strip leading/trailing whitespace
                    message = line.decode('utf-8').strip()
                    if message:
                        logging.info(f"Received from MCU: '{message}'")
                        # Put the message into the thread-safe queue
                        incoming_message_queue.put(message)
            except serial.SerialException as e:
                logging.error(f"Serial read error: {e}. Connection may be lost.")
                # The main loop will handle reconnection
                time.sleep(1)
            except Exception as e:
                logging.error(f"An unexpected error occurred in the serial reader thread: {e}")
                time.sleep(1)
        else:
            # Wait if the serial port is not available
            time.sleep(1)

def initialize_serial():
    """
    Initializes the serial connection to the MCU and starts the reader thread.
    Attempts to connect and retries if it fails.
    """
    global ser, reader_thread
    
    # Start the reader thread if it's not already running
    if reader_thread is None or not reader_thread.is_alive():
        reader_thread = threading.Thread(target=_serial_reader_thread, daemon=True)
        reader_thread.start()

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
        command (str): The command to send (e.g., 'i', 'o').
    """
    global ser
    if ser and ser.is_open:
        with serial_lock:
            try:
                full_command = (command).encode('utf-8')
                ser.write(full_command)
                ser.flush() 
                logging.info(f"Sent command to MCU: '{command}'")
            except serial.SerialException as e:
                logging.error(f"Error writing to serial port: {e}. Connection might be lost.")
                ser.close()
                ser = None
                initialize_serial()
            except Exception as e:
                logging.error(f"An unexpected error occurred while sending command: {e}")
    else:
        logging.warning(f"Command '{command}' not sent. Serial connection not available.")
        if ser is None:
             logging.info("Attempting to re-initialize serial connection...")
             threading.Thread(target=initialize_serial, daemon=True).start()

def get_latest_mcu_message():
    """
    Retrieves the latest message from the MCU without blocking.

    Returns:
        str: The oldest message from the queue, or None if the queue is empty.
    """
    if not incoming_message_queue.empty():
        return incoming_message_queue.get_nowait()
    return None

# --- Initialize on module load ---
initialization_thread = threading.Thread(target=initialize_serial, daemon=True)
initialization_thread.start()