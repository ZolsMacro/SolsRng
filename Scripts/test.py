import win32gui
import win32con
import time

def high_frequency_heartbeat():
    window_title = "Roblox"
    hwnd = win32gui.FindWindow(None, window_title)

    if not hwnd:
        print("Error: Roblox not found.")
        return

    print("--- 1-Second Heartbeat Active ---")
    print("Looping every 1 second. No movement or keys.")
    print("Reminder: DO NOT MINIMIZE the window.")

    try:
        while True:
            # Send a NULL message (General Heartbeat)
            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
            
            # Send a PAINT message (Tells the engine to stay awake)
            win32gui.PostMessage(hwnd, win32con.WM_PAINT, 0, 0)
            
            # Send an ACTIVATE message (Tells the engine it has focus)
            win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)

            # 1 second delay
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nLoop stopped.")

if __name__ == "__main__":
    high_frequency_heartbeat()