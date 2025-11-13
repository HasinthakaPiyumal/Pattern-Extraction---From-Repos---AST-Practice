# Cluster 19

def format_col_str(col):
    suffix = '(FK)' if col.name in fk_col_names else '(PK)' if col.name in pk_col_names else ''
    if show_datatypes:
        return '- %s : %s' % (col.name + suffix, format_col_type(col))
    else:
        return '- %s' % (col.name + suffix)

