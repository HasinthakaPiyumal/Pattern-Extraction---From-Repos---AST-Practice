# Cluster 44

def audio_data_to_numpy(audio_data, sr=16000):
    audio_array, sr0 = audio_data
    scale = np.iinfo(audio_array.dtype).max if audio_array.dtype in [np.int16, np.int32] else 1.0
    ret = librosa.resample(y=audio_array.astype(np.float32) / scale, orig_sr=sr0, target_sr=sr)
    return ret

