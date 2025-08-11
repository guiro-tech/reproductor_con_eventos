# gui/animations.py
import tkinter as tk
import ttkbootstrap as ttkb

def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

def _ease_out_back(t: float, s: float = 1.70158) -> float:
    t -= 1
    return (t) * t * ((s + 1) * t + s) + 1

def _run_animation(root, steps, interval_ms, updater):
    i = 0
    def tick():
        nonlocal i
        if i <= steps:
            t = i / float(steps)
            updater(t)
            i += 1
            root.after(interval_ms, tick)
    tick()

def fade_in_window(root, duration_ms=450, steps=20):
    try:
        root.attributes('-alpha', 0.0)
    except Exception:
        return
    _run_animation(root, steps, duration_ms // steps,
                   lambda t: root.attributes('-alpha', _ease_out_cubic(t)))

def slide_pad_in(root, widget, from_pad=40, to_pad=10, duration_ms=380, steps=18):
    widget.configure(padding=(10, from_pad, 10, 10))
    def upd(t):
        y = int(from_pad + (to_pad - from_pad) * _ease_out_back(t))
        widget.configure(padding=(10, y, 10, 10))
    _run_animation(root, steps, duration_ms // steps, upd)

def bind_hover_lift(root, btn, grow_px=4, duration_ms=120, steps=8):
    try:
        orig_bs = btn.cget("bootstyle") or ""
    except tk.TclError:
        return
    target_bs = orig_bs if orig_bs.endswith("-outline") else (orig_bs + "-outline" if orig_bs else "outline")
    base_pad = (10, 6)
    big_pad  = (base_pad[0] + grow_px, base_pad[1] + grow_px)
    def animate_pad(to_big: bool):
        start = big_pad if not to_big else base_pad
        end   = big_pad if to_big else base_pad
        def upd(t):
            tt = _ease_out_cubic(t)
            x = int(start[0] + (end[0] - start[0]) * tt)
            y = int(start[1] + (end[1] - start[1]) * tt)
            btn.configure(padding=(x, y))
        _run_animation(root, steps, max(1, duration_ms // steps), upd)
    def on_enter(_):
        try: btn.configure(bootstyle=target_bs)
        except tk.TclError: pass
        animate_pad(True)
    def on_leave(_):
        try: btn.configure(bootstyle=orig_bs)
        except tk.TclError: pass
        animate_pad(False)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
