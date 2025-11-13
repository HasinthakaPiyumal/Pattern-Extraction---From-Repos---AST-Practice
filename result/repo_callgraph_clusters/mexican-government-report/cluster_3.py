# Cluster 3

def plot_donut(df):
    """Generates a donut plot with the counts of 3 categories.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """
    labels = ['Positivo', 'Negativo', 'Neutro']
    positive = len(df[df['score'] > 0])
    negative = len(df[df['score'] < 0])
    neutral = len(df[df['score'] == 0])
    values = [positive, negative, neutral]
    colors = ['green', 'orange', 'yellow']
    explode = (0, 0, 0)
    plt.rcParams['font.size'] = 18
    plt.rcParams['legend.fontsize'] = 20
    plt.pie(values, explode=explode, labels=None, colors=colors, autopct='%1.1f%%', shadow=False)
    centre_circle = plt.Circle((0, 0), 0.75, color='#5C0E10', fc='#5C0E10', linewidth=0)
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.axis('equal')
    plt.legend(labels)
    plt.savefig('donut.png', facecolor='#5C0E10')

