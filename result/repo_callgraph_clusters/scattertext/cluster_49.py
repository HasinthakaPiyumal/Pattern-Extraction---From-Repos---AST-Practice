# Cluster 49

def iter_party_speech_pairs():
    for speaker_obj in convention_speech_iter():
        political_party = speaker_obj['name']
        for speech in speaker_obj['speeches']:
            yield (political_party, speech)

