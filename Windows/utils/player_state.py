# utils/player_state.py
played_songs = []
current_song_index = -1
paused = False
play_mode = "Orden"
fade_duration = 2000
song_length = 0
progress_update_interval = 1000
playlist_ref = None
evento_en_progreso = None
stopped = False
_last_countdown_secs = None
_countdown_active = False
_event_started_at = None
_last_finished_id = None
_finished_reported = False

# NUEVO: solo avanzar la playlist si el usuario presionó Play
playback_started = False
