# Cluster 8

def is_path_exists_or_creatable(pathname):
    try:
        return is_path_exists(pathname) or is_path_creatable(pathname)
    except OSError:
        return False

def mkdir_if_missing(input_path, warning=True, debug=True):
    """
	create a directory if not existing:
		1. if the input is a path of file, then create the parent directory of this file
		2. if the root directory does not exists for the input, then create all the root directories recursively until the parent directory of input exists

	parameters:
		input_path:     a string path
	"""
    good_path = safe_path(input_path, warning=warning, debug=debug)
    if debug:
        assert is_path_exists_or_creatable(good_path), 'input path is not valid or creatable: %s' % good_path
    dirname, _, _ = fileparts(good_path)
    if not is_path_exists(dirname):
        mkdir_if_missing(dirname)
    if isfolder(good_path) and (not is_path_exists(good_path)):
        os.mkdir(good_path)

def load_txt_file(file_path, debug=True):
    """
    load data or string from text file
    """
    file_path = safe_path(file_path)
    if debug:
        assert is_path_exists(file_path), 'text file is not existing at path: %s!' % file_path
    with open(file_path, 'r') as file:
        data = file.read().splitlines()
    num_lines = len(data)
    file.close()
    return (data, num_lines)

def load_list_from_folder(folder_path, ext_filter=None, depth=1, recursive=False, sort=True, save_path=None, debug=True):
    """
    load a list of files or folders from a system path

    parameters:
        folder_path:    root to search
        ext_filter:     a string to represent the extension of files interested
        depth:          maximum depth of folder to search, when it's None, all levels of folders will be searched
        recursive:      False: only return current level
                        True: return all levels till to the input depth

    outputs:
        fulllist:       a list of elements
        num_elem:       number of the elements
    """
    folder_path = safe_path(folder_path)
    if debug:
        assert isfolder(folder_path), 'input folder path is not correct: %s' % folder_path
    if not is_path_exists(folder_path):
        print('the input folder does not exist\n')
        return ([], 0)
    if debug:
        assert islogical(recursive), 'recursive should be a logical variable: {}'.format(recursive)
        assert depth is None or (isinteger(depth) and depth >= 1), 'input depth is not correct {}'.format(depth)
        assert ext_filter is None or (islist(ext_filter) and all((isstring(ext_tmp) for ext_tmp in ext_filter))) or isstring(ext_filter), 'extension filter is not correct'
    if isstring(ext_filter):
        ext_filter = [ext_filter]
    fulllist = list()
    if depth is None:
        recursive = True
        wildcard_prefix = '**'
        if ext_filter is not None:
            for ext_tmp in ext_filter:
                wildcard = os.path.join(wildcard_prefix, '*' + ext_tmp)
                curlist = glob2.glob(os.path.join(folder_path, wildcard))
                if sort:
                    curlist = sorted(curlist)
                fulllist += curlist
        else:
            wildcard = wildcard_prefix
            curlist = glob2.glob(os.path.join(folder_path, wildcard))
            if sort:
                curlist = sorted(curlist)
            fulllist += curlist
    else:
        wildcard_prefix = '*'
        for index in range(depth - 1):
            wildcard_prefix = os.path.join(wildcard_prefix, '*')
        if ext_filter is not None:
            for ext_tmp in ext_filter:
                wildcard = wildcard_prefix + ext_tmp
                curlist = glob.glob(os.path.join(folder_path, wildcard))
                if sort:
                    curlist = sorted(curlist)
                fulllist += curlist
        else:
            wildcard = wildcard_prefix
            curlist = glob.glob(os.path.join(folder_path, wildcard))
            if sort:
                curlist = sorted(curlist)
            fulllist += curlist
        if recursive and depth > 1:
            newlist, _ = load_list_from_folder(folder_path=folder_path, ext_filter=ext_filter, depth=depth - 1, recursive=True)
            fulllist += newlist
    fulllist = [os.path.normpath(path_tmp) for path_tmp in fulllist]
    num_elem = len(fulllist)
    if save_path is not None:
        save_path = safe_path(save_path)
        if debug:
            assert is_path_exists_or_creatable(save_path), 'the file cannot be created'
        with open(save_path, 'w') as file:
            for item in fulllist:
                file.write('%s\n' % item)
        file.close()
    return (fulllist, num_elem)

