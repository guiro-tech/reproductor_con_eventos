# gui/botones.py
import ttkbootstrap as ttkb

def crear_controles(root, *,
                    row=2, column=0, colspan=2,
                    padx=10, pady=10,
                    uniform="ctrls"):
    frame = ttkb.Frame(root)
    frame.grid(row=row, column=column, columnspan=colspan,
               sticky="ew", padx=padx, pady=pady)
    frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform=uniform)

    btn_play  = ttkb.Button(frame, text="▶️ Play",  bootstyle="primary")   # <- sin round
    btn_stop  = ttkb.Button(frame, text="⏹️ Stop",  bootstyle="danger")
    btn_pause = ttkb.Button(frame, text="⏸️ Pause", bootstyle="info")
    btn_next  = ttkb.Button(frame, text="⏭️ Next",  bootstyle="warning")

    btn_play.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    btn_stop.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    btn_pause.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    btn_next.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    return frame, {
        "play":  btn_play,
        "stop":  btn_stop,
        "pause": btn_pause,
        "next":  btn_next
    }
