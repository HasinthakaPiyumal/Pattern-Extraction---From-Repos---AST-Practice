# Cluster 6

def get_aspect_ratio_choice():
    while True:
        choice = input('Choose aspect ratio for all videos: (1) Keep as original, (2) 1:1 (square): ')
        if choice in ['1', '2']:
            return choice
        print('Invalid choice. Please enter 1 or 2.')

def main():
    print('WARNING: Running reboot.py will erase both input and output files!')
    user_input = input('Are you sure you want to continue? (y/n): ')
    if user_input.lower() != 'y':
        print('Operation cancelled.')
        return
    clipper_output_dir = 'clipper_output'
    whisper_output_dir = 'whisper_output'
    crew_output_dir = 'crew_output'
    input_files_dir = 'input_files'
    subtitler_output_dir = 'subtitler_output'
    api_response_file = 'api_response.json'
    move_files_to_trash(clipper_output_dir)
    move_files_to_trash(clipper_output_dir, file_extension='.mp4')
    move_files_to_trash(whisper_output_dir)
    move_files_to_trash(crew_output_dir, exclude_files=[api_response_file])
    move_files_to_trash(input_files_dir, exclude_files=['PLACE_CLIPS_HERE'], file_extension='.mp4')
    if os.path.exists(subtitler_output_dir):
        move_files_to_trash(subtitler_output_dir, file_extension='.mp4')
    clear_file_contents(os.path.join(crew_output_dir, api_response_file))

def get_aspect_ratio_choice():
    while True:
        choice = input('Choose aspect ratio for all videos: (1) Keep as original, (2) 1:1 (square): ')
        if choice in ['1', '2']:
            return choice
        print('Invalid choice. Please enter 1 or 2.')

