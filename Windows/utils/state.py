# utils/state.py
import os
import pickle
from typing import Optional
from datetime import datetime, timedelta
import os.path as _osp

STATE_FILE = "estado_reproductor.pkl"

def _format_repeat(intervalo: Optional[int]) -> str:
    if not intervalo:
        return "Una sola vez"
    if intervalo % 3600 == 0:
        return f"Cada {intervalo // 3600} Horas"
    if intervalo % 60 == 0:
        return f"Cada {intervalo // 60} Minutos"
    return f"Cada {intervalo} Segundos"

def _get_duration_local(file_path: str):
    try:
        from mutagen.mp3 import MP3
        from mutagen.wave import WAVE
        if file_path and file_path.lower().endswith(".mp3"):
            audio = MP3(file_path)
        elif file_path and file_path.lower().endswith(".wav"):
            audio = WAVE(file_path)
        else:
            return "00:00", 0
        duration = int(getattr(audio.info, "length", 0) or 0)
        m, s = divmod(duration, 60)
        return f"{m:02}:{s:02}", duration
    except Exception:
        return "00:00", 0

def save_state(
    playlist,
    event_list: Optional[object] = None,
    mode_selector: Optional[object] = None,
    file_path: Optional[str] = None,
):
    from utils import events as evmod
    from utils import player_state as pst

    target_file = file_path if file_path else STATE_FILE

    try:
        playlist_rows = [playlist.item(item)["values"] for item in playlist.get_children()] if playlist else []
        event_rows = [event_list.item(item)["values"] for item in event_list.get_children()] if event_list else []

        state = {
            "play_mode": pst.play_mode,
            "current_song_index": pst.current_song_index,
            "paused": pst.paused,
            "playlist": playlist_rows,
            "event_list": event_rows,
            "eventos": evmod.eventos,
        }
        with open(target_file, "wb") as f:
            pickle.dump(state, f)
    except Exception as e:
        print(f"⚠️ No se pudo guardar estado: {e}")

def load_state(playlist, event_list, mode_selector: Optional[object], file_path: Optional[str] = None):
    from utils import events as evmod
    from utils import player_state as pst

    target_file = file_path if file_path else STATE_FILE
    if not os.path.exists(target_file):
        return

    try:
        with open(target_file, "rb") as f:
            state = pickle.load(f)
    except Exception as e:
        print(f"⚠️ No se pudo cargar estado: {e}")
        return

    try:
        playlist.delete(*playlist.get_children())
        for row in state.get("playlist", []):
            playlist.insert("", "end", values=row)

        event_list.delete(*event_list.get_children())

        eventos_guardados = state.get("eventos")
        evmod.eventos.clear()

        if isinstance(eventos_guardados, list) and eventos_guardados:
            evmod.eventos.extend(eventos_guardados)
            for ev in evmod.eventos:
                try:
                    nombre = ev.get("nombre", "")
                    archivo = ev.get("archivo", "")
                    hora_inicio = ev.get("hora_inicio")
                    intervalo = ev.get("intervalo_repeticion")

                    if not isinstance(hora_inicio, datetime):
                        raise ValueError("hora_inicio no es datetime")

                    file_name = _osp.basename(archivo) if archivo else (nombre or "")
                    hora_str = hora_inicio.strftime("%H:%M:%S")
                    dur_str, _ = _get_duration_local(archivo) if archivo else ("00:00", 0)
                    rep_text = _format_repeat(intervalo)

                    event_list.insert("", "end", values=(file_name, hora_str, dur_str, rep_text))
                except Exception as e:
                    print(f"⚠️ Evento inválido al cargar: {e}")
        else:
            legacy_rows = state.get("event_list", [])
            for evrow in legacy_rows:
                try:
                    pista = evrow[0] if len(evrow) > 0 else ""
                    hora_str = evrow[1] if len(evrow) > 1 else "00:00:00"
                    rep_text = evrow[3] if len(evrow) > 3 else "Una sola vez"

                    ahora = datetime.now()
                    h, m, s = [int(x) for x in hora_str.split(":")]
                    hora_obj = ahora.replace(hour=h, minute=m, second=s, microsecond=0)
                    if hora_obj < ahora:
                        hora_obj += timedelta(days=1)

                    intervalo = None
                    txt = (rep_text or "").strip().lower()
                    if txt.startswith("cada "):
                        try:
                            num = int(txt.split()[1])
                            if "hora" in txt:
                                intervalo = num * 3600
                            elif "minuto" in txt:
                                intervalo = num * 60
                            elif "segundo" in txt or txt.endswith("s"):
                                intervalo = num
                        except Exception:
                            intervalo = None

                    evmod.eventos.append({
                        "nombre": pista,
                        "hora_inicio": hora_obj,
                        "intervalo_repeticion": intervalo,
                        "archivo": "",
                    })

                    event_list.insert("", "end", values=evrow)
                except Exception as e:
                    print(f"⚠️ No se pudo reconstruir evento legacy: {e}")

        loaded_mode = state.get("play_mode", "Orden")
        loaded_index = int(state.get("current_song_index", -1) or -1)
        loaded_paused = bool(state.get("paused", False))

        pst.play_mode = loaded_mode
        pst.played_songs.clear()
        pst.current_song_index = loaded_index
        pst.paused = loaded_paused

        if mode_selector is not None and hasattr(mode_selector, "set"):
            mode_selector.set(loaded_mode)

        items = playlist.get_children()
        if 0 <= loaded_index < len(items):
            song_id = items[loaded_index]
            playlist.selection_set(song_id)
            playlist.focus(song_id)

    except Exception as e:
        print(f"⚠️ Error aplicando estado cargado: {e}")
