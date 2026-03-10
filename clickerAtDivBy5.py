import pyautogui  # type: ignore
import time
from datetime import datetime, timedelta
import pytz  # type: ignore
import winsound


# ───────────────────────────────────────────────
# Display a banner showing when the next click will happen
# ───────────────────────────────────────────────
def print_next_click_banner(next_click_time):
    print(r"""
      ╔════════ CLOCK ════════╗
      ║        🕒              ║
      ║   • Scheduled Click •  ║
      ╚════════════════════════╝
    """)
    print(f"🖱️ NEXT CLICK → {next_click_time.strftime('%H:%M:%S')}")
    print("-" * 35)


# ───────────────────────────────────────────────
# Main Auto Clicker Logic
# ───────────────────────────────────────────────
def auto_click():

    cairo_tz = pytz.timezone("Africa/Cairo")

    click_second = int(input("♦️ Enter the second to click (0-59): "))

    total_click_count = 0
    hourly_click_count = 0

    last_recorded_hour = datetime.now(cairo_tz).hour
    last_click_time = None


    # ───────────────────────────────────────────────
    # Calculate next click time
    # ───────────────────────────────────────────────
    def schedule_next_click(now):

        minute = now.minute
        hour = now.hour

        divisible_minute = minute + (5 - minute % 5)

        if divisible_minute == 60:
            divisible_minute = 0
            hour = (hour + 1) % 24

        # لو الثانية = 0 → اضغط عند الدقيقة نفسها
        if click_second == 0:
            click_minute = divisible_minute

        # باقي الثواني → قبل الدقيقة بدقيقة (السلوك القديم)
        else:
            click_minute = (divisible_minute - 1) % 60

            if click_minute == 59:
                hour = (hour + 1) % 24

        next_click = now.replace(
            hour=hour,
            minute=click_minute,
            second=click_second,
            microsecond=0
        )

        if next_click <= now:
            next_click += timedelta(minutes=5)

        print_next_click_banner(next_click)

        return next_click


    next_click_at = schedule_next_click(datetime.now(cairo_tz))

    try:

        print(f"Auto Clicker started. Clicking at second {click_second:02d}.")

        while True:

            current_time = datetime.now(cairo_tz)
            current_hour = current_time.hour

            # Reset hourly counter
            if current_hour != last_recorded_hour:
                print(
                    f"Hour changed {last_recorded_hour:02d}:00 → {current_hour:02d}:00 | "
                    f"Clicks last hour: {hourly_click_count}"
                )
                last_recorded_hour = current_hour
                hourly_click_count = 0


            # ───────────────────────────────────────────────
            # MAIN CLICK
            # ───────────────────────────────────────────────
            if current_time >= next_click_at:

                x, y = pyautogui.position()
                pyautogui.click(x, y)

                winsound.Beep(1000, 500)

                total_click_count += 1
                hourly_click_count += 1
                last_click_time = current_time

                print(
                    f"[Main] Click #{total_click_count} "
                    f"(Hour {current_hour:02d}:{hourly_click_count}) "
                    f"{current_time.strftime('%H:%M:%S')}"
                )

                next_click_at = schedule_next_click(current_time)

                time.sleep(1.2)


            # ───────────────────────────────────────────────
            # EXTRA CLICK exactly 2.5 minutes after main click
            # ───────────────────────────────────────────────
            if last_click_time:

                if (current_time - last_click_time).seconds >= 150:

                    x, y = pyautogui.position()
                    pyautogui.click(x, y)

                    total_click_count += 1
                    hourly_click_count += 1

                    print(
                        f"[Extra] Second Click #{total_click_count} "
                        f"(Hour {current_hour:02d}:{hourly_click_count}) "
                        f"{current_time.strftime('%H:%M:%S')} (2.5 min later)"
                    )

                    last_click_time = None

                    time.sleep(1.2)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print(f"Stopped. Total clicks: {total_click_count}")


if __name__ == "__main__":
    auto_click()