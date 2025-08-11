import sys
import random
import contextlib
import pygame
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from utils import events as evmod
from utils import programacion as prog
from utils import player_state as pst

if not pygame.mixer.get_init():
    pygame.mixer.init()

@contextlib.contextmanager
def _suppress_stderr():
    import os
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr_fd = os.dup(2)
        os.dup2(devnull, 2)
        yield
    finally:
        try:
            os.dup2(old_stderr_fd, 2)
        finally:
            os.close(old_stderr_fd)
            os.close(devnull)

def set_current_song_index(index):
    pst.current_song_index = index

def set_paused(value):
    pst.paused = value

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

def update_progress_bar(root, progress_bar):
    from utils.programacion import handle_event_or_next_song
    if pst.stopped:
        return
    # Si está pausado, NO disparemos el loop de eventos para que no salte a otra rola
    if pst.paused:
        root.after(pst.progress_update_interval, lambda: update_progress_bar(root, progress_bar))
        return
    if pygame.mixer.music.get_busy():
        current_time = pygame.mixer.music.get_pos() // 1000
        progress_bar['value'] = (current_time / pst.song_length) * 100 if pst.song_length > 0 else 0
        root.after(pst.progress_update_interval, lambda: update_progress_bar(root, progress_bar))
    else:
        handle_event_or_next_song(root, progress_bar, pst.playlist_ref)

def reproducir_evento(evento, root, progress_bar):
    pst.evento_en_progreso = evento
    pst._finished_reported = False
    prog.ensure_anchor(evento)
    try:
        with _suppress_stderr():
            pygame.mixer.music.load(evento["archivo"])
    except Exception:
        fail = evento.get("_fails", 0) + 1
        evento["_fails"] = fail
        if not evento.get("intervalo_repeticion") or fail >= 3:
            try:
                evmod.eventos.remove(evento)
            except ValueError:
                pass
        pst.evento_en_progreso = None
        return
    _, pst.song_length = get_duration(evento["archivo"])
    pygame.mixer.music.play(fade_ms=pst.fade_duration)
    pst._event_started_at = datetime.now()
    update_progress_bar(root, progress_bar)
    intervalo = evento.get("intervalo_repeticion")
    if intervalo and intervalo > 0:
        evento["hora_inicio"] = prog.next_multiple_after(evento["anchor"], intervalo, pst._event_started_at)
    else:
        try:
            evmod.eventos.remove(evento)
        except ValueError:
            pass

def play_current_song(root, playlist, progress_bar):
    pst.playlist_ref = playlist
    songs = playlist.get_children()
    if not songs:
        return
    if pst.current_song_index < 0 or pst.current_song_index >= len(songs):
        pst.current_song_index = 0
    playlist.selection_clear()
    song_id = songs[pst.current_song_index]
    playlist.selection_set(song_id)
    playlist.focus(song_id)
    song_item = playlist.item(song_id)
    song_path = song_item['values'][2]
    with _suppress_stderr():
        pygame.mixer.music.load(song_path)
    _, pst.song_length = get_duration(song_path)
    pygame.mixer.music.play(fade_ms=pst.fade_duration)
    update_progress_bar(root, progress_bar)

def play_song(root, playlist, progress_bar):
    pst.playlist_ref = playlist
    songs = playlist.get_children()
    if not songs:
        return
    pst.stopped = False
    # marcar que el usuario arrancó reproducción
    pst.playback_started = True
    if pst.paused:
        pygame.mixer.music.unpause()
        pst.paused = False
    else:
        selected = playlist.selection()
        if not selected:
            if pst.current_song_index < 0:
                pst.current_song_index = 0
        else:
            pst.current_song_index = playlist.index(selected[0])
        play_current_song(root, playlist, progress_bar)

def next_song(root, playlist, progress_bar):
    pst.playlist_ref = playlist
    if pst.stopped:
        return
    songs = playlist.get_children()
    if not songs:
        return
    if pst.play_mode == "Aleatorio":
        if len(pst.played_songs) >= len(songs):
            pst.played_songs.clear()
        remaining_songs = [i for i in range(len(songs)) if i not in pst.played_songs]
        next_index = random.choice(remaining_songs)
        pst.played_songs.append(next_index)
    else:
        next_index = (pst.current_song_index + 1) % len(songs)
    pst.current_song_index = next_index
    play_current_song(root, playlist, progress_bar)

def pause_song(playlist=None, mode_selector=None):
    # No disparemos nada más; solo toggle pausa
    if pygame.mixer.music.get_busy() and not pst.paused:
        pygame.mixer.music.pause()
        pst.paused = True
    elif pst.paused:
        pygame.mixer.music.unpause()
        pst.paused = False

def stop_song(playlist, mode_selector=None):
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(int(pst.fade_duration))
        else:
            pygame.mixer.music.stop()
    except Exception:
        pygame.mixer.music.stop()
    pst.paused = False
    pst.stopped = True
    # al hacer stop, deshabilitar autoplay desde el loop
    pst.playback_started = False

__all__ = [
    "play_song", "pause_song", "stop_song", "next_song",
    "set_current_song_index", "set_paused", "reproducir_evento",
    "update_progress_bar"
]
