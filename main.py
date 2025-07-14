
import pygetwindow as gw
import mss
import mss.tools
import easyocr
import requests
import time

# Initialize EasyOCR reader
reader = easyocr.Reader(['ko', 'en'])

# Discord Webhook URL - Replace with your actual webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your/webhook/url"

def send_discord_message(message):
    """Sends a message to the configured Discord webhook."""
    if DISCORD_WEBHOOK_URL == "https://discord.com/api/webhooks/your/webhook/url":
        print("Please configure your Discord webhook URL in the script.")
        return
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Message sent to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

def process_chat_image(image_path):
    """Extracts text from an image and checks for keywords."""
    try:
        results = reader.readtext(image_path)
        detected_text = " ".join([result[1] for result in results])
        print(f"Detected Text: {detected_text}")

        # Keywords to look for
        keywords = ["경뿌", "우르스"]
        
        for keyword in keywords:
            if keyword in detected_text:
                message = f"키워드 '{keyword}' 감지! 내용: {detected_text}"
                send_discord_message(message)
                break # Send only one message per capture
    except Exception as e:
        print(f"Error processing image with OCR: {e}")


def capture_maplestory_chat():
    """Captures the MapleStory chat window and processes it."""
    try:
        maple_window = gw.getWindowsWithTitle('MapleStory')[0]
        if not maple_window:
            print("MapleStory window not found.")
            return

        with mss.mss() as sct:
            # Adjust these values to capture the chat area
            monitor = {"top": maple_window.top + 300, "left": maple_window.left + 10, "width": 500, "height": 100}
            output = "maple_chat.png"
            
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
            print(f"Screenshot saved to {output}")
            
            process_chat_image(output)

    except IndexError:
        print("MapleStory window not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Example of running it once
    # In the final version, this will be in a loop.
    capture_maplestory_chat()
