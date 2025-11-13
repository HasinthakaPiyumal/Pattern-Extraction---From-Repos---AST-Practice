# Cluster 3

def set_default_mpl():
    from matplotlib import cycler
    colors = cycler('color', ['#EE6666', '#3388BB', '#9988DD', '#EECC55', '#88BB44', '#FFBBBB'])
    plt.rc('axes', facecolor='#E6E6E6', edgecolor='none', axisbelow=True, grid=True, prop_cycle=colors)
    plt.rc('grid', color='w', linestyle='solid')
    plt.rc('xtick', direction='out', color='k')
    plt.rc('ytick', direction='out', color='k')
    plt.rc('patch', edgecolor='#E6E6E6')
    plt.rcParams.update({'font.size': 20})
    plt.rcParams.update({'xtick.labelsize': 15})
    plt.rcParams.update({'ytick.labelsize': 15})
    plt.rcParams.update({'axes.titlesize': 24})
    plt.rcParams.update({'axes.labelsize': 20})
    plt.rcParams.update({'lines.linewidth': 2})

