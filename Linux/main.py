import os
import sys
import platform
import random
import pickle
import pygame
from datetime import datetime, timedelta
from tkinter import TclError

from mutagen.mp3 import MP3
from mutagen.wave import WAVE

# DnD
import tkinterdnd2 as td
from tkinterdnd2 import DND_FILES, DND_TEXT

from gui import create_gui
from utils import (
    save_state, load_state, load_playlist, save_playlist,
    new_playlist, update_play_mode,
    on_drop, play_song, pause_song, stop_song,
    next_song, open_event_window
)
from utils.explorer import setup_explorer
from utils.programacion import start_event_loop  # ⬅️ LOOP DE EVENTOS
# Para fallback de Wayland (pegar rutas/URIs)
from utils.playlist import add_to_playlist, find_music_files

from urllib.parse import urlparse, unquote  # normalizar file:// URIs


# ===================== TKDND PATH PORTABLE (venv / PyInstaller) =====================

ARCH_MAP = {
    "x86_64": "linux-x64",
    "aarch64": "linux-arm64",
    "armv7l": "linux-arm64",
}

arch = platform.machine()
tkdnd_folder = ARCH_MAP.get(arch, "linux-x64")

if getattr(sys, "frozen", False):
    # Ejecutable (PyInstaller): datos dentro de _MEIPASS
    base = sys._MEIPASS  # noqa
    tkdnd_base = os.path.join(base, "tkinterdnd2", "tkdnd", tkdnd_folder)
else:
    # Entorno de desarrollo: usar paquete instalado
    td_dir = os.path.dirname(td.__file__)
    tkdnd_base = os.path.join(td_dir, "tkdnd", tkdnd_folder)

tkdnd_path = os.path.join(tkdnd_base, "tkdnd.tcl")
tkdnd_unix_path = os.path.join(tkdnd_base, "tkdnd_unix.tcl")
os.environ["TKDND_LIBRARY"] = tkdnd_base


# ===================== Helpers Wayland: pegar desde portapapeles =====================

def _to_fs_path(p: str) -> str:
    """Convierte 'file:///home/user/tema.mp3' -> '/home/user/tema.mp3'."""
    if not p:
        return p
    p = p.strip()
    if p.startswith("file://"):
        return unquote(urlparse(p).path)
    return p


def _parse_text_uri_list(s: str):
    """
    text/uri-list: líneas con 'file:///...' (ignora comentarios '#').
    También acepta rutas crudas por línea.
    """
    out = []
    for line in (s or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _paste_into_playlist(root, playlist):
    """Fallback para Wayland: copiar en Nautilus (Ctrl+C) → pegar aquí (Ctrl+V)."""
    try:
        data = root.clipboard_get()
    except Exception:
        return 0

    total = 0
    for item in _parse_text_uri_list(data):
        p = _to_fs_path(item)
        if os.path.isdir(p):
            files = find_music_files(p)
            add_to_playlist(files, playlist)
            total += len(files)
        elif os.path.isfile(p):
            add_to_playlist([p], playlist)
            total += 1
    if total == 0:
        print("[paste] No se agregaron pistas (duplicados/extensiones no válidas).")
    return total


# ================================== APP ==================================

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

    # Cargar tkdnd
    try:
        root.tk.eval(f'source "{tkdnd_path}"')
        root.tk.eval(f'source "{tkdnd_unix_path}"')
        # Asegurar package require (por si acaso)
        try:
            root.tk.call('package', 'require', 'tkdnd')
        except TclError:
            pass
    except TclError as e:
        print(f"⚠️ Error cargando tkdnd: {e}")
        print(f"Archivos usados:\n  {tkdnd_path}\n  {tkdnd_unix_path}")

    setup_explorer(tree, playlist)

    # --- DnD vs Wayland fallback ---
    session = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    if session == "wayland":
        # En Wayland, Tk corre en XWayland y Nautilus en Wayland → DnD no llega.
        # Fallback: pegar desde portapapeles (Ctrl+V / Ctrl+Shift+V)
        root.bind_all("<Control-v>", lambda e: _paste_into_playlist(root, playlist))
        root.bind_all("<Control-V>", lambda e: _paste_into_playlist(root, playlist))
        root.bind_all("<Control-Shift-v>", lambda e: _paste_into_playlist(root, playlist))
        root.bind_all("<Control-Shift-V>", lambda e: _paste_into_playlist(root, playlist))
        print("[info] Sesión Wayland detectada: usando fallback de Pegar (Ctrl+V).")
    else:
        # Xorg: DnD sí funciona
        try:
            playlist.drop_target_register(DND_FILES, DND_TEXT)
            playlist.dnd_bind('<<Drop>>', lambda e: on_drop(e, root, playlist))
        except TclError as e:
            print(f"[DnD] No se pudo registrar DnD ({e}). Activando fallback pegar.")
            root.bind_all("<Control-v>", lambda e: _paste_into_playlist(root, playlist))
            root.bind_all("<Control-V>", lambda e: _paste_into_playlist(root, playlist))

    # Botones y bindings
    add_event_button.config(command=lambda: open_event_window(root, event_list))
    play_button.config(command=lambda: play_song(root, playlist, progress_bar))
    pause_button.config(command=lambda: pause_song(playlist, mode_selector))
    stop_button.config(command=lambda: stop_song(playlist))
    next_button.config(command=lambda: next_song(root, playlist, progress_bar))

    mode_selector.bind("<<ComboboxSelected>>",
                       lambda e: update_play_mode(e, mode_selector, playlist))

    # Cargar estado (incluye eventos)
    load_state(playlist, event_list, mode_selector)

    # Loop de eventos (cada ~1s)
    start_event_loop(root, progress_bar, playlist)

    root.mainloop()


if __name__ == "__main__":
    run()
