# Cluster 39

def clean_ax(this_ax: plt.Axes) -> plt.Axes:
    """
    Standardizes the matplotlib axes for better visualization.
    :param this_ax: Default axes.
    :return: Standardized axes.
    """
    this_ax.get_xaxis().tick_bottom()
    this_ax.get_yaxis().tick_left()
    this_ax.spines['top'].set_visible(False)
    this_ax.spines['bottom'].set_visible(False)
    this_ax.spines['right'].set_visible(False)
    this_ax.spines['left'].set_visible(False)
    return this_ax

