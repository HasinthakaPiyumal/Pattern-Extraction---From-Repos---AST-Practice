# Cluster 41

def save_video(name: str, frame_list: List[np.array], fps: int):
    """Requres cv2"""
    import cv2
    video_name = name + '.mp4'
    video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_list[0].shape[1], frame_list[0].shape[0]))
    for img in frame_list:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        video.write(img)
    video.release()

