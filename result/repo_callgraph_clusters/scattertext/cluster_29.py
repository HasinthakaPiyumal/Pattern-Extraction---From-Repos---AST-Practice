# Cluster 29

def produce_scattertext_pyplot(scatterplot_structure, figsize=(15, 7), textsize=7, distance_margin_fraction=0.009, scatter_size=5, cmap='RdYlBu', sample=0, xlabel=None, ylabel=None, dpi=300, draw_lines=False, linecolor='k', draw_all=False, nbr_candidates=0):
    """
    Parameters
    ----------
    scatterplot_structure : ScatterplotStructure
    figsize : Tuple[int,int]
        Size of ouput pyplot figure
    textsize : int
        Size of text terms in plot
    distance_margin_fraction : float
        Fraction of the 2d space to use as margins for text bboxes
    scatter_size : int
        Size of scatter disks
    cmap : str
        Matplotlib compatible colormap
    sample : int
        if >0 samples a subset from the scatterplot_structure, used for testing
    xlabel : str
        Overrides label from scatterplot_structure
    ylabel : str
        Overrides label from scatterplot_structure
    dpi : int
        Pyplot figure resolution

    Returns
    -------
    matplotlib.figure.Figure
    matplotlib figure that can be used with plt.show() or plt.savefig()

    """
    return pyplot_from_scattertext_structure(scatterplot_structure, figsize=figsize, textsize=textsize, distance_margin_fraction=distance_margin_fraction, scatter_size=scatter_size, cmap=cmap, sample=sample, xlabel=xlabel, ylabel=ylabel, dpi=dpi, draw_lines=draw_lines, linecolor=linecolor, draw_all=draw_all, nbr_candidates=nbr_candidates)

