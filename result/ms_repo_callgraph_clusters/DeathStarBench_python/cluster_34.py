# Cluster 34

def thumbnailId(video_id: str):
    if '.' in video_id:
        img_id = video_id.rsplit('.', 1)[0]
        if img_id == '':
            img_id = video_id
    else:
        img_id = video_id
    return 'tn-%s.jpeg' % img_id

# Node: rsplit
