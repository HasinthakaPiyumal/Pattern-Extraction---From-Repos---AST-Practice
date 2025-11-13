# Cluster 2

def plot_map(df):
    """Generates a map using the state counts. You will require to download
    the following file and extract its contents to a folder named: mexicostates

    https://www.arcgis.com/home/item.html?id=ac9041c51b5c49c683fbfec61dc03ba8

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """
    mexico_df = geopandas.read_file('./mexicostates')
    for state in STATES:
        clean_name = clean_word(state)
        if clean_name == 'Ciudad de Mexico':
            clean_name = 'Distrito Federal'
        elif clean_name == 'Estado de Mexico':
            clean_name = 'Mexico'
        mexico_df.loc[mexico_df['ADMIN_NAME'] == clean_name, 'count'] = len(df[df['text_lower'] == state.lower()])
    plt.rcParams['figure.figsize'] = [12, 8]
    mexico_df.plot(column='count', cmap='plasma', legend=True)
    plt.title('Mentions by State')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('map.png', facecolor='#5C0E10')

