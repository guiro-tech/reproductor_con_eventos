import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from utils.playlist import get_duration

__all__ = ["open_event_window", "eventos"]

# Lista compartida que usa el player
eventos = []

def open_event_window(root, event_list):
    def agregar_evento():
        nonlocal evento_nombre, evento_hora, evento_minuto, evento_segundo
        nonlocal repetir_tipo, intervalo_repeticion, evento_archivo

        nombre_evento = (evento_nombre.get() or "").strip()
        archivo_evento = evento_archivo["text"].strip()

        # Validaciones básicas
        if not archivo_evento:
            messagebox.showerror("Error", "Selecciona un archivo de música.")
            return
        if not os.path.isfile(archivo_evento):
            messagebox.showerror("Error", "El archivo seleccionado no existe.")
            return

        try:
            hora = int(evento_hora.get())
            minuto = int(evento_minuto.get())
            segundo = int(evento_segundo.get())
        except Exception:
            messagebox.showerror("Error", "Hora inválida.")
            return

        tipo_repeticion = repetir_tipo.get()  # "Horas" | "Minutos" | "Segundos" | "Una sola vez"

        # Construir fecha/hora objetivo (hoy a la hora indicada; si ya pasó, se programa para mañana)
        ahora = datetime.now()
        evento_programado = ahora.replace(hour=hora, minute=minuto, second=segundo, microsecond=0)
        if evento_programado < ahora:
            evento_programado += timedelta(days=1)

        # Intervalo (en segundos) si aplica
        intervalo = None
        if tipo_repeticion in ("Horas", "Minutos", "Segundos"):
            try:
                n = int(intervalo_repeticion.get())
                if n <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Error", "Intervalo inválido (usa números enteros > 0).")
                return
            if tipo_repeticion == "Horas":
                intervalo = n * 3600
            elif tipo_repeticion == "Minutos":
                intervalo = n * 60
            else:
                intervalo = n

        # Guardar en la lista interna que consume el player
        eventos.append({
            "nombre": nombre_evento or os.path.basename(archivo_evento),
            "hora_inicio": evento_programado,
            "intervalo_repeticion": intervalo,   # None si es una sola vez
            "archivo": archivo_evento,
        })

        # Pintar en la tabla visual con 4 columnas: Pista | Tiempo | Duración | Repetir
        file_name = os.path.basename(archivo_evento)
        file_duration, _ = get_duration(archivo_evento)
        if intervalo:
            # Mostrar el texto coherente con la unidad elegida
            if tipo_repeticion == "Horas":
                rep_text = f"Cada {intervalo // 3600} Horas"
            elif tipo_repeticion == "Minutos":
                rep_text = f"Cada {intervalo // 60} Minutos"
            else:
                rep_text = f"Cada {intervalo} Segundos"
        else:
            rep_text = "Una sola vez"

        # LOG: evento programado (cuánto falta)
        tiempo_restante = evento_programado - datetime.now()
        print(
            "[EVENTO] Programado:",
            f"'{(nombre_evento or os.path.basename(archivo_evento))}'",
            "para",
            evento_programado.strftime("%Y-%m-%d %H:%M:%S"),
            f"(en {str(tiempo_restante).split('.')[0]})"
        )

        event_list.insert(
            "",
            "end",
            values=(file_name, evento_programado.strftime("%H:%M:%S"), file_duration, rep_text)
        )

        event_window.destroy()

    def seleccionar_archivo_evento():
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos de música", "*.mp3 *.wav")]
        )
        if archivo:
            evento_archivo.config(text=archivo)

    # --- UI de la ventana de eventos ---
    event_window = tk.Toplevel(root)
    event_window.title("Agregar Evento")
    event_window.resizable(False, False)

    # Prefills con hora actual
    ahora = datetime.now()

    # Nombre
    tk.Label(event_window, text="Nombre del Evento:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    evento_nombre = tk.Entry(event_window, width=32)
    evento_nombre.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="w")

    # Hora / Min / Seg
    tk.Label(event_window, text="Hora:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    evento_hora = ttk.Combobox(event_window, values=[f"{i:02d}" for i in range(24)], width=5, state="readonly")
    evento_hora.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    evento_hora.set(f"{ahora.hour:02d}")

    tk.Label(event_window, text="Minuto:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
    evento_minuto = ttk.Combobox(event_window, values=[f"{i:02d}" for i in range(60)], width=5, state="readonly")
    evento_minuto.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    evento_minuto.set(f"{ahora.minute:02d}")

    tk.Label(event_window, text="Segundo:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
    evento_segundo = ttk.Combobox(event_window, values=[f"{i:02d}" for i in range(60)], width=5, state="readonly")
    evento_segundo.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    evento_segundo.set(f"{ahora.second:02d}")

    # Repetición
    tk.Label(event_window, text="Repetir cada:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
    intervalo_repeticion = tk.Entry(event_window, width=6)
    intervalo_repeticion.grid(row=4, column=1, padx=10, pady=5, sticky="w")

    repetir_tipo = ttk.Combobox(
        event_window,
        values=["Horas", "Minutos", "Segundos", "Una sola vez"],
        state="readonly",
        width=14
    )
    repetir_tipo.grid(row=4, column=2, padx=10, pady=5, sticky="w")
    repetir_tipo.set("Una sola vez")

    # Archivo
    tk.Label(event_window, text="Archivo:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
    evento_archivo = tk.Label(event_window, text="", relief="sunken", width=48, anchor="w")
    evento_archivo.grid(row=5, column=1, columnspan=2, padx=10, pady=5, sticky="w")

    btn_archivo = tk.Button(event_window, text="Seleccionar archivo", command=seleccionar_archivo_evento)
    btn_archivo.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="w")

    # Guardar
    btn_guardar_evento = tk.Button(event_window, text="Agregar Evento", command=agregar_evento)
    btn_guardar_evento.grid(row=7, column=0, columnspan=3, padx=10, pady=10)
