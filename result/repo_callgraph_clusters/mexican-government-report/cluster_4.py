# Cluster 4

def get_word_counts(df):
    """Gets the total word count and the total unique lemmas.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be analyzed.

    """
    df.loc[df['lemma_lower'] == 'programa', 'lemma_lower'] = 'programar'
    words = df[df['is_alphabet'] == True]['text_lower'].count()
    print('Words:', words)
    unique_words = df[df['is_alphabet'] == True]['lemma_lower'].nunique()
    print('Unique words:', unique_words)

def get_entity_counts(df):
    """Gets the number of counts per entity.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be analyzed.

    """
    entities = df['label'].value_counts()
    print(entities)
    locations = df[df['label'] == 'ORG']['text'].value_counts()
    print(locations)

