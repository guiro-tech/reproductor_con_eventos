import os
from gui import tree
from utils import populate_tree, on_open_node, add_to_playlist

def setup_explorer():
    """
    Inicializa el árbol del explorador con el directorio raíz del usuario (~),
    y conecta los eventos para explorar y agregar archivos con doble clic o Enter.
    """
    drive = os.path.expanduser('~/')
    node = tree.insert('', 'end', text=drive, open=False, values=[drive])
    populate_tree(tree, node, drive)

    tree.bind('<<TreeviewOpen>>', on_open_node)
    tree.bind('<Double-1>', lambda event: add_to_playlist([tree.item(tree.focus())['values'][0]]))
    tree.bind('<Return>', lambda event: add_to_playlist([tree.item(tree.focus())['values'][0]]))

