# Cluster 10

def burn_subtitles(video_path, subtitle_path, output_video_path):
    """
    Uses ffmpeg to burn subtitles into the video.
    """
    cmd = ['ffmpeg', '-i', video_path, '-vf', f'subtitles={subtitle_path}', '-c:a', 'copy', output_video_path]
    try:
        subprocess.run(cmd, check=True)
        logging.info(f'Subtitles have been burned into the video: {output_video_path}')
    except subprocess.CalledProcessError as e:
        logging.error(f'Error burning subtitles: {e}')

def clean_whisper_output():
    whisper_output_folder = './whisper_output'
    for filename in os.listdir(whisper_output_folder):
        file_path = os.path.join(whisper_output_folder, filename)
        try:
            if os.path.isfile(file_path):
                send2trash(file_path)
                logging.info(f'Moved {file_path} to trash')
        except Exception as e:
            logging.error(f'Error while moving {file_path} to trash: {e}')

def move_files_to_trash(directory, exclude_files=None, file_extension=None):
    """
    Move files in the specified directory to trash, optionally excluding some files and filtering by extension.
    
    :param directory: The directory from which to move files to trash.
    :param exclude_files: A list of filenames to exclude from moving to trash.
    :param file_extension: If provided, only files with this extension will be moved to trash.
    """
    if exclude_files is None:
        exclude_files = []
    if not os.path.exists(directory):
        logging.error(f'Directory not found: {directory}')
        return
    for filename in os.listdir(directory):
        if filename not in exclude_files:
            if file_extension is None or filename.lower().endswith(file_extension.lower()):
                file_path = os.path.join(directory, filename)
                send2trash(file_path)
                logging.info(f'Moved to trash: {file_path}')

def local_whisper_process(input_folder, crew_output_folder, transcript=None, subtitles=None, transcribe_flag=True):
    for filename in os.listdir(input_folder):
        if filename.endswith('.mp4'):
            input_video_path = os.path.join(input_folder, filename)
            logging.info(f'Processing video: {input_video_path}')
            if transcribe_flag:
                if transcript and subtitles:
                    initial_srt_path = os.path.join(crew_output_folder, f'{os.path.splitext(filename)[0]}_subtitles.srt')
                    with open(initial_srt_path, 'w') as srt_file:
                        srt_file.write(subtitles)
                else:
                    full_transcript, full_subtitles = transcribe_main(input_video_path)
                    initial_srt_path = os.path.join(crew_output_folder, f'{os.path.splitext(filename)[0]}_subtitles.srt')
                    with open(initial_srt_path, 'w') as srt_file:
                        srt_file.write(full_subtitles)
            else:
                initial_srt_path = os.path.join(crew_output_folder, f'{os.path.splitext(filename)[0]}.srt')
            if wait_for_file(initial_srt_path):
                whisper_output_dir = 'whisper_output'
                srt_files = [f for f in os.listdir(whisper_output_dir) if f.endswith('.srt')]
                txt_files = [f for f in os.listdir(whisper_output_dir) if f.endswith('.txt')]
                if srt_files and txt_files:
                    subtitles_file = os.path.join(whisper_output_dir, srt_files[0])
                    transcript_file = os.path.join(whisper_output_dir, txt_files[0])
                    with open(transcript_file, 'r') as file:
                        transcript = file.read()
                    with open(subtitles_file, 'r') as file:
                        subtitles = file.read()
                    for srt_filename in sorted(os.listdir(crew_output_folder)):
                        if srt_filename.startswith('new_file_return_subtitles') and srt_filename.endswith('.srt'):
                            subtitle_file_path = os.path.join(crew_output_folder, srt_filename)
                else:
                    logging.error('No .srt or .txt files found in the whisper_output directory.')
            else:
                logging.error(f'Failed to verify the readiness of subtitles file: {initial_srt_path}')
    logging.info(f'local_transcribe.py completed')

