# Cluster 36

def strip(txt: str) -> str:
    translation_table = str.maketrans('', '', string.whitespace)
    return txt.translate(translation_table)

