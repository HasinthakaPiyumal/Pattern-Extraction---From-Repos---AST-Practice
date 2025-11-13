# Cluster 138

def keyboard_handler(sender, key_code):
    """Handle keyboard events"""
    global selected_node_for_deletion
    if key_code == 68:
        delete_selected_node()

