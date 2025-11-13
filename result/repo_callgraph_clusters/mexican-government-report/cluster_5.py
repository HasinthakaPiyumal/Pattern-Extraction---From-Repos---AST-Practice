# Cluster 5

def plot_most_used_words(df):
    """Generates a bar plot with the counts of the most used lemmas.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """
    df.loc[df['lemma_lower'] == 'programa', 'lemma_lower'] = 'programar'
    words = df[(df['is_alphabet'] == True) & (df['is_stopword'] == False) & (df['lemma_lower'].str.len() > 1)]['lemma_lower'].value_counts()[:20]
    sns.barplot(x=words.values, y=words.index, palette='Blues_d', linewidth=0)
    plt.xlabel('Occurrences Count')
    plt.title('Most Frequent Words')
    plt.savefig('words_counts.png', facecolor='#5C0E10')

def plot_sentiment_analysis(df):
    """Generates a bar plot with the sentiment scores of each sentence.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """
    df = df[(df['score'] <= 10) & (df['score'] >= -10)]
    colors = np.array([(0.811, 0.913, 0.145)] * len(df['score']))
    colors[df['score'] >= 0] = (0.529, 0.87, 0.972)
    yticks_labels = [str(i) for i in range(-12, 12, 2)]
    plt.yticks(np.arange(-12, 12, 2), yticks_labels)
    plt.bar(df.index, df['score'], color=colors, linewidth=0)
    plt.xlabel('Sentence Number')
    plt.ylabel('Score')
    plt.title('Sentiment Analysis')
    plt.savefig('sentiment_analysis.png', facecolor='#5C0E10')

