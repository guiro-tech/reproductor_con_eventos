# gui/window.py
import ttkbootstrap as ttkb
from tkinterdnd2 import TkinterDnD

class CustomTk(TkinterDnD.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttkb.Style("cyborg")

def crear_root(title="Reproductor con eventos", size="1000x600"):
    root = CustomTk()
    root.title(title)
    root.geometry(size)
    return root
