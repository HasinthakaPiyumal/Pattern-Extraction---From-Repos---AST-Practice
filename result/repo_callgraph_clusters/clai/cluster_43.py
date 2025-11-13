# Cluster 43

def process_files(command_id, user_name, files_changes):
    files_to_send = map_files(files_changes)
    send_files(command_id=command_id, user_name=user_name, files_values=FilesChangesValues(user_files=files_to_send, working_directory_files=[]))

