
# Reproductor con eventos

Proyecto desarrollado **a la medida** para una **iglesia local** en una residencial de la **zona 3 de Villa Nueva, Guatemala**.  
Se construyó pensando **principalmente en Windows**, pero **se desarrolló y probó en Linux**; por eso el repositorio incluye **ambas versiones** (carpetas `Windows/` y `Linux/`).

> Las dependencias están listadas en **`requirements.txt`**.

---

## ✨ ¿Qué hace?

- **Playlist** de pistas (`.mp3`, `.wav`) con **Nombre, Duración y Ruta**.
- **Explorador** integrado: doble clic agrega a la playlist.
- **Programación de eventos**: reproducir a una hora dada o con **repetición** (intervalos).
- **Prioridad de eventos** sobre la reproducción normal; al terminar, vuelve a la playlist.
- **Controles**: Play / Pausa / Stop / Siguiente + **barra de progreso**.
- **Modos**: Orden / Aleatorio (sin repetir hasta agotar).
- **Persistencia**: guarda/carga **estado** y **playlist** (`.pkl`).

---

## 📦 Requisitos

- **Python 3.12+**
- Instalar dependencias:
  ```bash
  pip install -r requirements.txt
* En **Linux**, además:

  ```bash
  sudo apt install python3-tk
  ```

---

## ▶️ Ejecutar en desarrollo

### Windows

```powershell
cd Windows
python main.py
```

### Linux

```bash
cd Linux
python3 main.py
```

> **Nota DnD (Linux):**
> En **Xorg** el arrastrar/soltar funciona con `tkinterdnd2`.
> En **Wayland (GNOME)**, por limitación de Tk + XWayland, el DnD desde Nautilus no llega. Usar **Ctrl+V** (copiar en Nautilus → pegar en la app) o los botones de “Agregar archivos/carpeta”.

---

## 🛠️ Empaquetado “one-file” (PyInstaller)

> Los comandos incluyen los recursos de `tkinterdnd2`/`ttkbootstrap` y corrigen módulos de Pillow para los temas.

### Windows (EXE)

```powershell
cd Windows
pyinstaller -F -w main.py `
  --name Reproductor `
  --icon image.ico `
  --collect-data tkinterdnd2 `
  --collect-data ttkbootstrap `
  --hidden-import PIL.Image `
  --hidden-import PIL.ImageTk `
  --hidden-import PIL._tkinter_finder `
  --add-data "image.ico;."
```

### Linux (ELF)

```bash
cd Linux
pyinstaller -F -w main.py \
  --name Reproductor \
  --collect-data tkinterdnd2 \
  --collect-data ttkbootstrap \
  --hidden-import PIL.Image \
  --hidden-import PIL.ImageTk \
  --hidden-import PIL._tkinter_finder \
  --add-data "image.ico:."
```

> En Linux, el **icono del ejecutable** se maneja vía `.desktop` (no se “inyecta” en el binario como en Windows).

---

## 🧱 Estructura

```
.
├── Linux/
│   ├── main.py
│   ├── image.ico
│   ├── gui/                # layout, estilos, tablas, dnd, etc.
│   └── utils/              # player, playlist, eventos, estado, programación
├── Windows/
│   ├── main.py
│   ├── image.ico
│   ├── gui/
│   └── utils/
└── requirements.txt
```

---

## 🔎 Detalles técnicos

* La playlist guarda cada fila como `values = (nombre, duración, ruta)`; el reproductor carga desde `values[2]`.
* Los eventos contienen `archivo`, `hora_inicio` y `intervalo_repeticion`; un **loop** verifica cada \~1s y dispara puntualmente.
* `pygame` maneja reproducción y **fade**; el estado global vive en `utils/player_state.py`.

---

## ⚠️ Limitaciones conocidas

* **Wayland (GNOME):** DnD de Nautilus → Tk no funciona (limitación de plataforma). Usar **Ctrl+V** o diálogos de archivo.
* Formatos soportados por defecto: **.mp3** y **.wav** (se amplía en `utils/playlist.py`).

---

## 🙏 Créditos

Desarrollado por **El Güiro Tech**.
Hecho especialmente para el uso de una iglesia local en la **zona 3 de Villa Nueva, Guatemala**.



