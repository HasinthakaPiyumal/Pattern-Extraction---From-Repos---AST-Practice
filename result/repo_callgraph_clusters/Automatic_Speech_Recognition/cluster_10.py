# Cluster 10

def plotWaveform(audio):
    """
    Plotting the waveform of a wav file
    """
    spf = wave.open(audio, 'r')
    signal = spf.readframes(-1)
    signal = np.fromstring(signal, 'Int16')
    fs = spf.getframerate()
    if spf.getnchannels() == 2:
        print('Just mono files')
        sys.exit(0)
    Time = np.linspace(0, len(signal) / fs, num=len(signal))
    plt.figure(1)
    plt.title('Waveform of an audio')
    plt.plot(Time, signal)
    plt.show()

def get_filter_banks(filters_num=20, NFFT=512, samplerate=16000, low_freq=0, high_freq=None):
    """Calculate Mel filter banks.
    Args:
        filters_num: Numbers of Mel filters.
        NFFT:FFT size. Defaulted to 512.
        samplerate: Sampling rate. Defaulted to 16KHz.
        low_freq: Lowest frequency.
        high_freq: Highest frequency.
    """
    low_mel = hz2mel(low_freq)
    high_mel = hz2mel(high_freq)
    mel_points = numpy.linspace(low_mel, high_mel, filters_num + 2)
    hz_points = mel2hz(mel_points)
    bin = numpy.floor((NFFT + 1) * hz_points / samplerate)
    fbank = numpy.zeros([filters_num, NFFT // 2 + 1])
    for j in xrange(0, filters_num):
        for i in xrange(int(bin[j]), int(bin[j + 1])):
            fbank[j, i] = (i - bin[j]) / (bin[j + 1] - bin[j])
        for i in xrange(int(bin[j + 1]), int(bin[j + 2])):
            fbank[j, i] = (bin[j + 2] - i) / (bin[j + 2] - bin[j + 1])
    return fbank

