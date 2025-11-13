# Cluster 7

def transcribe_main(file):
    plain = True
    srt = True
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = whisper.load_model('medium.en').to(DEVICE)
    result, transcript, subtitles = transcribe_file(model, srt, plain, file)
    return (transcript, subtitles)

