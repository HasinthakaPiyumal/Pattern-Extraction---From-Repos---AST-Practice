# Cluster 17

def calcMFCC(signal, samplerate=16000, win_length=0.025, win_step=0.01, feature_len=13, filters_num=26, NFFT=512, low_freq=0, high_freq=None, pre_emphasis_coeff=0.97, cep_lifter=22, appendEnergy=True, mode='mfcc'):
    """Caculate Features.
    Args:
        signal: 1-D numpy array.
        samplerate: Sampling rate. Defaulted to 16KHz.
        win_length: Window length. Defaulted to 0.025, which is 25ms/frame.
        win_step: Interval between the start points of adjacent frames.
            Defaulted to 0.01, which is 10ms.
        feature_len: Numbers of features. Defaulted to 13.
        filters_num: Numbers of filters. Defaulted to 26.
        NFFT: Size of FFT. Defaulted to 512.
        low_freq: Lowest frequency.
        high_freq: Highest frequency.
        pre_emphasis_coeff: Coefficient for pre-emphasis. Pre-emphasis increase
            the energy of signal at higher frequency. Defaulted to 0.97.
        cep_lifter: Numbers of lifter for cepstral. Defaulted to 22.
        appendEnergy: Wheter to append energy. Defaulted to True.
        mode: 'mfcc' or 'fbank'.
            'mfcc': Mel-Frequency Cepstral Coefficients(MFCC).
                    Complete process: Mel filtering -> log -> DCT.
            'fbank': Apply Mel filtering -> log.

    Returns:
        2-D numpy array with shape (NUMFRAMES, features). Each frame containing feature_len of features.
    """
    filters_num = 2 * feature_len
    feat, energy = fbank(signal, samplerate, win_length, win_step, filters_num, NFFT, low_freq, high_freq, pre_emphasis_coeff)
    feat = numpy.log(feat)
    if mode == 'mfcc':
        feat = dct(feat, type=2, axis=1, norm='ortho')[:, :feature_len]
        feat = lifter(feat, cep_lifter)
    elif mode == 'fbank':
        feat = feat[:, :feature_len]
    if appendEnergy:
        feat[:, 0] = numpy.log(energy)
    return feat

def log_fbank(signal, samplerate=16000, win_length=0.025, win_step=0.01, filters_num=26, NFFT=512, low_freq=0, high_freq=None, pre_emphasis_coeff=0.97):
    """Calculate log of features.
    """
    feat, energy = fbank(signal, samplerate, win_length, win_step, filters_num, NFFT, low_freq, high_freq, pre_emphasis_coeff)
    return numpy.log(feat)

