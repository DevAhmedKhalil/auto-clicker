import queue as _queue
import threading
import time
import tkinter as tk
import winsound
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import pyautogui

PRIMARY = "#2563eb"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
BG = "#f1f5f9"
CARD = "#ffffff"
BORDER = "#cbd5e1"
TEXT = "#0f172a"
MUTED = "#64748b"
ERROR = "#b91c1c"


class ClickerEngine:
    """All auto-click logic runs in a background thread so the GUI stays responsive."""

    def __init__(self, log_cb):
        self._stop = threading.Event()
        self._thread = None
        self._log_cb = log_cb

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, mode, cfg):
        if self.is_running():
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(mode, cfg), daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

    def _sleep(self, secs):
        end = time.monotonic() + secs
        while time.monotonic() < end:
            if self._stop.is_set():
                return False
            time.sleep(0.05)
        return True

    def _log(self, msg):
        self._log_cb(msg)

    def _run(self, mode, cfg):
        try:
            if mode == 1:
                self._mode_seconds(cfg)
            elif mode == 2:
                self._mode_every5(cfg)
            else:
                self._mode_two_screens(cfg)
        except Exception as exc:
            self._log(f"[ERROR] {exc}")
        finally:
            self._log("Engine stopped.")


    # ---------- Mode 1: click at specific seconds every minute ----------
    def _mode_seconds(self, cfg):
        seconds = sorted(set(cfg["seconds"]))
        total = hourly = 0
        last_hour = datetime.now().hour
        self._log(f"Mode 1 started | will click at second(s): {seconds}")
        while not self._stop.is_set():
            now = datetime.now()
            h = now.hour
            if h != last_hour:
                self._log(f"Hour changed {last_hour:02d} -> {h:02d} | clicks last hour: {hourly}")
                last_hour = h
                hourly = 0
            if now.second in seconds:
                x, y = pyautogui.position()
                pyautogui.click(x, y)
                total += 1
                hourly += 1
                self._log(f"Mouse #{total} clicked at ({x},{y}) | {now.strftime('%H:%M:%S')} | h:{hourly}")
                if not self._sleep(1.1):
                    break
            time.sleep(0.05)


    # ---------- Mode 2: click every 5 min (+1 extra after 2.5 min) ----------
    def _schedule_next_click(self, now, click_second):
        minute = now.minute
        hour = now.hour
        divisible_minute = minute + (5 - minute % 5)
        if divisible_minute == 60:
            divisible_minute = 0
            hour = (hour + 1) % 24
        if click_second == 0:
            click_minute = divisible_minute
        else:
            click_minute = (divisible_minute - 1) % 60
            if click_minute == 59:
                hour = (hour + 1) % 24
        nxt = now.replace(hour=hour, minute=click_minute, second=click_second, microsecond=0)
        if nxt <= now:
            nxt += timedelta(minutes=5)
        self._log(f"Next click -> {nxt.strftime('%H:%M:%S')}")
        return nxt

    def _mode_every5(self, cfg):
        click_second = cfg["click_second"]
        total = hourly = 0
        last_hour = datetime.now().hour
        last_click_time = None
        next_click_at = self._schedule_next_click(datetime.now(), click_second)
        self._log(f"Mode 2 started | click at second {click_second:02d} every 5 min + extra after 2.5 min")
        while not self._stop.is_set():
            now = datetime.now()
            h = now.hour
            if h != last_hour:
                self._log(f"Hour changed {last_hour:02d} -> {h:02d} | clicks last hour: {hourly}")
                last_hour = h
                hourly = 0

            if now >= next_click_at:
                x, y = pyautogui.position()
                pyautogui.click(x, y)
                winsound.Beep(1000, 300)
                total += 1
                hourly += 1
                last_click_time = now
                self._log(f"[Main] #{total} clicked at ({x},{y}) | {now.strftime('%H:%M:%S')}")
                next_click_at = self._schedule_next_click(now, click_second)
                if not self._sleep(1.2):
                    break

            if last_click_time is not None and (now - last_click_time).seconds >= 150:
                x, y = pyautogui.position()
                pyautogui.click(x, y)
                total += 1
                hourly += 1
                self._log(f"[Extra] #{total} clicked at ({x},{y}) | {now.strftime('%H:%M:%S')} (2.5 min later)")
                last_click_time = None
                if not self._sleep(1.2):
                    break

            time.sleep(0.05)


    # ---------- Mode 3: alternate two screens, one click per minute ----------
    def _mode_two_screens(self, cfg):
        pos1, pos2 = cfg["pos1"], cfg["pos2"]
        click_second = cfg["second"]
        total = 0
        last_click_minute = -1
        self._log(f"Mode 3 started | screen 1 = {pos1} | screen 2 = {pos2} | second: {click_second:02d}")
        while not self._stop.is_set():
            now = datetime.now()
            minute = now.minute
            second = now.second

            if second == click_second and last_click_minute != minute:
                is_odd = minute % 2 == 1
                pos = pos1 if is_odd else pos2
                pyautogui.click(pos)
                total += 1
                last_click_minute = minute
                self._log(f"Screen {'1' if is_odd else '2'} clicked #{total} at {pos} | {now.strftime('%H:%M:%S')}")
                if not self._sleep(1.1):
                    break

            time.sleep(0.05)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _e=None):
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{self.widget.winfo_rootx() + 20}+{self.widget.winfo_rooty() + self.widget.winfo_height() + 5}")
        label = tk.Label(self.tip, text=self.text, justify="left", bg="#1e293b", fg="white",
                         font=("Segoe UI", 9), padx=8, pady=5, wraplength=320)
        label.pack()

    def _hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def _build_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)

    style.configure("Card.TLabelframe", background=CARD, bordercolor=BORDER, relief="solid")
    style.configure("Card.TLabelframe.Label", background=CARD, foreground=PRIMARY,
                    font=("Segoe UI", 11, "bold"))

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Hint.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 8))
    style.configure("Err.TLabel", background=CARD, foreground=ERROR, font=("Segoe UI", 9, "bold"))
    style.configure("Status.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))

    style.configure("TRadiobutton", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
    style.map("TRadiobutton", background=[("active", CARD)],
              foreground=[("active", PRIMARY), ("disabled", "#9ca3af")])

    style.configure("TEntry", fieldbackground="white", bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, focuscolor=PRIMARY)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])

    style.configure("Accent.TButton", background=SUCCESS, foreground="white",
                    font=("Segoe UI", 11, "bold"), borderwidth=0, focusthickness=0, padding=(18, 8))
    style.map("Accent.TButton", background=[("active", "#128a35"), ("disabled", "#a7d9b5")])

    style.configure("Danger.TButton", background=DANGER, foreground="white",
                    font=("Segoe UI", 11, "bold"), borderwidth=0, focusthickness=0, padding=(18, 8))
    style.map("Danger.TButton", background=[("active", "#b02020"), ("disabled", "#e8a5a3")])

    style.configure("Ghost.TButton", background=CARD, foreground=PRIMARY,
                    font=("Segoe UI", 10, "bold"), borderwidth=1, bordercolor=PRIMARY, padding=(10, 6))
    style.map("Ghost.TButton", background=[("active", "#e0e7ff"), ("disabled", "#f1f5f9")],
              foreground=[("disabled", "#9ca3af")])


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        root.title("Auto Clicker")
        root.configure(bg=BG)
        _build_styles()

        self.engine = ClickerEngine(self.log)
        self.msg_q = _queue.Queue()
        self.pos1 = None
        self.pos2 = None
        self._running_flag = False
        self._err_job = None

        self._build_ui()
        self._center_window(640, 640)
        root.after(100, self._poll_queue)
        root.after(250, self._tick_clock)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, w, h):
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 3
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(560, 540)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PRIMARY, height=54)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Auto Clicker", bg=PRIMARY, fg="white",
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=16, pady=10)
        self.clock_lbl = tk.Label(header, text="--:--:--", bg=PRIMARY, fg="#dbeafe",
                                  font=("Consolas", 12, "bold"))
        self.clock_lbl.pack(side="right", padx=16)

        self.mode_card = ttk.LabelFrame(self.root, text="  Select Mode  ", style="Card.TLabelframe", padding=12)
        self.mode_card.pack(fill="x", padx=14, pady=(12, 6))
        self.mode_var = tk.StringVar(value="1")
        mode_opts = [
            ("1", "Mode 1  -  Click at specific seconds (every minute)"),
            ("2", "Mode 2  -  Click every 5 min + extra click after 2.5 min"),
            ("3", "Mode 3  -  Alternate between two screens (odd/even minute)"),
        ]
        for value, label in mode_opts:
            ttk.Radiobutton(self.mode_card, text=label, variable=self.mode_var, value=value,
                            command=self._switch_mode).pack(anchor="w", pady=3)

        self.settings_frame = ttk.LabelFrame(self.root, text="  Settings  ", style="Card.TLabelframe", padding=12)
        self.settings_frame.pack(fill="x", padx=14, pady=6)

        self.m1 = ttk.Frame(self.settings_frame, style="Card.TFrame")
        self.m1_row = ttk.Frame(self.m1, style="Card.TFrame")
        self.m1_row.pack(anchor="w", pady=4)
        ttk.Label(self.m1_row, text="Seconds to click (comma separated):", style="Card.TLabel").pack(side="left")
        self.m1_entry = ttk.Entry(self.m1_row, width=12)
        self.m1_entry.insert(0, "0,30")
        self.m1_entry.pack(side="left", padx=(8, 0))
        ttk.Label(self.m1, text="Clicks at the current mouse position whenever the seconds match.",
                  style="Hint.TLabel", wraplength=520).pack(anchor="w")
        ToolTip(self.m1_entry, "Example: 0,30 clicks at :00 and :30 of every minute.")

        self.m2 = ttk.Frame(self.settings_frame, style="Card.TFrame")
        self.m2_row = ttk.Frame(self.m2, style="Card.TFrame")
        self.m2_row.pack(anchor="w", pady=4)
        ttk.Label(self.m2_row, text="Click second (0-59):", style="Card.TLabel").pack(side="left")
        self.m2_entry = ttk.Entry(self.m2_row, width=6)
        self.m2_entry.insert(0, "30")
        self.m2_entry.pack(side="left", padx=(8, 0))
        ttk.Label(self.m2, text="Main click at the next minute divisible by 5, plus an extra click 2.5 min later.",
                  style="Hint.TLabel", wraplength=520).pack(anchor="w")
        ToolTip(self.m2_entry, "Main click lands one minute before each 5-minute mark, at this second.")

        self.m3 = ttk.Frame(self.settings_frame, style="Card.TFrame")
        self.m3_row = ttk.Frame(self.m3, style="Card.TFrame")
        self.m3_row.pack(anchor="w", pady=4)
        ttk.Label(self.m3_row, text="Click second (0-59):", style="Card.TLabel").pack(side="left")
        self.m3_second_entry = ttk.Entry(self.m3_row, width=6)
        self.m3_second_entry.insert(0, "58")
        self.m3_second_entry.pack(side="left", padx=(8, 0))
        ttk.Label(self.m3_row, text="   |   ", style="Card.TLabel").pack(side="left")
        self.rec1_btn = ttk.Button(self.m3_row, text="Record Position 1", style="Ghost.TButton",
                                   command=lambda: self._record_pos(1))
        self.rec1_btn.pack(side="left")
        self.pos1_lbl = ttk.Label(self.m3_row, text="Not recorded", style="Card.TLabel", foreground=DANGER)
        self.pos1_lbl.pack(side="left", padx=6)
        ttk.Label(self.m3_row, text="   |   ", style="Card.TLabel").pack(side="left")
        self.rec2_btn = ttk.Button(self.m3_row, text="Record Position 2", style="Ghost.TButton",
                                   command=lambda: self._record_pos(2))
        self.rec2_btn.pack(side="left")
        self.pos2_lbl = ttk.Label(self.m3_row, text="Not recorded", style="Card.TLabel", foreground=DANGER)
        self.pos2_lbl.pack(side="left", padx=6)
        ttk.Label(self.m3, text="Screen 1 is clicked on odd minutes, screen 2 on even minutes, at the chosen second.",
                  style="Hint.TLabel", wraplength=520).pack(anchor="w")
        ToolTip(self.rec1_btn, "Move the mouse to screen 1, then click. Position is captured after a 5s countdown.")
        ToolTip(self.rec2_btn, "Move the mouse to screen 2, then click. Position is captured after a 5s countdown.")

        self.err_lbl = ttk.Label(self.settings_frame, text="", style="Err.TLabel")
        self._switch_mode()

        ctrl = tk.Frame(self.root, bg=BG)
        ctrl.pack(fill="x", padx=14, pady=12)
        btn_container = tk.Frame(ctrl, bg=BG)
        btn_container.pack()
        self.start_btn = ttk.Button(btn_container, text="\u25B6  Start", style="Accent.TButton", command=self._start)
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = ttk.Button(btn_container, text="\u23F9  Stop", style="Danger.TButton", command=self._stop)
        self.stop_btn.pack(side="left")
        ToolTip(self.start_btn, "Start the auto clicker with the current settings.")
        ToolTip(self.stop_btn, "Stop the auto clicker immediately.")

        self.status_bar = tk.Frame(self.root, bg=BG)
        self.status_bar.pack(fill="x", padx=14)
        self.status_dot = tk.Canvas(self.status_bar, width=12, height=12, bg=BG, highlightthickness=0, bd=0)
        self.dot = self.status_dot.create_oval(2, 2, 9, 9)
        self.status_dot.pack(side="left")
        self.status_lbl = ttk.Label(self.status_bar, text="Idle", style="Status.TLabel")
        self.status_lbl.pack(side="left", padx=(6, 0))
        self._set_status("Idle", "#9ca3af")

        log_card = tk.Frame(self.root, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        log_card.pack(fill="both", expand=True, padx=14, pady=(6, 14))
        log_header = tk.Frame(log_card, bg=CARD)
        log_header.pack(fill="x")
        tk.Label(log_header, text="    Activity Log  ", bg=CARD, fg=PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(side="left", pady=4)
        self.clear_btn = ttk.Button(log_header, text="\U0001F5D1", style="Ghost.TButton",
                                    width=3, command=self._clear_log)
        self.clear_btn.pack(side="right", padx=4, pady=2)
        ToolTip(self.clear_btn, "Clear the activity log.")

        self.log_text = tk.Text(log_card, height=11, font=("Consolas", 9), bg="#f8fafc",
                                fg=TEXT, relief="flat", bd=0, padx=6, pady=6, insertbackground=TEXT)
        sb = tk.Scrollbar(log_card, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    def _switch_mode(self):
        mode = int(self.mode_var.get())
        for f in (self.m1, self.m2, self.m3):
            f.pack_forget()
        self.err_lbl.pack_forget()
        if mode == 1:
            self.m1.pack(anchor="w")
        elif mode == 2:
            self.m2.pack(anchor="w")
        else:
            self.m3.pack(anchor="w")

    def _show_error(self, msg):
        self.err_lbl.config(text=f"\u26A0  {msg}")
        self.err_lbl.pack(anchor="w", pady=(8, 0))
        if self._err_job:
            self.root.after_cancel(self._err_job)
        self._err_job = self.root.after(6000, lambda: self.err_lbl.pack_forget())

    def _record_pos(self, n):
        btn = self.rec1_btn if n == 1 else self.rec2_btn
        btn.config(state="disabled")

        def countdown(secs):
            if secs > 0:
                btn.config(text=f"Move the mouse to the position... {secs}")
                self.root.after(1000, lambda: countdown(secs - 1))
            else:
                x, y = pyautogui.position()
                if n == 1:
                    self.pos1 = (x, y)
                    self.pos1_lbl.config(text=f"{x},{y}", foreground=SUCCESS)
                else:
                    self.pos2 = (x, y)
                    self.pos2_lbl.config(text=f"{x},{y}", foreground=SUCCESS)
                btn.config(state="normal", text=f"Re-record Position {n}")
                self.log(f"Position {n} recorded at ({x},{y})")

        btn.config(text="Move the mouse now (5s)...")
        countdown(5)

    def _set_status(self, text, color):
        self.status_lbl.config(text=text, foreground=color)
        self.status_dot.itemconfig(self.dot, fill=color, outline=color)

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(250, self._tick_clock)

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _parse_int(self, raw, field_name, low, high):
        raw = raw.strip()
        if raw == "":
            raise ValueError(f"{field_name} is required.")
        try:
            v = int(raw)
        except ValueError:
            raise ValueError(f"{field_name} must be a whole number.")
        if not (low <= v <= high):
            raise ValueError(f"{field_name} must be between {low} and {high}.")
        return v

    def _start(self):
        if self.engine.is_running():
            return
        mode = int(self.mode_var.get())
        cfg = {}
        try:
            if mode == 1:
                parts = [s.strip() for s in self.m1_entry.get().split(",")]
                vals = []
                for p in parts:
                    if p == "":
                        continue
                    if not p.lstrip("-").isdigit():
                        raise ValueError(f"'{p}' is not a valid number.")
                    vals.append(int(p))
                if not vals:
                    raise ValueError("Enter at least one second.")
                for v in vals:
                    if not (0 <= v <= 59):
                        raise ValueError("Seconds must be between 0 and 59.")
                seconds = sorted(set(vals))
                cfg["seconds"] = seconds
            elif mode == 2:
                cfg["click_second"] = self._parse_int(self.m2_entry.get(), "Click second", 0, 59)
            else:
                if self.pos1 is None or self.pos2 is None:
                    raise ValueError("Record both screen positions first.")
                cfg["second"] = self._parse_int(self.m3_second_entry.get(), "Click second", 0, 59)
                cfg["pos1"], cfg["pos2"] = self.pos1, self.pos2
        except ValueError as e:
            self._show_error(str(e))
            messagebox.showerror("Invalid Settings", str(e))
            return

        self.log("=" * 45)
        self.engine.start(mode, cfg)
        self._running_flag = True
        self._set_status("Running", SUCCESS)
        mode_names = {1: "Seconds", 2: "Every 5 min", 3: "Two screens"}
        self.log(f"Started: Mode {mode} ({mode_names[mode]})")
        self._set_controls_enabled(False)

    def _stop(self):
        was_running = self.engine.is_running()
        self.engine.stop()
        self._running_flag = False
        self._set_status("Idle", "#9ca3af")
        self._set_controls_enabled(True)
        if was_running:
            self.log("Stopped by user.")

    def _set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.mode_card.winfo_children():
            child.config(state=state)
        for w in (self.m1_entry, self.m2_entry, self.m3_second_entry):
            w.config(state=state)
        if self.pos1 is not None:
            self.rec1_btn.config(state=state)
        else:
            self.rec1_btn.config(state="normal" if enabled else "disabled")
        if self.pos2 is not None:
            self.rec2_btn.config(state=state)
        else:
            self.rec2_btn.config(state="normal" if enabled else "disabled")
        self.start_btn.config(state="disabled" if not enabled else "normal")

    def log(self, msg):
        self.msg_q.put(msg)

    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_q.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except _queue.Empty:
            pass

        if self._running_flag and not self.engine.is_running():
            self._running_flag = False
            self._set_status("Idle", "#9ca3af")
            self._set_controls_enabled(True)

        self.root.after(100, self._poll_queue)

    def _on_close(self):
        self.engine.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()