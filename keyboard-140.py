# Version 1.4.0 (Raspberry Pi)
import RPi.GPIO as GPIO
import time
import random
import string
from datetime import datetime
from rpi_ws281x import PixelStrip, Color, WS2811_STRIP_RGB
import logging

# Set up logging
logging.basicConfig(
    filename='keyboard_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# GPIO pin assignments
ROW_PINS = [0, 1, 2]
COL_PINS = [3, 4, 5, 6, 7, 8, 9]
EXTRA_ROW_PINS = [10, 11]
EXTRA_COL_PINS = [12, 13]
SPEAKER_PIN = 16
NEO_PIN = 21
NUM_PIXELS = 26

# Colors - Explicitly define RGB values for WS2811
RED = Color(255, 0, 0)      # Pure red
GREEN = Color(0, 255, 0)    # Pure green
BLUE = Color(0, 0, 255)     # Pure blue
WHITE = Color(255, 255, 255)  # White

# Define colors for different states
SELECTED_COLOR = GREEN
RETURN_COLOR = GREEN
BACKSPACE_COLOR = RED
DEFAULT_COLOR = WHITE

# Button and key mappings (same as before)
BUTTON_MAP_3x7 = [
    [1, 2, 3, 4, 5, 6, 7],
    [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21]
]
BUTTON_MAP_2x2 = [
    [22, 23],
    [24, 25]
]

PIXEL_MAP_3x7 = [
    [1, 2, 3, 4, 5, 6, 7],
    [17, 16, 15, 14, 13, 12, 11],
    [18, 19, 20, 21, 22, 23, 24]
]
PIXEL_MAP_2x2 = [
    [8, 9],
    [25, 26]
]

KEY_MAP_3x7 = [
    ["A", "B", "C", "D", "E", "F", "G"],
    ["I", "J", "K", "L", "M", "N", "O"],
    ["P", "Q", "R", "S", "T", "U", "V"]
]
KEY_MAP_2x2 = [
    ["H", "RETURN"],
    ["X", "BACKSPACE"]
]

class KeyboardRecorder:
    def __init__(self):
        self.current_session_keys = []
        self.selected_keys = set()
        self.current_user_id = self.generate_user_id()
        self.strip = None
        self.setup_neopixels()
        self.setup_audio()
        self.last_keypress_time = 0
        self.debounce_delay = 0.2
        self.matrix_state = [[False for _ in COL_PINS] for _ in ROW_PINS]
        self.extra_matrix_state = [[False for _ in EXTRA_COL_PINS] for _ in EXTRA_ROW_PINS]
        
    def setup_audio(self):
        """Initialize PWM for the speaker"""
        try:
            self.pwm = GPIO.PWM(SPEAKER_PIN, 440)  # Start with 440 Hz (A4 note)
            self.pwm.start(0)  # Start with 0% duty cycle (silent)
            logging.info("Audio PWM initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize audio PWM: {e}")
            raise

    def play_key_beep(self):
        """Play a short beep for regular key presses"""
        try:
            self.pwm.ChangeFrequency(440)  # A4 note
            self.pwm.ChangeDutyCycle(50)
            time.sleep(0.05)  # Short duration
            self.pwm.ChangeDutyCycle(0)
        except Exception as e:
            logging.error(f"Error playing key beep: {e}")

    def play_success_sound(self):
        """Play a success melody when Return is pressed"""
        try:
            # Play an ascending arpeggio
            notes = [
                (392, 0.1),  # G4
                (493.88, 0.1),  # B4
                (587.33, 0.1),  # D5
                (783.99, 0.2)   # G5
            ]
            
            for freq, duration in notes:
                self.pwm.ChangeFrequency(freq)
                self.pwm.ChangeDutyCycle(50)
                time.sleep(duration)
                
            self.pwm.ChangeDutyCycle(0)
        except Exception as e:
            logging.error(f"Error playing success sound: {e}")

    def setup_neopixels(self):
        try:
            # Initialize with explicit WS2811 RGB strip type
            self.strip = PixelStrip(NUM_PIXELS, NEO_PIN, strip_type=WS2811_STRIP_RGB)
            self.strip.begin()
            self.set_default_colors()
            logging.info("NeoPixels initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize NeoPixels: {e}")
            raise
            
    def set_default_colors(self):
        """Set all LEDs to their default states"""
        for i in range(NUM_PIXELS):
            self.strip.setPixelColor(i, WHITE_COLOR)
        
        return_pixel = self.find_pixel_index("RETURN")
        backspace_pixel = self.find_pixel_index("BACKSPACE")
        if return_pixel >= 0:
            self.strip.setPixelColor(return_pixel, GREEN_COLOR)
        if backspace_pixel >= 0:
            self.strip.setPixelColor(backspace_pixel, RED_COLOR)
        
        self.strip.show()

    def generate_user_id(self):
        adjectives = ["Quick", "Happy", "Bright", "Calm", "Sharp", "Brave", "Smart", "Kind", "Loyal", "Wise"]
        animals = ["Fox", "Bear", "Wolf", "Eagle", "Tiger", "Lion", "Deer", "Owl", "Hawk", "Shark"]
        return f"{random.choice(adjectives)}{random.choice(animals)}{random.randint(1000,9999)}"

    def toggle_key(self, key):
        """Toggle a key's selected state"""
        pixel_index = self.find_pixel_index(key)
        if pixel_index >= 0:
            if key in self.selected_keys:
                self.selected_keys.remove(key)
                self.strip.setPixelColor(pixel_index, WHITE_COLOR)
            else:
                self.selected_keys.add(key)
                self.strip.setPixelColor(pixel_index, GREEN_COLOR)
            self.strip.show()

    def handle_keypress(self, key):
        current_time = time.time()
        
        if current_time - self.last_keypress_time < self.debounce_delay:
            return
            
        self.last_keypress_time = current_time
        logging.debug(f"Key pressed: {key}")

        if key == "BACKSPACE":
            self.play_key_beep()
            self.selected_keys.clear()
            self.set_default_colors()
        elif key == "RETURN":
            if self.selected_keys:  # Only play success sound if there are selected keys
                self.play_success_sound()
            self.current_session_keys = list(self.selected_keys)
            self.save_session()
            self.selected_keys.clear()
            self.current_session_keys = []
            self.current_user_id = self.generate_user_id()
            self.set_default_colors()
        else:
            self.play_key_beep()
            self.toggle_key(key)

    def find_pixel_index(self, key):
        for row_idx, row in enumerate(KEY_MAP_3x7):
            if key in row:
                col_idx = row.index(key)
                return PIXEL_MAP_3x7[row_idx][col_idx] - 1
        for row_idx, row in enumerate(KEY_MAP_2x2):
            if key in row:
                col_idx = row.index(key)
                return PIXEL_MAP_2x2[row_idx][col_idx] - 1
        return -1

    def save_session(self):
        try:
            if self.selected_keys:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session_data = f"{self.current_user_id},{''.join(sorted(self.selected_keys))},{timestamp}\n"
                
                with open("keypress_log.csv", "a") as log_file:
                    log_file.write(session_data)
                logging.info(f"Session saved: {session_data.strip()}")
        except Exception as e:
            logging.error(f"Error saving session: {e}")

    def scan_matrix(self):
        current_time = time.time()
        if (current_time - self.last_keypress_time) < self.debounce_delay:
            return

        # Reset all row pins to HIGH
        for pin in ROW_PINS + EXTRA_ROW_PINS:
            GPIO.output(pin, GPIO.HIGH)

        key_detected = False
        
        # Scan main matrix (3x7)
        for row_idx, row_pin in enumerate(ROW_PINS):
            # Set current row LOW
            GPIO.output(row_pin, GPIO.LOW)
            time.sleep(0.001)  # Allow signal to settle
            
            # Read all columns for this row
            for col_idx, col_pin in enumerate(COL_PINS):
                is_pressed = GPIO.input(col_pin) == GPIO.LOW
                
                # If this is a new keypress
                if is_pressed and not self.matrix_state[row_idx][col_idx]:
                    key = KEY_MAP_3x7[row_idx][col_idx]
                    self.handle_keypress(key)
                    key_detected = True
                    self.last_keypress_time = current_time
                
                # Update state
                self.matrix_state[row_idx][col_idx] = is_pressed
            
            # Set row back to HIGH
            GPIO.output(row_pin, GPIO.HIGH)
            
            if key_detected:
                return

        # Scan extra matrix (2x2) only if no key was detected in main matrix
        if not key_detected:
            for row_idx, row_pin in enumerate(EXTRA_ROW_PINS):
                GPIO.output(row_pin, GPIO.LOW)
                time.sleep(0.001)
                
                for col_idx, col_pin in enumerate(EXTRA_COL_PINS):
                    is_pressed = GPIO.input(col_pin) == GPIO.LOW
                    
                    if is_pressed and not self.extra_matrix_state[row_idx][col_idx]:
                        key = KEY_MAP_2x2[row_idx][col_idx]
                        self.handle_keypress(key)
                        self.last_keypress_time = current_time
                    
                    self.extra_matrix_state[row_idx][col_idx] = is_pressed
                
                GPIO.output(row_pin, GPIO.HIGH)

        time.sleep(0.001)  # Small delay at the end of scanning

    def set_default_colors(self):
        """Set all LEDs to their default states"""
        for i in range(NUM_PIXELS):
            self.strip.setPixelColor(i, DEFAULT_COLOR)
        
        return_pixel = self.find_pixel_index("RETURN")
        backspace_pixel = self.find_pixel_index("BACKSPACE")
        if return_pixel >= 0:
            self.strip.setPixelColor(return_pixel, RETURN_COLOR)
        if backspace_pixel >= 0:
            self.strip.setPixelColor(backspace_pixel, BACKSPACE_COLOR)
        
        self.strip.show()

    def toggle_key(self, key):
        """Toggle a key's selected state"""
        pixel_index = self.find_pixel_index(key)
        if pixel_index >= 0:
            if key in self.selected_keys:
                self.selected_keys.remove(key)
                self.strip.setPixelColor(pixel_index, DEFAULT_COLOR)
                logging.debug(f"Key {key} deselected, pixel {pixel_index} set to DEFAULT")
            else:
                self.selected_keys.add(key)
                self.strip.setPixelColor(pixel_index, SELECTED_COLOR)
                logging.debug(f"Key {key} selected, pixel {pixel_index} set to SELECTED")
            self.strip.show()

def handle_keypress(self, key):
        current_time = time.time()
        
        if current_time - self.last_keypress_time < self.debounce_delay:
            return
            
        self.last_keypress_time = current_time
        logging.debug(f"Key pressed: {key}")

        if key == "BACKSPACE":
            self.play_key_beep()
            self.selected_keys.clear()
            self.set_default_colors()
        elif key == "RETURN":
            if self.selected_keys:  # Only play success sound if there are selected keys
                self.play_success_sound()
            self.current_session_keys = list(self.selected_keys)
            self.save_session()
            self.selected_keys.clear()
            self.current_session_keys = []
            self.current_user_id = self.generate_user_id()
            self.set_default_colors()
        else:
            self.play_key_beep()
            self.toggle_key(key)

def find_pixel_index(self, key):
        for row_idx, row in enumerate(KEY_MAP_3x7):
            if key in row:
                col_idx = row.index(key)
                return PIXEL_MAP_3x7[row_idx][col_idx] - 1
        for row_idx, row in enumerate(KEY_MAP_2x2):
            if key in row:
                col_idx = row.index(key)
                return PIXEL_MAP_2x2[row_idx][col_idx] - 1
        return -1

def save_session(self):
        try:
            if self.selected_keys:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session_data = f"{self.current_user_id},{''.join(sorted(self.selected_keys))},{timestamp}\n"
                
                with open("keypress_log.csv", "a") as log_file:
                    log_file.write(session_data)
                logging.info(f"Session saved: {session_data.strip()}")
        except Exception as e:
            logging.error(f"Error saving session: {e}")

def scan_matrix(self):
        # Reset current pressed key if enough time has passed (key release)
        if (time.time() - self.last_keypress_time) > self.debounce_delay:
            self.current_pressed_key = None

        # Only scan if no key is currently being pressed
        if self.current_pressed_key is None:
            # Scan 3x7 matrix
            for row in range(len(ROW_PINS)):
                GPIO.output(ROW_PINS[row], GPIO.LOW)
                time.sleep(0.001)  # Small delay to stabilize
                
                for col in range(len(COL_PINS)):
                    if GPIO.input(COL_PINS[col]) == GPIO.LOW:
                        key = KEY_MAP_3x7[row][col]
                        if self.current_pressed_key is None:  # Only register if no other key is pressed
                            self.current_pressed_key = key
                            self.handle_keypress(key)
                            self.last_keypress_time = time.time()
                            break  # Exit after first key detection
                
                GPIO.output(ROW_PINS[row], GPIO.HIGH)
                
                if self.current_pressed_key:  # If we found a key, stop scanning
                    break

            # Only scan 2x2 matrix if no key was found in 3x7 matrix
            if not self.current_pressed_key:
                for row in range(len(EXTRA_ROW_PINS)):
                    GPIO.output(EXTRA_ROW_PINS[row], GPIO.LOW)
                    time.sleep(0.001)
                    
                    for col in range(len(EXTRA_COL_PINS)):
                        if GPIO.input(EXTRA_COL_PINS[col]) == GPIO.LOW:
                            key = KEY_MAP_2x2[row][col]
                            if self.current_pressed_key is None:
                                self.current_pressed_key = key
                                self.handle_keypress(key)
                                self.last_keypress_time = time.time()
                                break
                    
                    GPIO.output(EXTRA_ROW_PINS[row], GPIO.HIGH)
                    
                    if self.current_pressed_key:
                        break

        # Add a small delay to prevent CPU overload
        time.sleep(0.01)
		
def setup_gpio():
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)  # Disable warnings
        
        # Setup row pins as outputs
        for pin in ROW_PINS + EXTRA_ROW_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
            
        # Setup column pins as inputs with pull-up resistors
        for pin in COL_PINS + EXTRA_COL_PINS:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        GPIO.setup(SPEAKER_PIN, GPIO.OUT)
        logging.info("GPIO setup completed successfully")
    except Exception as e:
        logging.error(f"GPIO setup failed: {e}")
        raise
		
def main():
    try:
        setup_gpio()
        keyboard = KeyboardRecorder()
        logging.info("Keyboard recorder initialized and running...")
        
        while True:
            keyboard.scan_matrix()
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if hasattr(keyboard, 'pwm'):
            keyboard.pwm.stop()
        GPIO.cleanup()
        logging.info("GPIO cleanup completed")

if __name__ == "__main__":
    main()