# gui/explorador.py
import ttkbootstrap as ttkb

def crear_explorador(root, *, row=0, column=0, sticky="nsew", padx=10, pady=10):
    frame_explorer = ttkb.Frame(root)
    frame_explorer.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)

    tree = ttkb.Treeview(frame_explorer, height=10)
    tree.heading('#0', text='📁 Explorador', anchor='w')
    tree.pack(side="left", fill="both", expand=True)

    vsb = ttkb.Scrollbar(frame_explorer, orient="vertical", command=tree.yview)
    vsb.pack(side="right", fill="y")
    tree.configure(yscrollcommand=vsb.set)

    return frame_explorer, tree
