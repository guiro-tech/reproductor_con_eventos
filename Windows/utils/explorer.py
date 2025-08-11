import os
from utils.playlist import add_to_playlist

allowed_extensions = ['.mp3', '.wav']

def populate_tree(tree_widget, parent, path):
    try:
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                node = tree_widget.insert(parent, 'end', text=item, open=False, values=[full_path])
                # marcador hijo para que muestre triángulo de expandir
                tree_widget.insert(node, 'end')
            elif os.path.isfile(full_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in allowed_extensions:
                    tree_widget.insert(parent, 'end', text=item, values=[full_path])
    except PermissionError:
        pass

def on_open_node(event):
    tree_widget = event.widget
    node = tree_widget.focus()
    tree_widget.delete(*tree_widget.get_children(node))
    path = tree_widget.item(node, "values")[0]
    populate_tree(tree_widget, node, path)

def on_tree_double_click(event, tree_widget, playlist):
    # fila bajo el cursor
    item_id = tree_widget.identify_row(event.y)
    if not item_id:
        return
    vals = tree_widget.item(item_id, "values")
    if not vals:
        return
    path = vals[0]

    # si es carpeta, expándela con doble click
    if os.path.isdir(path):
        tree_widget.item(item_id, open=not tree_widget.item(item_id, "open"))
        # si no se había poblado aún, poblarla ahora
        if not tree_widget.get_children(item_id):
            populate_tree(tree_widget, item_id, path)
        return

    # si es archivo de audio compatible, agregarlo a la playlist
    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_extensions:
        add_to_playlist([path], playlist)

def setup_explorer(tree_widget, playlist):
    root_path = os.path.expanduser("~")
    # raíz visible como Home
    tree_widget.delete(*tree_widget.get_children())
    root_node = tree_widget.insert('', 'end', text=os.path.basename(root_path) or root_path, values=[root_path], open=False)
    tree_widget.insert(root_node, 'end')  # marcador
    # binds
    tree_widget.bind('<<TreeviewOpen>>', on_open_node)
    tree_widget.bind('<Double-1>', lambda e: on_tree_double_click(e, tree_widget, playlist))
