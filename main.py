
import pygetwindow as gw
import mss
import mss.tools
import easyocr
import requests
import time
import configparser
import os

# --- Configuration ---
def load_config():
    """Loads configuration from config.ini."""
    config = configparser.ConfigParser()
    # Use absolute path for config file to avoid issues with working directory
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
    reader = easyocr.Reader(['ko', 'en'])
except (FileNotFoundError, configparser.Error) as e:
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
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Discord notification sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not send message to Discord: {e}")

def process_chat_image(image_path):
    """Extracts text from an image and checks for keywords."""
    try:
        results = reader.readtext(image_path)
        if not results:
            return

        detected_text = " ".join([result[1] for result in results])
        print(f"Detected Text: {detected_text}")

        for keyword in KEYWORDS:
            if keyword in detected_text:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                message = f"[{timestamp}] Keyword '{keyword}' detected!\n> {detected_text}"
                send_discord_message(message)
                break  # Send only one message per capture
    except Exception as e:
        print(f"ERROR: Failed to process image with OCR: {e}")

def capture_and_process():
    """Captures the MapleStory chat window and triggers processing."""
    try:
        maple_windows = gw.getWindowsWithTitle('MapleStory')
        if not maple_windows:
            print("MapleStory window not found. Waiting...")
            return

        maple_window = maple_windows[0]
        # Simple check if the window is minimized
        if maple_window.isMinimized:
            print("MapleStory window is minimized. Skipping capture.")
            return

        with mss.mss() as sct:
            # These coordinates might need tweaking depending on the game's resolution and UI scale.
            # It's better to make these configurable in config.ini in the future.
            monitor = {
                "top": maple_window.top + 300,
                "left": maple_window.left + 10,
                "width": 500,
                "height": 100
            }
            output_filename = "maple_chat_capture.png"
            
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_filename)
            
            process_chat_image(output_filename)

    except IndexError:
        # This can happen if the window closes between getWindowsWithTitle and accessing the list.
        print("MapleStory window not found. It might have been closed.")
    except Exception as e:
        # Catching other potential errors from pygetwindow or mss
        print(f"ERROR: An error occurred during screen capture: {e}")


# --- Main Loop ---
def main():
    """Main loop to periodically capture and process the chat."""
    print("Starting MapleStory Discord Alerter.")
    print(f"Keywords: {KEYWORDS}")
    print(f"Capture Interval: {CAPTURE_INTERVAL} seconds")
    
    while True:
        try:
            capture_and_process()
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
