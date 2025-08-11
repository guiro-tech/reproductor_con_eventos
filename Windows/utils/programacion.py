# utils/programacion.py
import os
import sys
from datetime import datetime, timedelta
from utils import events as evmod
from utils import player_state as pst

def is_oneshot(e):
    return not e.get("intervalo_repeticion")

def sec_bucket(dt: datetime) -> datetime:
    return dt.replace(microsecond=0)

def _has_valid_file(e):
    p = e.get("archivo") or ""
    return bool(p) and os.path.isfile(p)

def winner_in_bucket(bucket):
    if not bucket:
        return None
    ones_valid = [e for e in bucket if is_oneshot(e) and _has_valid_file(e)]
    if ones_valid:
        return sorted(ones_valid, key=lambda e: (e.get("nombre",""), id(e)))[0]
    any_valid = [e for e in bucket if _has_valid_file(e)]
    if any_valid:
        return sorted(any_valid, key=lambda e: (0 if is_oneshot(e) else 1, e.get("nombre",""), id(e)))[0]
    ones = [e for e in bucket if is_oneshot(e)]
    base = ones if ones else bucket
    return sorted(base, key=lambda e: (e.get("nombre",""), id(e)))[0]

def ensure_anchor(ev):
    if "anchor" not in ev or not isinstance(ev["anchor"], datetime):
        ev["anchor"] = ev.get("hora_inicio")

def next_multiple_after(anchor: datetime, interval_s: int, t: datetime) -> datetime:
    if interval_s <= 0:
        return t
    elapsed = (t - anchor).total_seconds()
    k = int(elapsed // interval_s) + 1
    return anchor + timedelta(seconds=interval_s * k)

def next_future_event(now: datetime):
    futuros = [e for e in evmod.eventos if e.get("hora_inicio") and e["hora_inicio"] > now]
    if not futuros:
        return None
    min_sec = min(sec_bucket(e["hora_inicio"]) for e in futuros)
    bucket = [e for e in futuros if sec_bucket(e["hora_inicio"]) == min_sec]
    return winner_in_bucket(bucket)

def select_due_event(now: datetime):
    vencidos = [e for e in evmod.eventos if e.get("hora_inicio") and e["hora_inicio"] <= now]
    if not vencidos:
        return None
    max_sec = max(sec_bucket(e["hora_inicio"]) for e in vencidos)
    bucket = [e for e in vencidos if sec_bucket(e["hora_inicio"]) == max_sec]
    return winner_in_bucket(bucket)

def reschedule_repeats_after_block(block_start: datetime, block_end: datetime):
    for e in evmod.eventos:
        intervalo = e.get("intervalo_repeticion")
        hora = e.get("hora_inicio")
        if not intervalo or not isinstance(hora, datetime):
            continue
        ensure_anchor(e)
        if block_start <= hora <= block_end:
            e["hora_inicio"] = next_multiple_after(e["anchor"], intervalo, block_end)

def pick_event_to_fire(now: datetime):
    ev = select_due_event(now)
    if not ev:
        return None
    sec = sec_bucket(ev["hora_inicio"])
    same = [e for e in evmod.eventos if e.get("hora_inicio") and sec_bucket(e["hora_inicio"]) == sec and e["hora_inicio"] <= now]
    win = winner_in_bucket(same) or ev
    if not _has_valid_file(win) and is_oneshot(win):
        try:
            evmod.eventos.remove(win)
        except Exception:
            pass
        rest = [e for e in same if e is not win]
        win2 = winner_in_bucket(rest)
        return win2
    if not _has_valid_file(win):
        rest = [e for e in same if e is not win and _has_valid_file(e)]
        if rest:
            return winner_in_bucket(rest)
    return win

def _print_countdown_line(nombre, secs):
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    line = f"[EVENTO] Siguiente: '{nombre}' en {h:02d}:{m:02d}:{s:02d}"
    sys.stdout.write("\r" + line + " " * 12)
    sys.stdout.flush()

def _clear_countdown_line():
    sys.stdout.write("\r" + " " * 140 + "\r")
    sys.stdout.flush()

def _show_countdown(now):
    proximo = next_future_event(now)
    if proximo:
        secs = int((proximo["hora_inicio"] - now).total_seconds())
        if secs >= 0 and secs != pst._last_countdown_secs:
            _print_countdown_line(proximo.get("nombre", ""), secs)
            pst._last_countdown_secs = secs
            pst._countdown_active = True
    else:
        if pst._countdown_active:
            _clear_countdown_line()
            pst._countdown_active = False
            pst._last_countdown_secs = None

def handle_event_or_next_song(root, progress_bar, playlist):
    import pygame
    from utils.player import reproducir_evento, next_song

    if pst.stopped:
        return

    now = datetime.now()

    if pst.evento_en_progreso is not None and is_oneshot(pst.evento_en_progreso):
        if pygame.mixer.music.get_busy():
            if pst._countdown_active:
                _clear_countdown_line()
                pst._countdown_active = False
                pst._last_countdown_secs = None
            root.after(1000, lambda: handle_event_or_next_song(root, progress_bar, playlist))
            return

    try:
        _show_countdown(now)
    except Exception:
        pass

    evento_vencido = select_due_event(now)

    if pygame.mixer.music.get_busy():
        if evento_vencido is not None:
            ganador = pick_event_to_fire(now) or evento_vencido
            if not ganador:
                root.after(1000, lambda: handle_event_or_next_song(root, progress_bar, playlist))
                return
            try:
                pygame.mixer.music.fadeout(300)
            except Exception:
                pygame.mixer.music.stop()
            root.after(320, lambda ev=ganador: reproducir_evento(ev, root, progress_bar))
            return
        root.after(1000, lambda: handle_event_or_next_song(root, progress_bar, playlist))
        return

    if pst.evento_en_progreso is not None:
        ev_id = id(pst.evento_en_progreso)
        if pst._last_finished_id != ev_id or not pst._finished_reported:
            nombre = pst.evento_en_progreso.get("nombre", "")
            intervalo = pst.evento_en_progreso.get("intervalo_repeticion")
            if not intervalo and pst._event_started_at is not None:
                reschedule_repeats_after_block(pst._event_started_at, now)
            if intervalo:
                proxima = pst.evento_en_progreso.get("hora_inicio")
                next_txt = proxima.strftime("%H:%M:%S") if hasattr(proxima, "strftime") else "desconocida"
                _clear_countdown_line()
                sys.stdout.write(f"\r[EVENTO] Finalizado: '{nombre}' | Se repetirá a las {next_txt}\n")
                sys.stdout.flush()
            else:
                _clear_countdown_line()
                sys.stdout.write(f"\r[EVENTO] Finalizado: '{nombre}'\n")
                sys.stdout.flush()
            pst._last_finished_id = ev_id
            pst._finished_reported = True
        pst.evento_en_progreso = None

        now2 = datetime.now()
        ev2 = select_due_event(now2)
        if ev2 is not None:
            ganador2 = pick_event_to_fire(now2) or ev2
            if ganador2 and _has_valid_file(ganador2):
                reproducir_evento(ganador2, root, progress_bar)
                return
            else:
                if ganador2 and is_oneshot(ganador2):
                    try:
                        evmod.eventos.remove(ganador2)
                    except Exception:
                        pass
        # REANUDAR playlist solo si el usuario dio Play y no está en pausa
        if pst.playback_started and not pst.paused and playlist is not None:
            next_song(root, playlist, progress_bar)
            return
        try:
            _show_countdown(now2)
        except Exception:
            pass

    if evento_vencido is not None:
        ganador = pick_event_to_fire(now) or evento_vencido
        if ganador and _has_valid_file(ganador):
            reproducir_evento(ganador, root, progress_bar)
        else:
            if ganador and is_oneshot(ganador):
                try:
                    evmod.eventos.remove(ganador)
                except Exception:
                    pass
        return

    # Fallback normal: solo avanzar música si el usuario arrancó la reproducción y NO está en pausa
    if pst.playback_started and not pst.paused and playlist is not None:
        next_song(root, playlist, progress_bar)

def start_event_loop(root, progress_bar, playlist):
    pst.playlist_ref = playlist
    def _tick():
        try:
            handle_event_or_next_song(root, progress_bar, pst.playlist_ref)
        finally:
            root.after(1000, _tick)
    root.after(1000, _tick)

__all__ = [
    "is_oneshot",
    "sec_bucket",
    "winner_in_bucket",
    "ensure_anchor",
    "next_future_event",
    "select_due_event",
    "next_multiple_after",
    "reschedule_repeats_after_block",
    "pick_event_to_fire",
    "handle_event_or_next_song",
    "start_event_loop",
]
