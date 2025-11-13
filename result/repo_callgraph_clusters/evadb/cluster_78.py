# Cluster 78

def gen_sample_input(input_type: HFInputTypes):
    if input_type == HFInputTypes.TEXT:
        return sample_text()
    elif input_type == HFInputTypes.IMAGE:
        return sample_image()
    elif input_type == HFInputTypes.AUDIO:
        return sample_audio()
    assert False, 'Invalid Input Type for Function'

