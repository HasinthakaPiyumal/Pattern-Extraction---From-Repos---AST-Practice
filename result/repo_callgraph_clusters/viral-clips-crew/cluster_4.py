# Cluster 4

def transcribe_file(model, srt, plain, file):
    input_file_path = Path(file)
    logging.info(f'Transcribing file: {input_file_path}\n')
    output_dir = Path('whisper_output')
    output_dir.mkdir(parents=True, exist_ok=True)
    result = model.transcribe(str(input_file_path), fp16=False, verbose=False, language='en')
    output_file_name = input_file_path.stem
    if plain:
        txt_path = output_dir / f'{output_file_name}.txt'
        logging.info(f'Creating text file: {txt_path}')
        with open(txt_path, 'w', encoding='utf-8') as txt:
            txt.write(result['text'])
        transcript = result['text']
    if srt:
        logging.info(f'Creating SRT file')
        srt_writer = get_writer('srt', str(output_dir))
        srt_writer(result, output_file_name)
        srt_path = output_dir / f'{output_file_name}.srt'
        with open(srt_path, 'r', encoding='utf-8') as srt_file:
            subtitles = srt_file.read()
    return (result, transcript, subtitles)

def main():
    logging.info('STARTING extracts.py')
    transcript, subtitles = get_whisper_output()
    if transcript is None or subtitles is None:
        logging.error('Failed to get whisper output')
        return None
    response = call_openai_api(transcript)
    if response and 'clips' in response:
        output_dir = Path('crew_output')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / 'api_response.json'
        save_response_to_file(response, output_path)
        extracts = [clip['text'] for clip in response['clips']]
        return extracts
    else:
        logging.error('Failed to get a valid response from OpenAI API')
        if response:
            logging.error(f'Unexpected response structure: {response}')
        return None

