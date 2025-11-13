# Cluster 14

def audio2frame(signal, frame_length, frame_step, winfunc=lambda x: numpy.ones((x,))):
    """ Framing audio signal. Uses numbers of samples as unit.

    Args:
    signal: 1-D numpy array.
	frame_length: In this situation, frame_length=samplerate*win_length, since we
        use numbers of samples as unit.
    frame_step:In this situation, frame_step=samplerate*win_step,
        representing the number of samples between the start point of adjacent frames.
	winfunc:lambda function, to generate a vector with shape (x,) filled with ones.

    Returns:
        frames*win: 2-D numpy array with shape (frames_num, frame_length).
    """
    signal_length = len(signal)
    frame_length = int(round(frame_length))
    frame_step = int(round(frame_step))
    if signal_length <= frame_length:
        frames_num = 1
    else:
        frames_num = 1 + int(math.ceil((1.0 * signal_length - frame_length) / frame_step))
    pad_length = int((frames_num - 1) * frame_step + frame_length)
    zeros = numpy.zeros((pad_length - signal_length,))
    pad_signal = numpy.concatenate((signal, zeros))
    indices = numpy.tile(numpy.arange(0, frame_length), (frames_num, 1)) + numpy.tile(numpy.arange(0, frames_num * frame_step, frame_step), (frame_length, 1)).T
    indices = numpy.array(indices, dtype=numpy.int32)
    frames = pad_signal[indices]
    win = numpy.tile(winfunc(frame_length), (frames_num, 1))
    return frames * win

def deframesignal(frames, signal_length, frame_length, frame_step, winfunc=lambda x: numpy.ones((x,))):
    """定义函数对原信号的每一帧进行变换，应该是为了消除关联性
    参数定义：
    frames:audio2frame函数返回的帧矩阵
    signal_length:信号长度
    frame_length:帧长度
    frame_step:帧间隔
    winfunc:对每一帧加window函数进行分析，默认此处不加window
    """
    signal_length = round(signal_length)
    frame_length = round(frame_length)
    frames_num = numpy.shape(frames)[0]
    assert numpy.shape(frames)[1] == frame_length, '"frames"矩阵大小不正确，它的列数应该等于一帧长度'
    indices = numpy.tile(numpy.arange(0, frame_length), (frames_num, 1)) + numpy.tile(numpy.arange(0, frames_num * frame_step, frame_step), (frame_length, 1)).T
    indices = numpy.array(indices, dtype=numpy.int32)
    pad_length = (frames_num - 1) * frame_step + frame_length
    if signal_length <= 0:
        signal_length = pad_length
    recalc_signal = numpy.zeros((pad_length,))
    window_correction = numpy.zeros((pad_length, 1))
    win = winfunc(frame_length)
    for i in range(0, frames_num):
        window_correction[indices[i, :]] = window_correction[indices[i, :]] + win + 1e-15
        recalc_signal[indices[i, :]] = recalc_signal[indices[i, :]] + frames[i, :]
    recalc_signal = recalc_signal / window_correction
    return recalc_signal[0:signal_length]

def calcfeat_delta_delta(signal, samplerate=16000, win_length=0.025, win_step=0.01, filters_num=26, NFFT=512, low_freq=0, high_freq=None, pre_emphasis_coeff=0.97, cep_lifter=22, appendEnergy=True, mode='mfcc', feature_len=13):
    """Calculate features, fist order difference, and second order difference coefficients.
        13 Mel-Frequency Cepstral Coefficients(MFCC), 13 first order difference
       coefficients, and 13 second order difference coefficients. There are 39 features
       in total.

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
        2-D numpy array with shape:(NUMFRAMES, 39). In each frame, coefficients are
            concatenated in (feature, delta features, delta delta feature) way.
    """
    filters_num = 2 * feature_len
    feat = calcMFCC(signal, samplerate, win_length, win_step, feature_len, filters_num, NFFT, low_freq, high_freq, pre_emphasis_coeff, cep_lifter, appendEnergy, mode=mode)
    feat_delta = delta(feat)
    feat_delta_delta = delta(feat_delta)
    result = numpy.concatenate((feat, feat_delta, feat_delta_delta), axis=1)
    return result

def lifter(cepstra, L=22):
    """Lifter function.
    Args:
        cepstra: MFCC coefficients.
        L: Numbers of lifters. Defaulted to 22.
    """
    if L > 0:
        nframes, ncoeff = numpy.shape(cepstra)
        n = numpy.arange(ncoeff)
        lift = 1 + L / 2 * numpy.sin(numpy.pi * n / L)
        return lift * cepstra
    else:
        return cepstra

