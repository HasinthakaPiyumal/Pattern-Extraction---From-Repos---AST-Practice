# Cluster 11

def extract_video_id(yt_vid_url):
    pattern = '(?:https?:\\/\\/)?(?:www\\.)?(?:youtube\\.com\\/(?:watch\\?v=|embed\\/|v\\/)|youtu\\.be\\/|youtube\\.com\\/shorts\\/)([a-zA-Z0-9_-]{11})(?:\\S+)?'
    match = re.search(pattern, yt_vid_url)
    if match:
        return match.group(1)
    else:
        return None

