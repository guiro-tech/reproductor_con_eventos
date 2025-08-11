import ttkbootstrap as ttkb
import tkinter as tk
from ttkbootstrap.constants import *
from gui.style import apply_style

# === módulos externos (tuyos) ===
from .botones import crear_controles
from .tabla_de_reproduccion import crear_tabla_reproduccion
from .tabla_de_eventos import crear_tabla_eventos
from .barra_de_progreso import crear_barra_progreso, iniciar_animacion_progress
from .explorador import crear_explorador
from .menu_app import crear_menu
from .animation import fade_in_window, slide_pad_in, bind_hover_lift
from .dnd import install_dnd_glow
from .window import crear_root


# ---- helper: eliminar selección del playlist ----
def _eliminar_seleccion_playlist(playlist):
    seleccion = playlist.selection()
    for item in seleccion:
        playlist.delete(item)


# ---------------------- MAIN ----------------------
def create_gui():
    root = crear_root()
    root.after(0, lambda: apply_style(root))

    # grid base
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=0)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Explorador
    frame_explorer, tree = crear_explorador(root)

    # Tabla de eventos (abajo-izquierda)
    details_frame, event_list, add_event_button = crear_tabla_eventos(root)

    # Controles
    frame_controls, botones = crear_controles(root)

    # Modo + barra de progreso
    frame_mode = ttkb.Frame(root)
    frame_mode.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

    mode_selector = ttkb.Combobox(
        frame_mode,
        values=["Orden", "Aleatorio"],
        state="readonly",
    )
    mode_selector.current(0)
    mode_selector.pack(padx=5, pady=5)

    # Progressbar REAL (determinate) + animación overlay que no toca 'value'
    progress_bar = crear_barra_progreso(frame_mode, length=280, mode="determinate")
    progress_bar.pack(padx=10, pady=10)
    iniciar_animacion_progress(progress_bar, speed_px=4, margin=2, bootstyle="primary")

    # Playlist
    frame_playlist, playlist = crear_tabla_reproduccion(root)

    # ---- Menú contextual (click derecho) para eliminar del playlist ----
    menu_playlist = ttkb.Menu(root, tearoff=0)
    menu_playlist.add_command(
        label="Eliminar",
        command=lambda: _eliminar_seleccion_playlist(playlist)
    )

    def _mostrar_menu_playlist(event):
        try:
            item = playlist.identify_row(event.y)
            if item:
                playlist.selection_set(item)  # selecciona el item bajo el cursor
                menu_playlist.tk_popup(event.x_root, event.y_root)
        finally:
            menu_playlist.grab_release()

    # Click derecho
    playlist.bind("<Button-3>", _mostrar_menu_playlist)
    # (Opcional) tecla Supr para borrar selección
    playlist.bind("<Delete>", lambda e: _eliminar_seleccion_playlist(playlist))

    # --------------------- Animaciones / binds ----------------------
    fade_in_window(root)
    slide_pad_in(root, frame_explorer, from_pad=48, to_pad=10, duration_ms=420)
    slide_pad_in(root, frame_playlist, from_pad=56, to_pad=10, duration_ms=460)
    slide_pad_in(root, frame_controls, from_pad=36, to_pad=10, duration_ms=360)

    for b in botones.values():
        bind_hover_lift(root, b)

    install_dnd_glow(root, tree, frame_explorer)
    install_dnd_glow(root, playlist, frame_playlist)

    # ---- Contexto para menú: refs a widgets que el menú usará ----
    ctx = {
        "root": root,
        "tree": tree,
        "event_list": event_list,
        "add_event_button": add_event_button,
        "play_button": botones["play"],
        "pause_button": botones["pause"],
        "stop_button": botones["stop"],
        "next_button": botones["next"],
        "mode_selector": mode_selector,
        "playlist": playlist,
        "progress_bar": progress_bar,
    }

    # Menú (al final, ya con ctx listo)
    crear_menu(root, ctx)

    return ctx


__all__ = ["create_gui"]
