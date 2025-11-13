# Cluster 1

def get_state_counts(df):
    """Gets the number of counts per state.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be analyzed.

    """
    total_count = 0
    state_counts = list()
    for state in STATES:
        state_count = len(df[df['text_lower'] == state.lower()])
        state_counts.append([state, state_count])
        total_count += state_count
    state_counts.sort(key=lambda x: x[1])
    print(state_counts)
    print(total_count)

def get_tokens(doc):
    """Get the tokens and save them to .csv

    Parameters
    ----------
    doc : spacy.doc
        A doc object.

    """
    data_list = [['text', 'text_lower', 'lemma', 'lemma_lower', 'part_of_speech', 'is_alphabet', 'is_stopword']]
    for token in doc:
        data_list.append([token.text, token.lower_, token.lemma_, token.lemma_.lower(), token.pos_, token.is_alpha, token.is_stop])
    with open('./tokens.csv', 'w', encoding='utf-8', newline='') as tokens_file:
        csv.writer(tokens_file).writerows(data_list)

def get_entities(doc):
    """Get the entities and save them to .csv

    Parameters
    ----------
    doc : spacy.doc
        A doc object.

    """
    data_list = [['text', 'text_lower', 'label']]
    for ent in doc.ents:
        data_list.append([ent.text, ent.lower_, ent.label_])
    with open('./entities.csv', 'w', encoding='utf-8', newline='') as entities_file:
        csv.writer(entities_file).writerows(data_list)

def get_sentences(doc):
    """Get the sentences, score and save them to .csv

    You will require to download the dataset (zip) from the following url:

    https://www.kaggle.com/rtatman/sentiment-lexicons-for-81-languages

    Once downloaded you will require to extract 2 .txt files:

    negative_words_es.txt
    positive_words_es.txt

    Parameters
    ----------
    doc : spacy.doc
        A doc object.

    """
    with open('positive_words_es.txt', 'r', encoding='utf-8') as temp_file:
        positive_words = temp_file.read().splitlines()
    with open('negative_words_es.txt', 'r', encoding='utf-8') as temp_file:
        negative_words = temp_file.read().splitlines()
    data_list = [['text', 'score']]
    for sent in doc.sents:
        if len(sent.text) > 10:
            score = 0
            for word in sent:
                if word.lower_ in positive_words:
                    score += 1
                if word.lower_ in negative_words:
                    score -= 1
            data_list.append([sent.text, score])
    with open('./sentences.csv', 'w', encoding='utf-8', newline='') as sentences_file:
        csv.writer(sentences_file).writerows(data_list)

