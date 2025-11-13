# Cluster 15

def spectrum_magnitude(frames, NFFT):
    """Apply FFT and Calculate magnitude of the spectrum.
    Args:
        frames: 2-D frames array calculated by audio2frame(...).
        NFFT:FFT size.
    Returns:
        Return magnitude of the spectrum after FFT, with shape (frames_num, NFFT).
    """
    complex_spectrum = numpy.fft.rfft(frames, NFFT)
    return numpy.absolute(complex_spectrum)

