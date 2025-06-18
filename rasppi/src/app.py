# app.py
# Main application with a user confirmation loop.

import logging
import threading
import base64
import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
import time

from camera import Camera
from nlp import find_best_match
# from robot_control import send_command_to_mcu

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key!'
socketio = SocketIO(app, async_mode='eventlet')

# --- App State Management ---
app_state = {
    "target_item": None,
    "found_item": None,
    "is_searching": False,
    "detected_objects": [],
    "robot_status": "Idle",
    "best_nlp_guess": "N/A",
    "best_nlp_score": 0.0,
    "ignored_items": set(), # To ignore rejected items temporarily
    "lock": threading.Lock()
}

try:
    camera = Camera()
except Exception as e:
    logging.critical(f"Failed to initialize camera. Application cannot start. Error: {e}")
    exit()


def background_processing_loop():
    logging.info("Starting background processing loop...")
    last_console_update_time = 0

    while True:
        current_detections = camera.get_detected_objects()
        
        with app_state['lock']:
            app_state['detected_objects'] = current_detections
            is_searching = app_state['is_searching']
            target_item = app_state['target_item']
            ignored_items = app_state['ignored_items']

        if is_searching and target_item:
            # Filter out items the user has already rejected
            searchable_detections = [d for d in current_detections if d not in ignored_items]

            match, score = find_best_match(target_item, searchable_detections, threshold=0.6)
            
            with app_state['lock']:
                app_state['best_nlp_guess'] = match or "None"
                app_state['best_nlp_score'] = score
            
            if match:
                logging.info(f"Potential match found: '{match}'. Pausing to ask for user confirmation.")
                
                # --- START CONFIRMATION FLOW ---
                with app_state['lock']:
                    app_state['is_searching'] = False # Pause the search
                    app_state['robot_status'] = f"Confirmation needed for '{match}'"
                
                # send_command_to_mcu('pause_sweep')

                # Get the frame, encode it, and send it to the UI
                confirmation_frame = camera.get_confirmation_frame()
                if confirmation_frame is not None:
                    _, buffer = cv2.imencode('.jpg', confirmation_frame)
                    img_str = base64.b64encode(buffer).decode('utf-8')
                    socketio.emit('request_confirmation', {'label': match, 'image': img_str})
        
        with app_state['lock']:
            status_data = app_state.copy()
            status_data.pop('lock') # Don't send the lock object
            status_data['ignored_items'] = list(status_data['ignored_items']) # Convert set for JSON
        socketio.emit('status_update', status_data)

        if time.time() - last_console_update_time > 2:
            print_console_status(status_data)
            last_console_update_time = time.time()

        socketio.sleep(1)

def print_console_status(state):
    print("\n" + "="*60)
    print(f"ROBOT STATUS UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"  - Robot State      : {state['robot_status']}")
    print(f"  - Searching For    : {state['target_item'] or 'N/A'}")
    print(f"  - Currently Seeing   : {state['detected_objects'] or 'None'}")
    print(f"  - Ignoring         : {state['ignored_items'] or 'None'}")
    print(f"  - NLP Best Guess   : '{state['best_nlp_guess']}' (Score: {state['best_nlp_score']:.4f})")
    print("="*60 + "\n")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global background_thread
    with app_state['lock']:
        if 'background_thread' not in globals():
            background_thread = socketio.start_background_task(target=background_processing_loop)

@socketio.on('set_target')
def handle_set_target(json_data):
    item_description = json_data.get('item', '').strip()
    if not item_description: return
    with app_state['lock']:
        app_state['target_item'] = item_description
        app_state['found_item'] = None
        app_state['is_searching'] = True
        app_state['robot_status'] = f"Searching for '{item_description}'"
        app_state['ignored_items'].clear() # Clear ignore list for new search
    # send_command_to_mcu(command=f'start_sweep:find={item_description}')

@socketio.on('user_confirmation')
def handle_user_confirmation(data):
    confirmed = data.get('confirmed')
    item = data.get('item')
    
    if confirmed:
        logging.info(f"User CONFIRMED '{item}'. Task complete.")
        with app_state['lock']:
            app_state['is_searching'] = False
            app_state['found_item'] = item
            app_state['robot_status'] = f"Task Complete. Found '{item}'."
        # send_command_to_mcu('stop_sweep')
    else:
        logging.info(f"User REJECTED '{item}'. Resuming search.")
        with app_state['lock']:
            app_state['ignored_items'].add(item)
            app_state['is_searching'] = True
            app_state['robot_status'] = f"Resuming search... (ignoring '{item}')"
        # send_command_to_mcu('start_sweep')


if __name__ == '__main__':
    logging.info("Starting Item Finder Application with Confirmation Loop...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
