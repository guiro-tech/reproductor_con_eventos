# gui/interactions.py
def bind_progress_pulse(play_btn, pause_btn, stop_btn, progress):
    progress._running = False
    def on_play(_=None):
        try:
            progress.configure(mode="indeterminate")
            if not progress._running:
                progress.start(12)
                progress._running = True
        except Exception:
            pass
    def on_pause(_=None):
        try:
            progress.stop()
            progress._running = False
        except Exception:
            pass
    def on_stop(_=None):
        try:
            progress.stop()
            progress._running = False
        except Exception:
            pass
    play_btn.bind("<ButtonRelease-1>", on_play, add="+")
    pause_btn.bind("<ButtonRelease-1>", on_pause, add="+")
    stop_btn.bind("<ButtonRelease-1>", on_stop, add="+")
