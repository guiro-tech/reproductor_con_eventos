# gui/dnd.py
import ttkbootstrap as ttkb
from tkinterdnd2 import DND_FILES

def install_dnd_glow(root, widget_for_dnd, frame_to_glow):
    try:
        style = ttkb.Style()
        base_style = frame_to_glow.cget("style") or "TFrame"
        glow_style = "GlowPing.TFrame"
        style.configure(glow_style, background="#0d6efd")
        def ping(_=None):
            frame_to_glow.configure(style=glow_style)
            root.after(180, lambda: frame_to_glow.configure(style=base_style))
        widget_for_dnd.drop_target_register(DND_FILES)
        widget_for_dnd.dnd_bind("<<Drop>>", ping)
    except Exception:
        pass
