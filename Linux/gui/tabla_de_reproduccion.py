# gui/tabla_de_reproduccion.py
import ttkbootstrap as ttkb

def crear_tabla_reproduccion(root, *,
                             row=0, column=1, rowspan=2,
                             sticky="nsew", padx=10, pady=10):
    """
    Crea la tabla de reproducción con el mismo estilo actual,
    pero con tamaño fijo como la captura enviada.
    """
    # Contenedor
    frame_playlist = ttkb.Frame(root)
    frame_playlist.grid(row=row, column=column, rowspan=rowspan,
                        sticky=sticky, padx=padx, pady=pady)

    # Bloquear auto-ajuste
    frame_playlist.grid_propagate(False)
    frame_playlist.configure(width=550, height=300)  # tamaño aproximado de tu imagen

    # Treeview
    playlist = ttkb.Treeview(
        frame_playlist,
        columns=("Nombre", "Duración", "Ruta"),
        show="headings",
        height=8  # altura en filas (aprox. como la imagen)
    )

    # Encabezados (igual que tenías)
    playlist.heading("Nombre", text="🎵 Nombre de la Canción", anchor="w")
    playlist.heading("Duración", text="⏱️ Duración", anchor="center")
    playlist.heading("Ruta", text="📂 Ruta", anchor="w")

    # Columnas ajustadas al ancho total (~550px)
    playlist.column("Nombre", width=250, anchor="w", stretch=False)
    playlist.column("Duración", width=80, anchor="center", stretch=False)
    playlist.column("Ruta", width=200, anchor="w", stretch=False)

    # Scrollbar vertical
    sb = ttkb.Scrollbar(frame_playlist, orient="vertical", command=playlist.yview)
    playlist.configure(yscrollcommand=sb.set)

    sb.pack(side="right", fill="y")
    playlist.pack(side="left", fill="both", expand=True)

    return frame_playlist, playlist

__all__ = ["crear_tabla_reproduccion"]
