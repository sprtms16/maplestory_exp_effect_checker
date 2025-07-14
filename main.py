
import pygetwindow as gw
import mss
import mss.tools
import easyocr
import requests
import time
import configparser
import os
import cv2
import numpy as np

# --- Configuration ---
def load_config():
    """Loads configuration from config.ini."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    if not os.path.exists(config_path):
        raise FileNotFoundError("config.ini not found. Please create it.")
    config.read(config_path, encoding='utf-8')
    return config['DEFAULT']

# --- Globals ---
try:
    config = load_config()
    DISCORD_WEBHOOK_URL = config.get('DiscordWebhookUrl')
    KEYWORDS = [k.strip() for k in config.get('Keywords', '경뿌,우르스').split(',')]
    CAPTURE_INTERVAL = config.getint('CaptureIntervalSeconds', 3)
    # OCR settings
    OCR_PREPROCESS = config.getboolean('OcrPreprocessing', True)
    # Capture coordinates
    CAPTURE_TOP = config.getint('CaptureTop', 300)
    CAPTURE_LEFT = config.getint('CaptureLeft', 10)
    CAPTURE_WIDTH = config.getint('CaptureWidth', 500)
    CAPTURE_HEIGHT = config.getint('CaptureHeight', 100)

    reader = easyocr.Reader(['ko', 'en'])
except (FileNotFoundError, configparser.Error, ValueError) as e:
    print(f"Error loading configuration: {e}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during initialization: {e}")
    exit()

# --- Core Functions ---
def send_discord_message(message):
    """Sends a message to the configured Discord webhook."""
    if not DISCORD_WEBHOOK_URL or 'your/webhook/url' in DISCORD_WEBHOOK_URL:
        print("WARNING: Discord webhook URL is not configured in config.ini.")
        return
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        print(f"Discord notification sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not send message to Discord: {e}")

def preprocess_image_for_ocr(image_np):
    """Applies preprocessing to the image to improve OCR accuracy."""
    # Convert to grayscale
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGRA2GRAY)
    # Apply a binary threshold to get a black and white image
    # This threshold value might need adjustment for different chat settings
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    return thresh

def process_chat_image(image_np):
    """Extracts text from an image and checks for keywords."""
    try:
        if OCR_PREPROCESS:
            processed_image = preprocess_image_for_ocr(image_np)
        else:
            processed_image = image_np

        results = reader.readtext(processed_image)
        if not results:
            return

        detected_text = " ".join([result[1] for result in results])
        print(f"Detected Text: {detected_text}")

        for keyword in KEYWORDS:
            if keyword in detected_text:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                message = f"[{timestamp}] Keyword '{keyword}' detected!\n> {detected_text}"
                send_discord_message(message)
                break
    except Exception as e:
        print(f"ERROR: Failed to process image with OCR: {e}")

def capture_and_process(sct):
    """Captures the MapleStory chat window and triggers processing."""
    try:
        maple_windows = gw.getWindowsWithTitle('MapleStory')
        if not maple_windows:
            print("MapleStory window not found. Waiting...")
            return

        maple_window = maple_windows[0]
        if maple_window.isMinimized:
            print("MapleStory window is minimized. Skipping capture.")
            return

        monitor = {
            "top": maple_window.top + CAPTURE_TOP,
            "left": maple_window.left + CAPTURE_LEFT,
            "width": CAPTURE_WIDTH,
            "height": CAPTURE_HEIGHT
        }
        
        sct_img = sct.grab(monitor)
        # Convert to numpy array for OpenCV processing
        img_np = np.array(sct_img)
        
        process_chat_image(img_np)

    except IndexError:
        print("MapleStory window not found. It might have been closed.")
    except Exception as e:
        print(f"ERROR: An error occurred during screen capture: {e}")

# --- Main Loop ---
def main():
    """Main loop to periodically capture and process the chat."""
    print("Starting MapleStory Discord Alerter.")
    print(f"Keywords: {KEYWORDS}")
    print(f"Capture Interval: {CAPTURE_INTERVAL} seconds")
    
    # Create mss instance once
    with mss.mss() as sct:
        while True:
            try:
                capture_and_process(sct)
                time.sleep(CAPTURE_INTERVAL)
            except KeyboardInterrupt:
                print("\nStopping the alerter. Goodbye!")
                break
            except Exception as e:
                print(f"FATAL: An unexpected error occurred in the main loop: {e}")
                print("Restarting in 10 seconds...")
                time.sleep(10)

if __name__ == "__main__":
    main()
