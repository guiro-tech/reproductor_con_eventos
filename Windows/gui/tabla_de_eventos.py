# gui/tabla_de_eventos.py
import ttkbootstrap as ttkb

def crear_tabla_eventos(root, *,
                        row=1, column=0,
                        sticky="nsew", padx=10, pady=10):
    """
    Crea la tabla de eventos (misma estética),
    con botón 'Agregar Evento' dentro del mismo frame (abajo).
    """
    # Frame contenedor (celda izquierda inferior del layout)
    details_frame = ttkb.Frame(root)
    details_frame.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)

    # Tamaño fijo parecido a tu captura
    details_frame.configure(width=450, height=200)
    details_frame.grid_propagate(False)

    # ---- Layout interno del frame ----
    #  row 0: subframe con tabla + scrollbar
    #  row 1: botón Agregar Evento
    details_frame.grid_rowconfigure(0, weight=1)
    details_frame.grid_rowconfigure(1, weight=0)
    details_frame.grid_columnconfigure(0, weight=1)

    # Subframe para la tabla y su scrollbar (así no mezclamos pack/grid)
    table_holder = ttkb.Frame(details_frame)
    table_holder.grid(row=0, column=0, sticky="nsew")
    table_holder.grid_rowconfigure(0, weight=1)
    table_holder.grid_columnconfigure(0, weight=1)

    # Tabla
    event_list = ttkb.Treeview(
        table_holder,
        columns=("Pista", "Tiempo", "Duración", "Repetir"),
        show="headings",
        height=6
    )

    # Encabezados
    event_list.heading("Pista", text="🎵 Pista", anchor="w")
    event_list.heading("Tiempo", text="⏱️ Tiempo", anchor="center")
    event_list.heading("Duración", text="✏️ Duración", anchor="center")
    event_list.heading("Repetir", text="🔁 Repetir", anchor="center")

    # Columnas (mismo look, tamaños razonables)
    event_list.column("Pista",    width=200, anchor="w",      stretch=False)
    event_list.column("Tiempo",   width=80,  anchor="center", stretch=False)
    event_list.column("Duración", width=80,  anchor="center", stretch=False)
    event_list.column("Repetir",  width=90,  anchor="center", stretch=False)

    # Scrollbar vertical
    sb = ttkb.Scrollbar(table_holder, orient="vertical", command=event_list.yview)
    event_list.configure(yscrollcommand=sb.set)

    # Colocación con grid dentro del holder
    event_list.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")

    # Botón dentro del mismo frame (abajo-izquierda)
    add_event_button = ttkb.Button(details_frame, text="➕ Agregar Evento", bootstyle="success-outline")
    add_event_button.grid(row=1, column=0, sticky="w", pady=(6, 0))

    return details_frame, event_list, add_event_button

__all__ = ["crear_tabla_eventos"]
