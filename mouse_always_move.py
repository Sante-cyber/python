import pyautogui
import time

# Disable the PyAutoGUI fail-safe (use with caution!)
pyautogui.FAILSAFE = False

delay = 0.5

def move_mouse_continuously():
    while True:
        try:
            # Get the current mouse position
            x, y = pyautogui.position()

            # Move the mouse to a new position (adjust as needed)
            pyautogui.moveTo(x + 100, y + 100, duration=0.25)  # Move diagonally
            time.sleep(delay)
            pyautogui.moveTo(x - 100, y - 100, duration=0.25)  # Move back
            time.sleep(delay)

        except Exception as e:
            print(f"Error encountered: {e}")
            # Wait for a bit before retrying to avoid continuous errors
            time.sleep(1)

if __name__ == "__main__":
    move_mouse_continuously()  # Keeps running indefinitely
