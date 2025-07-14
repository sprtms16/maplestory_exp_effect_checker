
import pygetwindow as gw
import mss
import mss.tools

def capture_maplestory_chat():
    try:
        maple_window = gw.getWindowsWithTitle('MapleStory')[0]
        if maple_window:
            with mss.mss() as sct:
                # Adjust these values to capture the chat area
                monitor = {"top": maple_window.top + 300, "left": maple_window.left + 10, "width": 500, "height": 100}
                output = "maple_chat.png"
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
                print(f"Screenshot saved to {output}")
        else:
            print("MapleStory window not found.")
    except IndexError:
        print("MapleStory window not found.")

if __name__ == "__main__":
    capture_maplestory_chat()
