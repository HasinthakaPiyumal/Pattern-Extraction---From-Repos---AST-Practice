# Cluster 9

def set_labels(axes, title=None, xlabel=None, ylabel=None, x_labels=None, y_labels=None, x_tick_params=None, y_tick_params=None, legend_title=None):
    axes.set_title('' if not title else title, fontsize='xx-large')
    axes.set_xlabel('' if not xlabel else xlabel, fontsize='x-large')
    axes.set_ylabel('' if not ylabel else ylabel, fontsize='x-large')
    if not x_tick_params:
        x_tick_params = {}
    if not y_tick_params:
        y_tick_params = {}
    axes.tick_params(axis='x', labelsize='x-large', **x_tick_params)
    axes.tick_params(axis='y', labelsize='x-large', **y_tick_params)
    if x_labels is not None:
        axes.set_xticklabels(x_labels)
    if y_labels is not None:
        axes.set_yticklabels(y_labels)
    legend = axes.get_legend()
    if legend:
        legend_title = legend_title or legend.get_title().get_text()
        legend.set_title(legend_title, prop=dict(size='x-large'))
        for text in legend.get_texts():
            text.set_fontsize('x-large')

