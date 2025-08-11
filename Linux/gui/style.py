from ttkbootstrap.style import Style

def apply_style(root):
    style = Style()  # Ya está aplicado en la ventana por themename, pero podés hacer override

    # 🎧 Treeview estilo personalizado
    style.configure("Treeview",
        font=("JetBrains Mono", 10),
        rowheight=25
    )
    style.map("Treeview",
        background=[("selected", "#0a84ff")],
        foreground=[("selected", "#ffffff")]
    )

    # Botones personalizados (si no usás bootstyle en todos)
    style.configure("TButton",
        font=("JetBrains Mono", 10, "bold"),
        padding=5
    )

    # ComboBox
    style.configure("TCombobox",
        font=("JetBrains Mono", 10)
    )

    # Fondo base
    root.configure(bg=style.colors.bg)  # o usá un color directo: "#101010"
