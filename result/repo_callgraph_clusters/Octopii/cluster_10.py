# Cluster 10

def truncate(local_location):
    characters_per_file = 1232500
    file_data = ''
    with open(local_location, 'r') as file:
        file_data = file.read()
        file.close()
    truncated_data = file_data[0:characters_per_file]
    with open(local_location, 'w') as file:
        file.write(truncated_data)
        file.close()

def is_image(file_path):
    try:
        i = Image.open(file_path)
        return True
    except:
        return False

def append_to_output_file(data, file_name):
    try:
        loaded_json = []
        try:
            with open(file_name, 'r+') as read_file:
                loaded_json = json.loads(read_file.read())
        except:
            print("\nCreating new file named '" + file_name + "' and writing to it.")
        with open(file_name, 'w') as write_file:
            loaded_json.append(data)
            write_file.write(json.dumps(loaded_json, indent=4))
    except:
        traceback.print_exc()
        print("Couldn't write to " + file_name + '. Please check if the path is correct and try again.')

def get_regexes():
    with open('definitions.json', 'r', encoding='utf-8') as json_file:
        _rules = json.load(json_file)
        return _rules

