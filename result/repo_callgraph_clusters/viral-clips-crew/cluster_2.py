# Cluster 2

def main(input_video, subtitle_file_path, output_folder, aspect_ratio_choice=None):
    if aspect_ratio_choice is None:
        aspect_ratio_choice = get_aspect_ratio_choice()
    process_video(input_video, subtitle_file_path, output_folder, aspect_ratio_choice)

