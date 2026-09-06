import pyautogui  # type: ignore
import time
from datetime import datetime
import pytz  # type: ignore

def wait_for_click_position(order):
    input(f"\n[+] Move your mouse to the position for screen {order} and press Enter...")
    position = pyautogui.position()
    print(f"[✓] Position for screen {order} recorded at {position}")
    return position

def auto_click():
    cairo_tz = pytz.timezone("Africa/Cairo")

    pos1 = wait_for_click_position("1 (First Screen)")
    time.sleep(0.5)
    pos2 = wait_for_click_position("2 (Second Screen)")
    time.sleep(0.5)

    click_count = 0
    last_main_click_minute = -1
    last_clicked_position = None
    ready_for_extra_click = False  # الشرط الجديد

    try:
        print("\n[▶] Auto Clicker started. Press Ctrl-C to quit.\n")
        while True:
            current_time = datetime.now(cairo_tz)
            minute = current_time.minute
            second = current_time.second

            # كليك أساسي عند الثانية 59
            if second == 58 and last_main_click_minute != minute:
                if minute % 2 == 1:
                    pyautogui.click(pos1)
                    last_clicked_position = pos1
                    screen = "Screen 1"
                else:
                    pyautogui.click(pos2)
                    last_clicked_position = pos2
                    screen = "Screen 2"

                click_count += 1
                last_main_click_minute = minute
                ready_for_extra_click = False  # يسمح بالضغط عند 30s فقط لو حصل كليك أساسي
                print(f"✅ #{click_count:03} | Clicked on 🖥 {screen} at {last_clicked_position} | 🕒 {current_time.strftime('%H:%M:%S')}")
                print("-" * 60)
                time.sleep(1.1)

            # كليك إضافي عند الثانية 30 **فقط إذا حصل كليك أساسي قبلها**
            elif second == 30 and ready_for_extra_click:
                pyautogui.click(last_clicked_position)
                print(f"🕧       | (30s) Extra Click on same screen at {last_clicked_position} | 🕒 {current_time.strftime('%H:%M:%S')}")
                print("-" * 60)
                ready_for_extra_click = False  # خلصنا الكليك الإضافي، نمنعه لحد ما يحصل كليك أساسي جديد
                time.sleep(1.1)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n[⏹] Auto Clicker stopped. Total counted clicks: {click_count}")

if __name__ == "__main__":
    auto_click()
