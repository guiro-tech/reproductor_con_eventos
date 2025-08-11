# gui/menu_app.py
import ttkbootstrap as ttkb
from tkinter import filedialog, messagebox

from utils.state import save_state, load_state

def _clear_ui(ctx):
    try:
        ctx["playlist"].delete(*ctx["playlist"].get_children(""))
    except Exception:
        pass
    try:
        ctx["event_list"].delete(*ctx["event_list"].get_children(""))
    except Exception:
        pass

def _reset_runtime_flags():
    try:
        from utils.player import set_current_song_index, set_paused
        from utils.playlist import set_play_mode
        set_current_song_index(-1)
        set_paused(True)
        set_play_mode("Orden")
    except Exception as e:
        print(f"⚠️ No se pudieron resetear flags runtime: {e}")

def nuevo_proyecto(ctx):
    if not messagebox.askyesno("Nuevo", "¿Limpiar playlist y eventos?"):
        return
    _clear_ui(ctx)
    _reset_runtime_flags()
    try:
        ctx["mode_selector"].set("Orden")
    except Exception:
        pass
    messagebox.showinfo("Nuevo", "Proyecto en blanco.")

def cargar_proyecto(ctx):
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo de estado",
        filetypes=[("Estado del reproductor", "*.pkl"), ("Todos los archivos", "*.*")]
    )
    if not file_path:
        return
    load_state(ctx["playlist"], ctx["event_list"], ctx["mode_selector"], file_path)
    messagebox.showinfo("Cargar", f"Estado cargado desde:\n{file_path}")

def guardar_proyecto(ctx):
    file_path = filedialog.asksaveasfilename(
        title="Guardar estado como",
        defaultextension=".pkl",
        filetypes=[("Estado del reproductor", "*.pkl"), ("Todos los archivos", "*.*")]
    )
    if not file_path:
        return
    save_state(ctx["playlist"], ctx["event_list"], ctx["mode_selector"], file_path)
    messagebox.showinfo("Guardar", f"Estado guardado en:\n{file_path}")

def crear_menu(root, ctx):
    menu_bar = ttkb.Menu(root)

    file_menu = ttkb.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Nuevo",   command=lambda: nuevo_proyecto(ctx))
    file_menu.add_command(label="Cargar",  command=lambda: cargar_proyecto(ctx))
    file_menu.add_command(label="Guardar", command=lambda: guardar_proyecto(ctx))
    file_menu.add_separator()
    file_menu.add_command(label="Salir", command=root.quit)

    menu_bar.add_cascade(label="Archivo", menu=file_menu)
    root.config(menu=menu_bar)
    return menu_bar
