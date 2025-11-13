# Cluster 46

def get_cropper():
    return cropping.ScrollingCropper(rows=5, cols=5, to_track=PLAYER, pad_char=BACKGROUND, scroll_margins=(2, 2))

