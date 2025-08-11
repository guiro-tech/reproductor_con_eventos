# gui/barra_de_progreso.py
import tkinter as tk
import ttkbootstrap as ttkb

def crear_barra_progreso(parent, *,
                         orient="horizontal",
                         length=200,
                         mode="determinate",
                         maximum=100):
    """
    Crea y retorna un ttk.Progressbar (real) SIN empacarlo.
    El player puede hacer: progress_bar['value'] = ...
    """
    pb = ttkb.Progressbar(parent, orient=orient, length=length, mode=mode, maximum=maximum)
    return pb


# ================== Animación overlay (no interfiere con 'value') ==================
def iniciar_animacion_progress(progress_bar, *, speed_px=4, interval_ms=16, margin=2, bootstyle="primary"):
    """
    Monta un Canvas encima del Progressbar y anima un 'shine' que rebota.
    No toca el 'value' del Progressbar.
    """
    # Evitar duplicados
    if getattr(progress_bar, "_shine_running", False):
        return

    # Canvas superpuesto (SIN bg="" -> usa color por defecto del tema)
    canvas = tk.Canvas(progress_bar, highlightthickness=0, bd=0, relief="flat")
    # Se ajusta al tamaño del progressbar
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Color del segmento según bootstyle (fallback si no hay tema)
    try:
        style = ttkb.Style()
        c = style.colors
        fill_color = {
            "primary":  c.primary,
            "success":  c.success,
            "info":     c.info,
            "warning":  c.warning,
            "danger":   c.danger,
            "secondary": getattr(c, "secondary", c.secondaryfg),
        }.get(bootstyle, c.primary)
    except Exception:
        fill_color = "#0d6efd"

    # Guardar estado en el widget para poder detener/l limpiar
    progress_bar._shine_running = True
    progress_bar._shine_canvas = canvas

    state = {"ready": False, "seg_id": None, "seg_w": 0, "seg_h": 0, "x": 0, "dir": 1}

    def _build_segment(_evt=None):
        if not getattr(progress_bar, "_shine_running", False):
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 1)
        h = max(canvas.winfo_height(), 1)
        seg_w = max(8, int(w * 0.25))  # 25% del ancho
        seg_h = max(4, h - 4)
        x = margin
        y = (h - seg_h) // 2
        seg_id = canvas.create_rectangle(x, y, x + seg_w, y + seg_h,
                                         outline="", fill=fill_color)
        state.update({"ready": True, "seg_id": seg_id, "seg_w": seg_w, "seg_h": seg_h, "x": x, "dir": 1})

    canvas.bind("<Configure>", _build_segment)
    canvas.after(0, _build_segment)

    def _step():
        if not getattr(progress_bar, "_shine_running", False):
            return
        if not state["ready"]:
            canvas.after(interval_ms, _step)
            return

        w = max(canvas.winfo_width(), 1)
        right = w - margin - state["seg_w"]
        x = state["x"] + speed_px * state["dir"]

        if x <= margin:
            x = margin
            state["dir"] = 1
        elif x >= right:
            x = right
            state["dir"] = -1

        y = (max(canvas.winfo_height(), 1) - state["seg_h"]) // 2
        canvas.coords(state["seg_id"], x, y, x + state["seg_w"], y + state["seg_h"])
        state["x"] = x
        canvas.after(interval_ms, _step)

    # Limpieza si destruyen el progressbar
    def _on_destroy(_evt=None):
        detener_animacion_progress(progress_bar)

    progress_bar.bind("<Destroy>", _on_destroy, add="+")
    _step()


def detener_animacion_progress(progress_bar):
    """
    Detiene y limpia la animación overlay si existe.
    """
    if getattr(progress_bar, "_shine_running", False):
        progress_bar._shine_running = False
        try:
            if getattr(progress_bar, "_shine_canvas", None):
                progress_bar._shine_canvas.destroy()
        except Exception:
            pass
        progress_bar._shine_canvas = None


__all__ = ["crear_barra_progreso", "iniciar_animacion_progress", "detener_animacion_progress"]
