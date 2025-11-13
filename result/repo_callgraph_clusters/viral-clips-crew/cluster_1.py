# Cluster 1

def convert_to_utf8(subtitle_path, output_path):
    """
    Converts subtitle file encoding to UTF-8.
    """
    try:
        with open(subtitle_path, 'r', encoding='iso-8859-1') as file:
            content = file.read()
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f'Subtitle encoding converted: {output_path}')
    except Exception as e:
        logging.error(f'Error during subtitle conversion: {e}')

def main():
    input_folder = './input_files'
    output_video_folder = './clipper_output'
    crew_output_folder = './crew_output'
    whisper_output_folder = './whisper_output'
    subtitler_output_folder = './subtitler_output'
    for folder in [input_folder, output_video_folder, crew_output_folder, whisper_output_folder, subtitler_output_folder]:
        os.makedirs(folder, exist_ok=True)
    while True:
        logging.info('Please select an option to proceed:')
        logging.info('1: Submit a YouTube Video Link')
        logging.info('2: Use an existing video file')
        choice = input('Please choose either option 1 or 2: ')
        if choice == '1':
            logging.info('Submitting a YouTube Video Link')
            url = input('Enter the YouTube URL: ')
            ytdl_main(url, input_folder, whisper_output_folder, whisper_output_folder)
            break
        elif choice == '2':
            logging.info('Using an existing video file')
            if not os.listdir(input_folder):
                logging.error(f'No video files found in the folder: {input_folder}')
                continue
            clean_whisper_output()
            local_whisper_process(input_folder, whisper_output_folder)
            break
        else:
            logging.info('Invalid choice. Please try again.')
    aspect_ratio_choice = get_aspect_ratio_choice()
    extracts_data = extracts.main()
    if extracts_data is None:
        logging.error('Failed to generate extracts. Exiting.')
        return
    crew.main(extracts_data)
    input_folder_path = Path(input_folder)
    crew_output_folder_path = Path(crew_output_folder)
    output_video_folder_path = Path(output_video_folder)
    for video_file in input_folder_path.glob('*.mp4'):
        for srt_file in crew_output_folder_path.glob('*.srt'):
            clipper.main(str(video_file), str(srt_file), str(output_video_folder_path), aspect_ratio_choice)
            logging.info(f'Processed {video_file} with {srt_file}')
    for video_file in output_video_folder_path.glob('*_trimmed.mp4'):
        base_name = video_file.stem.replace('_trimmed', '')
        srt_file = crew_output_folder_path / f'{base_name}.srt'
        if srt_file.exists():
            subtitler.process_video_and_subtitles(str(video_file), str(srt_file), subtitler_output_folder)
            logging.info(f'Added subtitles to {video_file}')
        else:
            logging.warning(f'No matching subtitle file found for {video_file}')
    logging.info(f'All videos processed. Final output saved in {subtitler_output_folder}')

def get_subtitles():
    whisper_output_dir = Path('whisper_output')
    if not whisper_output_dir.exists():
        logging.error(f'Directory not found: {whisper_output_dir}')
        return None
    srt_files = list(whisper_output_dir.glob('*.srt'))
    if not srt_files:
        logging.warning('No .srt files found in the whisper_output directory.')
        return None
    with open(srt_files[0], 'r') as file:
        subtitles = file.read()
    return subtitles

def get_whisper_output():
    whisper_output_dir = Path('whisper_output')
    if not whisper_output_dir.exists():
        logging.error(f'Directory not found: {whisper_output_dir}')
        return (None, None)
    srt_files = list(whisper_output_dir.glob('*.srt'))
    txt_files = list(whisper_output_dir.glob('*.txt'))
    if not srt_files or not txt_files:
        logging.warning('No .srt or .txt files found in the whisper_output directory.')
        return (None, None)
    with open(txt_files[0], 'r') as file:
        transcript = file.read()
    with open(srt_files[0], 'r') as file:
        subtitles = file.read()
    return (transcript, subtitles)

def save_response_to_file(response, output_path):
    try:
        with open(output_path, 'w') as f:
            json.dump(response, f, indent=4)
        logging.info(f'Response saved to {output_path}')
    except Exception as e:
        logging.error(f'Error saving response to file: {e}')

