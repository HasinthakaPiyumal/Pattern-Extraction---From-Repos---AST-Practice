# Cluster 29

def create_pb(playback_settings, **kwargs):
    playback_type = playback_settings.playback_type
    if playback_type == 'none':
        return NullPB(None)
    elif playback_type == 'by_video':
        return VideoPB(playback_settings['by_video'], **kwargs)
    elif playback_type == 'by_frame':
        return FramePB(playback_settings['by_frame'], **kwargs)
    elif playback_type == 'by_action':
        return ActionPB(playback_settings['by_action'], **kwargs)
    else:
        raise NotImplementedError

