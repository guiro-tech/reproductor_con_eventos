# utils/state.py
import os
import pickle
from typing import Optional
from datetime import datetime, timedelta
import os.path as _osp

STATE_FILE = "estado_reproductor.pkl"

def _format_repeat(intervalo: Optional[int]) -> str:
    """Devuelve texto 'Una sola vez' | 'Cada N Horas/Minutos/Segundos'."""
    if not intervalo:
        return "Una sola vez"
    if intervalo % 3600 == 0:
        return f"Cada {intervalo // 3600} Horas"
    if intervalo % 60 == 0:
        return f"Cada {intervalo // 60} Minutos"
    return f"Cada {intervalo} Segundos"

def save_state(playlist, event_list, mode_selector: Optional[object], file_path: Optional[str] = None):
    """
    Guarda:
      - play_mode, current_song_index, paused
      - playlist (tabla visual)
      - event_list (tabla visual)
      - eventos (lista real que usa el player: nombre, hora_inicio, intervalo_repeticion, archivo)
    """
    from utils.player import current_song_index, paused  # evita import circular al cargar módulo
    from utils.playlist import play_mode
    from utils import events as evmod

    target_file = file_path if file_path else STATE_FILE

    try:
        state = {
            "play_mode": play_mode,
            "current_song_index": current_song_index,
            "paused": paused,
            # Tablas visuales
            "playlist": [playlist.item(item)["values"] for item in playlist.get_children()],
            "event_list": [event_list.item(item)["values"] for item in event_list.get_children()],
            # Estructura real de eventos (para que el loop funcione al reabrir)
            "eventos": evmod.eventos,
        }
        with open(target_file, "wb") as f:
            pickle.dump(state, f)
    except Exception as e:
        print(f"⚠️ No se pudo guardar estado: {e}")

def load_state(playlist, event_list, mode_selector: Optional[object], file_path: Optional[str] = None):
    """
    Carga el estado y:
      - repinta playlist
      - reconstruye la lista real utils.events.eventos (si existe en el .pkl la usa directo;
        si no, intenta reconstruir desde la tabla visual como fallback)
      - repinta la tabla de eventos con 4 columnas: Pista | Tiempo | Duración | Repetir
      - restaura play_mode, índice y paused
    """
    from utils.player import set_current_song_index, set_paused
    from utils.playlist import set_play_mode, get_duration
    from utils import events as evmod

    target_file = file_path if file_path else STATE_FILE
    if not os.path.exists(target_file):
        print("⚠️ No existe el archivo de estado.")
        return

    try:
        with open(target_file, "rb") as f:
            state = pickle.load(f)
    except Exception as e:
        print(f"⚠️ No se pudo cargar estado: {e}")
        return

    try:
        # ---------- Playlist visual ----------
        playlist.delete(*playlist.get_children())
        for row in state.get("playlist", []):
            playlist.insert("", "end", values=row)

        # ---------- Eventos ----------
        event_list.delete(*event_list.get_children())

        # 1) Preferir la estructura real de eventos del .pkl (si existe)
        eventos_guardados = state.get("eventos")

        # limpiar SIN reasignar la lista compartida
        evmod.eventos.clear()

        if isinstance(eventos_guardados, list) and eventos_guardados:
            # Rellenar sin cambiar la referencia
            evmod.eventos.extend(eventos_guardados)

            # Repintar tabla visual desde la lista real
            for ev in evmod.eventos:
                try:
                    nombre = ev.get("nombre", "")
                    archivo = ev.get("archivo", "")
                    hora_inicio = ev.get("hora_inicio")  # debería ser datetime (pickle lo soporta)
                    intervalo = ev.get("intervalo_repeticion")

                    if not isinstance(hora_inicio, datetime):
                        raise ValueError("hora_inicio no es datetime")

                    file_name = _osp.basename(archivo) if archivo else (nombre or "")
                    hora_str = hora_inicio.strftime("%H:%M:%S")
                    dur_str, _ = get_duration(archivo) if archivo else ("00:00", 0)
                    rep_text = _format_repeat(intervalo)

                    event_list.insert("", "end", values=(file_name, hora_str, dur_str, rep_text))
                except Exception as e:
                    print(f"⚠️ Evento inválido al cargar: {e}")

        else:
            # 2) Fallback legacy: reconstruir desde la tabla visual guardada (no trae 'archivo' real)
            legacy_rows = state.get("event_list", [])
            for evrow in legacy_rows:
                try:
                    # Se esperaba: (Pista, Tiempo(HH:MM:SS), Duración, Repetir)
                    pista = evrow[0] if len(evrow) > 0 else ""
                    hora_str = evrow[1] if len(evrow) > 1 else "00:00:00"
                    rep_text = evrow[3] if len(evrow) > 3 else "Una sola vez"

                    # reconstruir hora_inicio a partir de la hora de hoy (o mañana si ya pasó)
                    ahora = datetime.now()
                    h, m, s = [int(x) for x in hora_str.split(":")]
                    hora_obj = ahora.replace(hour=h, minute=m, second=s, microsecond=0)
                    if hora_obj < ahora:
                        hora_obj += timedelta(days=1)

                    # reconstruir intervalo aproximado
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

                    # agregar a lista real (sin archivo porque no viene en legacy)
                    evmod.eventos.append({
                        "nombre": pista,
                        "hora_inicio": hora_obj,
                        "intervalo_repeticion": intervalo,
                        "archivo": "",  # no hay info en legacy
                    })

                    # repintar fila tal cual venía
                    event_list.insert("", "end", values=evrow)

                except Exception as e:
                    print(f"⚠️ No se pudo reconstruir evento legacy: {e}")

        # ---------- Flags ----------
        loaded_mode = state.get("play_mode", "Orden")
        loaded_index = int(state.get("current_song_index", -1) or -1)
        loaded_paused = bool(state.get("paused", False))

        set_play_mode(loaded_mode)
        set_current_song_index(loaded_index)
        set_paused(loaded_paused)

        if mode_selector is not None and hasattr(mode_selector, "set"):
            mode_selector.set(loaded_mode)

        # Seleccionar ítem actual en playlist si aplica
        items = playlist.get_children()
        if 0 <= loaded_index < len(items):
            song_id = items[loaded_index]
            playlist.selection_set(song_id)
            playlist.focus(song_id)

    except Exception as e:
        print(f"⚠️ Error aplicando estado cargado: {e}")
