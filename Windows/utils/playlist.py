# utils/playlist.py
import os
import re
import pickle
from urllib.parse import urlparse, unquote
from tkinter import filedialog
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from utils.state import save_state
from utils import player_state as pst  # <-- unificamos estado aquí

allowed_extensions = ['.mp3', '.wav']

def set_play_mode(mode: str):
    """
    Fija el modo de reproducción y limpia historial de aleatorio,
    usando SIEMPRE el estado central en player_state.
    """
    pst.play_mode = (mode or "Orden")
    pst.played_songs.clear()

def get_play_mode() -> str:
    """Devolver el modo actual desde el estado central."""
    return pst.play_mode or "Orden"

def load_playlist(playlist):
    file_path = filedialog.askopenfilename(
        title="Cargar lista de reproducción",
        filetypes=[("Pickle Files", "*.pkl")]
    )
    if file_path:
        with open(file_path, "rb") as f:
            playlist_data = pickle.load(f)
            playlist.delete(*playlist.get_children())
            for song in playlist_data.get("playlist", []):
                playlist.insert("", "end", values=song)

def save_playlist(playlist):
    file_path = filedialog.asksaveasfilename(
        title="Guardar lista de reproducción",
        defaultextension=".pkl",
        filetypes=[("Pickle Files", "*.pkl")]
    )
    if file_path:
        playlist_data = {
            "playlist": [playlist.item(item)["values"] for item in playlist.get_children()]
        }
        with open(file_path, "wb") as f:
            pickle.dump(playlist_data, f)

def new_playlist(playlist):
    playlist.delete(*playlist.get_children())

def update_play_mode(*args):
    """
    Firmas soportadas:
      - update_play_mode(event, mode_selector, playlist)
      - update_play_mode(playlist, mode_selector)
      - update_play_mode(event, mode_selector)
    """
    mode_selector = None
    playlist = None

    for a in args:
        if hasattr(a, "get_children") and hasattr(a, "insert"):
            playlist = a
        elif hasattr(a, "get") and hasattr(a, "set"):
            mode_selector = a

    if mode_selector is None:
        return

    # Actualizamos el estado central
    set_play_mode(mode_selector.get())

    # Guardamos si tenemos playlist
    if playlist is not None:
        # event_list y mode_selector son opcionales en save_state
        save_state(playlist, None, mode_selector)

def get_duration(file_path):
    try:
        if file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
        elif file_path.lower().endswith('.wav'):
            audio = WAVE(file_path)
        else:
            return "00:00", 0
        duration = int(audio.info.length)
        minutes, seconds = divmod(duration, 60)
        return f"{minutes:02}:{seconds:02}", duration
    except Exception:
        return "00:00", 0

def add_to_playlist(files, playlist):
    for file_path in files:
        if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in allowed_extensions:
            file_name = os.path.basename(file_path)
            file_duration, _ = get_duration(file_path)
            playlist.insert("", "end", values=(file_name, file_duration, file_path))
    # Guardamos el estado (parámetros opcionales en save_state)
    save_state(playlist)

def find_music_files(folder_path):
    music_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in allowed_extensions:
                music_files.append(os.path.join(root_dir, file))
    return music_files

def _parse_dnd_paths_fallback(dnd_data: str):
    if not dnd_data:
        return []
    tokens = re.findall(r'\{[^}]*\}|\S+', dnd_data)
    paths = []
    for t in tokens:
        t = t.strip()
        if t.startswith("{") and t.endswith("}"):
            t = t[1:-1]
        if t.lower().startswith("file:"):
            u = urlparse(t)
            p = unquote(u.path or "")
            if os.name == "nt" and p.startswith("/") and len(p) > 2 and p[2] == ":":
                p = p[1:]  # /C:/... -> C:/...
            t = p
        if os.name == "nt":
            t = t.replace("/", "\\")
        paths.append(t)
    return paths

def on_drop(event, root, playlist):
    try:
        file_paths = root.tk.splitlist(event.data)
    except Exception:
        file_paths = _parse_dnd_paths_fallback(event.data)

    for file_path in file_paths:
        if os.path.isdir(file_path):
            music_files = find_music_files(file_path)
            add_to_playlist(music_files, playlist)
        elif os.path.isfile(file_path):
            add_to_playlist([file_path], playlist)

__all__ = [
    "load_playlist", "save_playlist", "new_playlist", "update_play_mode",
    "add_to_playlist", "on_drop", "set_play_mode", "get_play_mode"
]
1