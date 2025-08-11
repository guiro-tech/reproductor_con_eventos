import os
import sys
import platform
import pickle
import pygame
from datetime import datetime, timedelta
from tkinter import TclError

print(">>> MAIN EN:", os.path.abspath(__file__))

from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from tkinterdnd2 import DND_FILES

from gui import create_gui
from utils import (
    save_state, load_state, load_playlist, save_playlist,
    new_playlist, update_play_mode,
    on_drop, play_song, pause_song, stop_song,
    next_song, open_event_window
)
from utils.explorer import setup_explorer
from utils.programacion import start_event_loop

# ---------------- tkdnd detection (Windows/Linux & PyInstaller) ----------------
def _find_tkdnd_paths():
    import importlib.util

    if os.name == "nt":
        folder_candidates = ["win-x64", "win-x86", "win-arm64", ""]
    else:
        arch = platform.machine().lower()
        folder_candidates = ["linux-x64", "linux-arm64", "osx-x64", "osx-arm64", ""]

    base_pkg = None
    spec = importlib.util.find_spec("tkinterdnd2")
    if spec and spec.origin:
        base_pkg = os.path.dirname(spec.origin)

    # PyInstaller bundle
    if getattr(sys, "_MEIPASS", None):
        pi_base = os.path.join(sys._MEIPASS, "tkinterdnd2", "tkdnd")
        for sub in folder_candidates:
            probe = os.path.join(pi_base, sub) if sub else pi_base
            tkdnd_tcl = os.path.join(probe, "tkdnd.tcl")
            if os.path.isfile(tkdnd_tcl):
                return probe, tkdnd_tcl, (os.path.join(probe, "tkdnd_unix.tcl") if os.name != "nt" else None)

    # venv site-packages
    if base_pkg:
        sp_base = os.path.join(base_pkg, "tkdnd")
        for sub in folder_candidates:
            probe = os.path.join(sp_base, sub) if sub else sp_base
            tkdnd_tcl = os.path.join(probe, "tkdnd.tcl")
            if os.path.isfile(tkdnd_tcl):
                return probe, tkdnd_tcl, (os.path.join(probe, "tkdnd_unix.tcl") if os.name != "nt" else None)

    # Fallbacks típicos
    fallbacks = []
    if os.name == "nt":
        fallbacks.append(os.path.abspath(".\\.env\\Lib\\site-packages\\tkinterdnd2\\tkdnd"))
    else:
        fallbacks.append(os.path.abspath("./.env/lib/python3.12/site-packages/tkinterdnd2/tkdnd"))

    for fb in fallbacks:
        for sub in folder_candidates:
            probe = os.path.join(fb, sub) if sub else fb
            tkdnd_tcl = os.path.join(probe, "tkdnd.tcl")
            if os.path.isfile(tkdnd_tcl):
                return probe, tkdnd_tcl, (os.path.join(probe, "tkdnd_unix.tcl") if os.name != "nt" else None)

    return None, None, None
# -----------------------------------------------------------------------------

def run():
    gui = create_gui()

    root = gui["root"]
    tree = gui["tree"]
    event_list = gui["event_list"]
    add_event_button = gui["add_event_button"]
    play_button = gui["play_button"]
    pause_button = gui["pause_button"]
    stop_button = gui["stop_button"]
    next_button = gui["next_button"]
    mode_selector = gui["mode_selector"]
    playlist = gui["playlist"]
    progress_bar = gui["progress_bar"]

    # Cargar tkdnd (portable y seguro en Windows usando / y tk.call)
    tkdnd_dir, tkdnd_path, tkdnd_unix_path = _find_tkdnd_paths()
    try:
        if tkdnd_dir and tkdnd_path and os.path.isfile(tkdnd_path):
            tkdnd_dir_posix = tkdnd_dir.replace("\\", "/")
            tkdnd_path_posix = tkdnd_path.replace("\\", "/")
            os.environ["TKDND_LIBRARY"] = tkdnd_dir_posix
            root.tk.call('source', tkdnd_path_posix)
            if tkdnd_unix_path and os.path.isfile(tkdnd_unix_path) and os.name != "nt":
                root.tk.call('source', tkdnd_unix_path.replace("\\", "/"))
        else:
            raise TclError("No se encontró carpeta tkdnd válida.")
    except TclError as e:
        print("⚠️ Error cargando tkdnd:", e)
        print("Rutas probadas:")
        print("  dir:", tkdnd_dir)
        print("  tcl:", tkdnd_path)
        print("  unix:", tkdnd_unix_path)

    setup_explorer(tree, playlist)

    # Drag-and-drop
    try:
        playlist.drop_target_register(DND_FILES)
        playlist.dnd_bind('<<Drop>>', lambda e: on_drop(e, root, playlist))
    except TclError:
        pass

    # Botones
    add_event_button.config(command=lambda: open_event_window(root, event_list))
    play_button.config(command=lambda: play_song(root, playlist, progress_bar))
    pause_button.config(command=lambda: pause_song(playlist, mode_selector))
    stop_button.config(command=lambda: stop_song(playlist))
    next_button.config(command=lambda: next_song(root, playlist, progress_bar))

    mode_selector.bind("<<ComboboxSelected>>", lambda e: update_play_mode(e, mode_selector, playlist))

    # Cargar estado
    load_state(playlist, event_list, mode_selector)

    # Loop de eventos (cada 1s)
    start_event_loop(root, progress_bar, playlist)

    root.mainloop()

if __name__ == "__main__":
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    run()
