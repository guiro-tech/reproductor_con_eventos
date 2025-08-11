# utils/playlist.py
import os
import pickle
import urllib.parse  # <- para normalizar URIs file:// en Linux
from tkinter import filedialog
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from utils.state import save_state

allowed_extensions = ['.mp3', '.wav']
played_songs = []
play_mode = "Orden"


def set_play_mode(mode: str):
    """Fija el modo de reproducción sin disparar eventos de UI."""
    global play_mode, played_songs
    play_mode = mode or "Orden"
    played_songs.clear()


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
    Soporta varias firmas:
      - update_play_mode(event, mode_selector, playlist)
      - update_play_mode(playlist, mode_selector)
      - update_play_mode(event, mode_selector)  (NO guarda estado por faltar playlist)
    Detecta quién es quién por atributos.
    """
    global play_mode, played_songs

    mode_selector = None
    playlist = None

    for a in args:
        # Detectar playlist (Treeview) por métodos típicos
        if hasattr(a, "get_children") and hasattr(a, "insert"):
            playlist = a
        # Detectar combobox por .get y .set (Treeview no tiene .get)
        elif hasattr(a, "get") and hasattr(a, "set"):
            mode_selector = a

    if mode_selector is None:
        # Nada que hacer si no sabemos el selector
        return

    play_mode = mode_selector.get() or "Orden"
    played_songs.clear()

    # Solo guardamos si tenemos playlist y mode_selector
    if playlist is not None:
        save_state(playlist, mode_selector)


def get_duration(file_path):
    try:
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
        elif file_path.endswith('.wav'):
            audio = WAVE(file_path)
        else:
            return "00:00", 0
        duration = int(audio.info.length)
        minutes, seconds = divmod(duration, 60)
        return f"{minutes:02}:{seconds:02}", duration
    except Exception:
        return "00:00", 0


def find_music_files(folder_path):
    music_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in allowed_extensions:
                music_files.append(os.path.join(root_dir, file))
    return music_files


# ======================= Normalización de rutas (Linux) =======================

def _to_fs_path(p: str) -> str:
    """
    Convierte 'file:///home/usuario/tema.mp3' -> '/home/usuario/tema.mp3'
    y deja igual si ya es ruta normal. Maneja %20, acentos, etc.
    """
    if not p:
        return p
    p = p.strip()
    if p.startswith("file://"):
        return urllib.parse.unquote(urllib.parse.urlparse(p).path)
    return p


# ======================= Inserción en playlist =======================

def add_to_playlist(files, playlist):
    """
    Inserta en el Treeview con values=(nombre, duración, ruta).
    Evita duplicados comparando la ruta (values[2]).
    """
    # Rutas ya existentes en la playlist
    existentes = set()
    for iid in playlist.get_children():
        vals = playlist.item(iid).get("values", [])
        if len(vals) >= 3:
            existentes.add(str(vals[2]))

    for file_path in files:
        file_path = _to_fs_path(file_path)
        if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in allowed_extensions:
            if file_path in existentes:
                continue  # duplicado, nel
            file_name = os.path.basename(file_path)
            file_duration, _ = get_duration(file_path)
            playlist.insert("", "end", values=(file_name, file_duration, file_path))
            existentes.add(file_path)

    # Guardamos el estado; el mode_selector puede ser None aquí y no pasa nada
    save_state(playlist, None)


# ======================= Drag & Drop handler =======================

def on_drop(event, root, playlist):
    """
    Handler para TkDND:
        playlist.drop_target_register(DND_FILES)
        playlist.dnd_bind('<<Drop>>', lambda e: on_drop(e, root, playlist))
    Soporta múltiples archivos, carpetas, y URIs file:// en Linux.
    """
    # print("DROP RAW:", event.data)  # <- descomenta para debug
    file_paths = [_to_fs_path(p) for p in root.tk.splitlist(event.data)]
    for file_path in file_paths:
        if os.path.isdir(file_path):
            music_files = find_music_files(file_path)
            add_to_playlist(music_files, playlist)
        elif os.path.isfile(file_path):
            add_to_playlist([file_path], playlist)

def _parse_text_uri_list(s: str):
    """
    text/uri-list: líneas con 'file:///...' (ignorar comentarios con '#')
    También acepta rutas crudas por línea.
    """
    out = []
    for line in (s or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out

def paste_into_playlist(root, playlist):
    """
    Lee el portapapeles y agrega archivos/carpetas a la playlist.
    Soporta:
      - text/uri-list  (file:///…)
      - rutas crudas (una por línea)
    """
    try:
        data = root.clipboard_get()
    except Exception:
        return 0

    # Reusar normalización del drop (si ya la agregaste)
    conv = globals().get('_to_fs_path', lambda p: p)

    total = 0
    for item in _parse_text_uri_list(data):
        p = conv(item)
        if os.path.isdir(p):
            total += add_to_playlist(find_music_files(p), playlist) or 0
        elif os.path.isfile(p):
            total += add_to_playlist([p], playlist) or 0
    return total
__all__ = [
    "load_playlist", "save_playlist", "new_playlist", "update_play_mode",
    "add_to_playlist", "on_drop", "set_play_mode", "play_mode",
    "find_music_files", "get_duration", "allowed_extensions",
    "paste_into_playlist"  # <-- NUEVO
]
