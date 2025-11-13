# Cluster 2

class Installer:

    def install():
        print('[+] Starting Installation...')
        print('[!] Checking model presence.')
        if Installer.check_model() is False:
            print('[!] Downloading model, this may take 15 minutes...')
            Installer.download_model()
        print('[!] Pulling docker images.')
        Installer.pull_docker_images()
        print('[+] Installation finished!')

    def check_model():
        if isfile(Config.MODEL_PATH):
            print('[+] Model found!')
            print('[!] Checking integrity, please allow 300 seconds...')
            if Installer.calculate_md5(Config.MODEL_PATH) == Config.MODEL_MD5:
                print('[+] Model integrity check pass!')
                return True
            else:
                print(f'[-] Check model file integrity! Expect md5sum={Config.MODEL_MD5}. Remove the file at {Config.MODEL_PATH} and try rerun the installer.')
                exit()
        else:
            print('[-] Model missing!')
            return False

    def calculate_md5(filename):
        hash_md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def download_model():
        try:
            r = requests.get(Config.MODEL_URL, stream=True, allow_redirects=True)
            if r.status_code != 200:
                r.raise_for_status()
                raise RuntimeError(f'Request to {Config.MODEL_URL} returned status code {r.status_code}')
            file_size = int(r.headers.get('Content-Length', 0))
            path = pathlib.Path(Config.MODEL_PATH).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            desc = '(Unknown total file size)' if file_size == 0 else ''
            r.raw.read = functools.partial(r.raw.read, decode_content=True)
            with tqdm.wrapattr(r.raw, 'read', total=file_size, desc=desc) as r_raw:
                with path.open('wb') as f:
                    shutil.copyfileobj(r_raw, f)
            print('[+] Model downloaded!')
            return True
        except:
            print('[-] Model download failed!')
            exit()

    def pull_docker_images():
        try:
            for image in Config.AI_IMAGES:
                process = subprocess.Popen(['docker', 'pull', image], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                while True:
                    output = process.stdout.readline()
                    print('    > ', output.strip())
                    return_code = process.poll()
                    if return_code is not None:
                        for output in process.stdout.readlines():
                            print('    > ', output.strip())
                        for error in process.stderr.readlines():
                            print('    > ', error.strip())
                            if 'permission denied' in error.strip():
                                process.stdout.close()
                                print('[!] Docker image pull failed! Check user permissions (add to docker group)')
                                exit()
                        break
                process.stdout.close()
                process.stderr.close()
            print('[+] Docker images pulled!')
            return True
        except Exception as e:
            print('[-] Docker pull failed! Are docker and docker-compose installed?', e)

def check_model():
    if isfile(Config.MODEL_PATH):
        print('[+] Model found!')
        print('[!] Checking integrity, please allow 300 seconds...')
        if Installer.calculate_md5(Config.MODEL_PATH) == Config.MODEL_MD5:
            print('[+] Model integrity check pass!')
            return True
        else:
            print(f'[-] Check model file integrity! Expect md5sum={Config.MODEL_MD5}. Remove the file at {Config.MODEL_PATH} and try rerun the installer.')
            exit()
    else:
        print('[-] Model missing!')
        return False

def pull_docker_images():
    try:
        for image in Config.AI_IMAGES:
            process = subprocess.Popen(['docker', 'pull', image], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            while True:
                output = process.stdout.readline()
                print('    > ', output.strip())
                return_code = process.poll()
                if return_code is not None:
                    for output in process.stdout.readlines():
                        print('    > ', output.strip())
                    for error in process.stderr.readlines():
                        print('    > ', error.strip())
                        if 'permission denied' in error.strip():
                            process.stdout.close()
                            print('[!] Docker image pull failed! Check user permissions (add to docker group)')
                            exit()
                    break
            process.stdout.close()
            process.stderr.close()
        print('[+] Docker images pulled!')
        return True
    except Exception as e:
        print('[-] Docker pull failed! Are docker and docker-compose installed?', e)

class Runner:

    def run(os_command: list, happy_msg: str, sad_msg: str):
        try:
            process = subprocess.Popen(os_command, stdout=subprocess.PIPE, universal_newlines=True)
            while True:
                output = process.stdout.readline()
                print('    > ', output.strip())
                return_code = process.poll()
                if return_code is not None:
                    for output in process.stdout.readlines():
                        print('    > ', output.strip())
                    break
            print(happy_msg)
            return True
        except:
            print(sad_msg)
            exit()

    def restart_container(container_name):
        print('[!] Checking if Challenge is already running.')
        status = subprocess.run(['docker', 'container', 'ps'], capture_output=True, text=True)
        if container_name in status.stdout:
            print('[!] Challenge is already running, rebooting it now.')
            subprocess.run(['docker', 'stop', container_name], capture_output=True, text=True)
        else:
            print('[+] Challenge not already started, starting now')

    def ctfd():
        print('[+] Starting CTFd')
        os_command = ['docker', 'compose', 'up', 'ctfd', '-d']
        happy_msg = '[+] CTFd Started! Open browser to http://127.0.0.1:8000'
        sad_msg = '[-] CTFd startup failed!'
        Runner.run(os_command, happy_msg, sad_msg)

    def check_llm_status(container_name, happy_msg, sad_msg):
        subprocess.run(['docker', 'exec', container_name, 'touch', '/challenge/log.txt'])
        print('[!] Waiting for LLM to load, this may take a few minutes...')
        try:
            test = False
            while test == False:
                result = subprocess.run(['docker', 'exec', container_name, 'cat', '/challenge/log.txt'], capture_output=True, text=True)
                if result.returncode > 0:
                    print('[-] Docker launch failed!', result)
                    exit()
                if 'LLM loaded!' in result.stdout:
                    print('[+] LLM Loaded!')
                    print(happy_msg)
                    test = True
                else:
                    sleep(5)
        except Exception as e:
            print(sad_msg, e)
            exit()

    def challenge_1():
        container_name = 'challenge1'
        print('[+] Starting Challenge 1!')
        os_command = ['docker', 'compose', 'up', container_name, '-d']
        run_happy_msg = '[!] Challenge 1 pending...'
        run_sad_msg = '[-] Challenge 1 startup failed!'
        llm_happy_msg = '[+] Netcat to port 9001 to start the challenge.  Good luck!'
        llm_sad_msg = run_sad_msg
        Runner.restart_container(container_name)
        Runner.run(os_command, run_happy_msg, run_sad_msg)
        Runner.check_llm_status(container_name, llm_happy_msg, llm_sad_msg)

    def challenge_2():
        container_name = 'challenge2'
        print('[+] Starting Challenge 2!')
        os_command = ['docker', 'compose', 'up', container_name, '-d']
        run_happy_msg = '[!] Challenge 2 pending...'
        run_sad_msg = '[-] Challenge 2 startup failed!'
        llm_happy_msg = '[+] Netcat to port 9002 to start the challenge.  Good luck!'
        llm_sad_msg = run_sad_msg
        Runner.restart_container(container_name)
        Runner.run(os_command, run_happy_msg, run_sad_msg)
        Runner.check_llm_status(container_name, llm_happy_msg, llm_sad_msg)

def run(os_command: list, happy_msg: str, sad_msg: str):
    try:
        process = subprocess.Popen(os_command, stdout=subprocess.PIPE, universal_newlines=True)
        while True:
            output = process.stdout.readline()
            print('    > ', output.strip())
            return_code = process.poll()
            if return_code is not None:
                for output in process.stdout.readlines():
                    print('    > ', output.strip())
                break
        print(happy_msg)
        return True
    except:
        print(sad_msg)
        exit()

