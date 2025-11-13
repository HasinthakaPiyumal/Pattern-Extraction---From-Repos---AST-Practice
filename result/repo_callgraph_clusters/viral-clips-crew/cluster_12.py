# Cluster 12

def main(yt_vid_url, mp4_dir_save_path, srt_dir_save_path, txt_dir_save_path):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    yt_video_id = extract_video_id(yt_vid_url)
    transcript = YouTubeTranscriptApi.get_transcript(yt_video_id)
    yt_vid_url_to_mp4(yt_vid_url, mp4_dir_save_path)
    yt_vid_id_to_srt(transcript, yt_video_id, srt_dir_save_path)
    yt_vid_id_to_txt(transcript, yt_video_id, txt_dir_save_path)

