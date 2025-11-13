# Cluster 9

def process_video_and_subtitles(video_path, subtitle_path, output_folder):
    """
    Full processing of video and subtitles.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    adjusted_subtitle_path = os.path.join(output_folder, base_name + '_adjusted.srt')
    utf8_subtitle_path = os.path.join(output_folder, base_name + '_utf8.srt')
    output_video_path = os.path.join(output_folder, base_name + '_subtitled.mp4')
    adjust_subtitle_timing(subtitle_path, adjusted_subtitle_path)
    convert_to_utf8(adjusted_subtitle_path, utf8_subtitle_path)
    burn_subtitles(video_path, utf8_subtitle_path, output_video_path)
    os.remove(adjusted_subtitle_path)
    os.remove(utf8_subtitle_path)
    logging.info('Temporary subtitle files removed.')

def process_video(input_video, subtitle_file_path, output_folder, aspect_ratio_choice):
    logging.info('~~~CLIPPER: PROCESSING VIDEO~~~')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    with open(subtitle_file_path, 'r') as file:
        subtitles_content = file.read()
    assert subtitles_content != '', 'clipper.py received an empty subtitles file'
    timestamps = re.findall('\\d{2}:\\d{2}:\\d{2},\\d{3}', subtitles_content)
    if not timestamps:
        logging.warning('No timestamps found in the subtitles.')
        return
    start_time = convert_timestamp(timestamps[0])
    end_time = convert_timestamp(timestamps[-1])
    logging.info(f'Extracted Start Time: {start_time}')
    logging.info(f'Extracted End Time: {end_time}')
    start_datetime = parse_timestamp(start_time)
    end_datetime = parse_timestamp(end_time)
    duration = end_datetime - start_datetime
    duration_seconds = duration.total_seconds()
    logging.info(f'Calculated Duration: {duration_seconds:.2f} seconds')
    if duration_seconds < 30:
        logging.warning(f'Video fragment duration ({duration_seconds:.2f} seconds) is less than 30 seconds. Skipping this subtitle file.')
        return
    if duration_seconds > 150:
        logging.warning(f'Video fragment duration ({duration_seconds:.2f} seconds) exceeds 2 minutes 30 seconds. Skipping this subtitle file.')
        return
    subtitle_base_name = os.path.splitext(os.path.basename(subtitle_file_path))[0]
    output_video_path = os.path.join(output_folder, f'{subtitle_base_name}_trimmed.mp4')
    logging.info(f'Output path: {output_video_path}')
    try:
        probe = ffmpeg.probe(input_video)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        logging.info(f'Video Width: {width}, Video Height: {height}')
        input_stream = ffmpeg.input(input_video, ss=start_time, t=duration_seconds)
        if aspect_ratio_choice == '2':
            if width > height:
                crop_size = height
                x_offset = (width - crop_size) // 2
                y_offset = 0
            else:
                crop_size = width
                x_offset = 0
                y_offset = (height - crop_size) // 2
            video = input_stream.video.filter('crop', crop_size, crop_size, x_offset, y_offset)
        else:
            video = input_stream.video
        audio = input_stream.audio
        output = ffmpeg.output(video, audio, output_video_path, vcodec='libx264', acodec='aac', audio_bitrate='192k', **{'vsync': 'vfr'})
        ffmpeg.run(output, overwrite_output=True)
        logging.info(f'Trimmed video saved to {output_video_path}')
    except ffmpeg.Error as e:
        logging.error(f'ffmpeg error: {str(e)}')

