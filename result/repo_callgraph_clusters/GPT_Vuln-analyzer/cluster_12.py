# Cluster 12

class PasswordCracker:

    def __init__(self, password_hash, wordlist_file, algorithm, salt=None, parallel=False, complexity_check=False):
        self.password_hash = password_hash
        self.wordlist_file = wordlist_file
        self.algorithm = algorithm
        self.salt = salt
        self.parallel = parallel
        self.complexity_check = complexity_check
        self.total_passwords = 0
        self.matched_password = None

    def crack_hash(self, word):
        if self.salt:
            word_with_salt = f'{self.salt}{word}'
        else:
            word_with_salt = word
        hashed_word = hashlib.new(self.algorithm, word_with_salt.encode()).hexdigest()
        if hashed_word == self.password_hash:
            self.matched_password = word
            return True
        return False

    def generate_passwords(self, min_length, max_length, character_set):
        passwords = []
        for length in range(min_length, max_length + 1):
            for combination in itertools.product(character_set, repeat=length):
                password = ''.join(combination)
                passwords.append(password)
        return passwords

    def evaluate_complexity(self, password):
        has_lowercase = False
        has_uppercase = False
        has_digit = False
        has_special = False
        for char in password:
            if char.islower():
                has_lowercase = True
            elif char.isupper():
                has_uppercase = True
            elif char.isdigit():
                has_digit = True
            else:
                has_special = True
        if len(password) >= 8 and has_lowercase and has_uppercase and has_digit and has_special:
            return True
        return False

    def crack_passwords(self, passwords):
        for password in passwords:
            self.total_passwords += 1
            if self.crack_hash(password):
                break

    def crack_passwords_parallel(self, passwords):
        pool = Pool()
        pool.map(self.crack_password, passwords)
        pool.close()

    def crack_password(self, password):
        if self.complexity_check and (not self.evaluate_complexity(password)):
            return
        if self.matched_password is None:
            if self.crack_hash(password):
                return

    def crack_passwords_with_wordlist(self):
        with open(self.wordlist_file, 'r', encoding='latin-1') as wordlist:
            passwords = wordlist.read().splitlines()
            if self.parallel:
                self.crack_passwords_parallel(passwords)
            else:
                self.crack_passwords(passwords)

    def crack_passwords_with_brute_force(self, min_length, max_length, character_set):
        passwords = self.generate_passwords(min_length, max_length, character_set)
        if self.parallel:
            self.crack_passwords_parallel(passwords)
        else:
            self.crack_passwords(passwords)

    def print_statistics(self):
        msg = f'Password Cracked! Password: {self.matched_password}' if self.matched_password else 'Password Cracking Failed'
        message_panel = Panel(Align.center(Group('\n', Align.center(msg)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA Password Cracker', border_style='blue')
        print(message_panel)

def crack_passwords_parallel(self, passwords):
    pool = Pool()
    pool.map(self.crack_password, passwords)
    pool.close()

class PasswordCracker:

    def __init__(self, password_hash, wordlist_file, algorithm, salt=None, parallel=False, complexity_check=False):
        self.password_hash = password_hash
        self.wordlist_file = wordlist_file
        self.algorithm = algorithm
        self.salt = salt
        self.parallel = parallel
        self.complexity_check = complexity_check
        self.total_passwords = 0
        self.matched_password = None

    def crack_hash(self, word):
        if self.salt:
            word_with_salt = f'{self.salt}{word}'
        else:
            word_with_salt = word
        hashed_word = hashlib.new(self.algorithm, word_with_salt.encode()).hexdigest()
        if hashed_word == self.password_hash:
            self.matched_password = word
            return True
        return False

    def generate_passwords(self, min_length, max_length, character_set):
        passwords = []
        for length in range(min_length, max_length + 1):
            for combination in itertools.product(character_set, repeat=length):
                password = ''.join(combination)
                passwords.append(password)
        return passwords

    def evaluate_complexity(self, password):
        has_lowercase = False
        has_uppercase = False
        has_digit = False
        has_special = False
        for char in password:
            if char.islower():
                has_lowercase = True
            elif char.isupper():
                has_uppercase = True
            elif char.isdigit():
                has_digit = True
            else:
                has_special = True
        if len(password) >= 8 and has_lowercase and has_uppercase and has_digit and has_special:
            return True
        return False

    def crack_passwords(self, passwords):
        for password in passwords:
            self.total_passwords += 1
            if self.crack_hash(password):
                break

    def crack_passwords_parallel(self, passwords):
        pool = Pool()
        pool.map(self.crack_password, passwords)
        pool.close()

    def crack_password(self, password):
        if self.complexity_check and (not self.evaluate_complexity(password)):
            return
        if self.matched_password is None:
            if self.crack_hash(password):
                return

    def crack_passwords_with_wordlist(self):
        with open(self.wordlist_file, 'r', encoding='latin-1') as wordlist:
            passwords = wordlist.read().splitlines()
            if self.parallel:
                self.crack_passwords_parallel(passwords)
            else:
                self.crack_passwords(passwords)

    def crack_passwords_with_brute_force(self, min_length, max_length, character_set):
        passwords = self.generate_passwords(min_length, max_length, character_set)
        if self.parallel:
            self.crack_passwords_parallel(passwords)
        else:
            self.crack_passwords(passwords)

    def print_statistics(self):
        print(f'Total Number of Passwords Tried: {self.total_passwords}')
        if self.matched_password:
            print(f'Password Cracked! Password: {self.matched_password}')
        else:
            print('Password Failed.')

def crack_passwords_parallel(self, passwords):
    pool = Pool()
    pool.map(self.crack_password, passwords)
    pool.close()

class PacketAnalysis:
    tshark_loc = ''
    services = []
    tcp_streams = []
    sources = []
    destinations = []
    resolved = []
    dns_query_names = []
    dns_resp_names = []
    unique_eapol_data = []
    combined_json = []

    def detect_tshark(self) -> None:
        try:
            osp = platform.system()
            match osp:
                case 'Darwin':
                    self.tshark_loc = 'tshark'
                case 'Linux':
                    self.tshark_loc = 'tshark'
                case 'Windows':
                    self.tshark_loc = '"C:\\Program Files\\Wireshark\\tshark.exe"'
        except Exception:
            pass

    def extract_network_info(self, json_data):
        services = set()
        tcp_streams = set()
        source_addresses = set()
        destination_addresses = set()
        resolved_sources = set()
        dns_query_names = set()
        dns_resp_names = set()
        unique_eapol_data = set()
        for entry in json_data:
            layers = entry.get('_source', {}).get('layers', {})
            tcp_layer = layers.get('tcp', {})
            if tcp_layer:
                service = tcp_layer.get('tcp.srcport')
                if service:
                    services.add(service)
            if tcp_layer:
                tcp_stream_val = tcp_layer.get('tcp.stream')
                if service:
                    tcp_streams.add(tcp_stream_val)
            ip_layer = layers.get('ip', {})
            if ip_layer:
                source_address = ip_layer.get('ip.src_host')
                destination_address = ip_layer.get('ip.dst_host')
                if source_address:
                    source_addresses.add(source_address)
                if destination_address:
                    destination_addresses.add(destination_address)
            eth_layer = layers.get('eth', {})
            if eth_layer:
                source_mac = eth_layer.get('eth.src')
                resolved_source_mac = eth_layer.get('eth.src_tree', {}).get('eth.src_resolved')
                if source_mac and resolved_source_mac:
                    resolved_sources.add(resolved_source_mac)
            dns_layer = layers.get('dns', {})
            if dns_layer:
                queries = dns_layer.get('Queries', [])
                if isinstance(queries, list):
                    for query in queries:
                        query_name = query.get('dns.qry.name')
                        if query_name:
                            dns_query_names.add(query_name)
                elif isinstance(queries, dict):
                    for query_name, query_info in queries.items():
                        dns_query_names.add(query_info.get('dns.qry.name'))
                answers = dns_layer.get('Answers', [])
                if isinstance(answers, list):
                    for answer in answers:
                        resp_name = answer.get('dns.resp.name')
                        if resp_name:
                            dns_resp_names.add(resp_name)
                elif isinstance(answers, dict):
                    for resp_name, resp_info in answers.items():
                        dns_resp_names.add(resp_info.get('dns.resp.name'))
            eapol_layer = layers.get('eapol', {})
            if eapol_layer:
                eapol_data = eapol_layer.get('wlan_rsna_eapol.keydes.data', '')
                unique_eapol_data.add(eapol_data)
        self.services = list(services)
        self.tcp_streams = list(tcp_streams)
        self.source_addresses = list(source_addresses)
        self.destination_addresses = list(destination_addresses)
        self.resolved_sources = list(resolved_sources)
        self.dns_query_names = list(dns_query_names)
        self.dns_resp_names = list(dns_resp_names)
        self.unique_eapol_data = list(unique_eapol_data)

    def run_tshark_command(self, service, source, streams):
        stream_cmd = f'{self.tshark_loc} -r test.pcap -q -z follow,tcp,raw,{streams} -Y "ip.addr=={source} and tcp.port=={service}"'
        runner = run(stream_cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
        output_lines = runner.stdout.splitlines()
        node_regex = re.compile('Node (\\d+): (.+)$')
        data_regex = re.compile('\\s+(.+)$')
        node_0, node_1, data = (None, None, None)
        for line in output_lines:
            node_match = node_regex.match(line)
            data_match = data_regex.match(line)
            if node_match:
                node_num, node_value = node_match.groups()
                if node_num == '0':
                    node_0 = node_value
                elif node_num == '1':
                    node_1 = node_value
            elif data_match:
                data = data_match.group(1)
        if node_0 is not None and node_1 is not None and (data is not None):
            return [f'Source: {node_0}', f'Destination: {node_1}', f'stream: {streams}']
        else:
            return []

    def flatten_json(self, data: Any, separator: Any='.') -> Any:
        flattened_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                nested_data = self.flatten_json(value, separator)
                for nested_key, nested_value in nested_data.items():
                    flattened_data[key + separator + nested_key] = nested_value
            else:
                flattened_data[key] = value
        return flattened_data

    def stream(self, service_list, source_list, tcp_streams_list, max_workers=20):
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            command_params = [(service, source, streams) for service in service_list for source in source_list for streams in tcp_streams_list]
            print('Total Streams combination: ', len(command_params))
            print('Number of workers in progress: ', max_workers)
            results = list(executor.map(lambda params: self.run_tshark_command(*params), command_params))
        results = [result for result in results if result]
        self.combined_json = results

    def PacketAnalyzer(self, cap_loc, save_loc, max_workers):
        self.detect_tshark()
        print('Collecting Json Data')
        raw_pcap = run(f'{self.tshark_loc} -r {cap_loc} -T json', shell=True, capture_output=True, text=True)
        try:
            raw_data = raw_pcap.stdout
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            print(f'Error decoding JSON: {e}')
            json_data = []
        print('Extracting IP details...')
        print('Extracting DNS details...')
        print('Extracting EAPOL details...')
        self.extract_network_info(json_data)
        print('Extracting TCP STREAMS details...')
        print('TCP streams can take some time..')
        self.stream(service_list=self.services, source_list=self.source_addresses, tcp_streams_list=self.tcp_streams, max_workers=max_workers)
        print('Completed')
        filtered_stream_data = self.combined_json
        values = {'PacketAnalysis': {'Services': self.services, 'TCP Streams': self.tcp_streams, 'Sources Address': self.source_addresses, 'Destination Address': self.destination_addresses, 'DNS Resolved': self.resolved, 'DNS Query': self.dns_query_names, 'DNS Response': self.dns_resp_names, 'EAPOL Data': self.unique_eapol_data, 'Stream Data': filtered_stream_data}}
        table_val = {'PacketAnalysis': {'Services': self.services, 'TCP Streams': self.tcp_streams, 'Sources Address': self.source_addresses, 'Destination Address': self.destination_addresses, 'DNS Resolved': self.resolved, 'DNS Query': self.dns_query_names, 'DNS Response': self.dns_resp_names, 'EAPOL Data': self.unique_eapol_data, ' Total Streams Data': str(len(filtered_stream_data))}}
        table = Table(title='GVA Report for PCAP', show_header=True, header_style='bold magenta')
        table.add_column('Identifiers', style='cyan')
        table.add_column('Data', style='green')
        flattened_data: dict = self.flatten_json(table_val, separator='.')
        for key, value in flattened_data.items():
            value_str = str(value)
            table.add_row(key, str(value_str))
        console = Console()
        console.print(table)
        with open(f'{save_loc}', 'w+') as file:
            file.write(str(json.dumps(values)))

def stream(self, service_list, source_list, tcp_streams_list, max_workers=20):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        command_params = [(service, source, streams) for service in service_list for source in source_list for streams in tcp_streams_list]
        print('Total Streams combination: ', len(command_params))
        print('Number of workers in progress: ', max_workers)
        results = list(executor.map(lambda params: self.run_tshark_command(*params), command_params))
    results = [result for result in results if result]
    self.combined_json = results

class PacketAnalysis:
    tshark_loc = ''
    services = []
    tcp_streams = []
    source_addresses = []
    destination_addresses = []
    resolved_sources = []
    dns_query_names = []
    dns_resp_names = []
    unique_eapol_data = []
    combined_json = []

    def __init__(self):
        self.detect_tshark()

    def detect_tshark(self) -> None:
        try:
            osp = platform.system()
            match osp:
                case 'Darwin':
                    self.tshark_loc = 'tshark'
                case 'Linux':
                    self.tshark_loc = 'tshark'
                case 'Windows':
                    self.tshark_loc = '"C:\\Program Files\\Wireshark\\tshark.exe"'
        except Exception:
            pass

    def extract_network_info(self, json_data):
        services = set()
        tcp_streams = set()
        source_addresses = set()
        destination_addresses = set()
        resolved_sources = set()
        dns_query_names = set()
        dns_resp_names = set()
        unique_eapol_data = set()
        for entry in json_data:
            layers = entry.get('_source', {}).get('layers', {})
            tcp_layer = layers.get('tcp', {})
            if tcp_layer:
                service = tcp_layer.get('tcp.srcport')
                if service:
                    services.add(service)
                tcp_stream_val = tcp_layer.get('tcp.stream')
                if tcp_stream_val:
                    tcp_streams.add(tcp_stream_val)
            ip_layer = layers.get('ip', {})
            if ip_layer:
                source_address = ip_layer.get('ip.src_host')
                destination_address = ip_layer.get('ip.dst_host')
                if source_address:
                    source_addresses.add(source_address)
                if destination_address:
                    destination_addresses.add(destination_address)
            eth_layer = layers.get('eth', {})
            if eth_layer:
                source_mac = eth_layer.get('eth.src')
                resolved_source_mac = eth_layer.get('eth.src_tree', {}).get('eth.src_resolved')
                if source_mac and resolved_source_mac:
                    resolved_sources.add(resolved_source_mac)
            dns_layer = layers.get('dns', {})
            if dns_layer:
                queries = dns_layer.get('Queries', [])
                if isinstance(queries, list):
                    for query in queries:
                        query_name = query.get('dns.qry.name')
                        if query_name:
                            dns_query_names.add(query_name)
                elif isinstance(queries, dict):
                    for query_name, query_info in queries.items():
                        dns_query_names.add(query_info.get('dns.qry.name'))
                answers = dns_layer.get('Answers', [])
                if isinstance(answers, list):
                    for answer in answers:
                        resp_name = answer.get('dns.resp.name')
                        if resp_name:
                            dns_resp_names.add(resp_name)
                elif isinstance(answers, dict):
                    for resp_name, resp_info in answers.items():
                        dns_resp_names.add(resp_info.get('dns.resp.name'))
            eapol_layer = layers.get('eapol', {})
            if eapol_layer:
                eapol_data = eapol_layer.get('wlan_rsna_eapol.keydes.data', '')
                unique_eapol_data.add(eapol_data)
        self.services = list(services)
        self.tcp_streams = list(tcp_streams)
        self.source_addresses = list(source_addresses)
        self.destination_addresses = list(destination_addresses)
        self.resolved_sources = list(resolved_sources)
        self.dns_query_names = list(dns_query_names)
        self.dns_resp_names = list(dns_resp_names)
        self.unique_eapol_data = list(unique_eapol_data)

    def run_tshark_command(self, service, source, streams):
        sanitized_service = shlex.quote(str(service))
        sanitized_source = shlex.quote(str(source))
        sanitized_streams = shlex.quote(str(streams))
        stream_cmd = f'{self.tshark_loc} -r test.pcap -q -z follow,tcp,raw,{sanitized_streams} -Y "ip.addr=={sanitized_source} and tcp.port=={sanitized_service}"'
        runner = run(stream_cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
        output_lines = runner.stdout.splitlines()
        node_regex = re.compile('Node (\\d+): (.+)$')
        data_regex = re.compile('\\s+(.+)$')
        node_0, node_1, data = (None, None, None)
        for line in output_lines:
            node_match = node_regex.match(line)
            data_match = data_regex.match(line)
            if node_match:
                node_num, node_value = node_match.groups()
                if node_num == '0':
                    node_0 = node_value
                elif node_num == '1':
                    node_1 = node_value
            elif data_match:
                data = data_match.group(1)
        if node_0 is not None and node_1 is not None and (data is not None):
            return [f'Source: {node_0}', f'Destination: {node_1}', f'stream: {streams}']
        else:
            return []

    def flatten_json(self, data: Any, separator: Any='.') -> Any:
        flattened_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                nested_data = self.flatten_json(value, separator)
                for nested_key, nested_value in nested_data.items():
                    flattened_data[key + separator + nested_key] = nested_value
            else:
                flattened_data[key] = value
        return flattened_data

    def stream(self, service_list, source_list, tcp_streams_list, max_workers=20):
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            command_params = [(service, source, streams) for service in service_list for source in source_list for streams in tcp_streams_list]
            print('Total Streams combination: ', len(command_params))
            print('Number of workers in progress: ', max_workers)
            results = list(executor.map(lambda params: self.run_tshark_command(*params), command_params))
        results = [result for result in results if result]
        self.combined_json = results

    def perform_full_analysis(self, pcap_path, json_path, max_workers=20):
        print('Collecting Json Data')
        sanitized_pcap_path = shlex.quote(pcap_path)
        raw_pcap = run(f'{self.tshark_loc} -r {sanitized_pcap_path} -T json', shell=True, capture_output=True, text=True)
        try:
            raw_data = raw_pcap.stdout
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            print(f'Error decoding JSON: {e}')
            json_data = []
        print('Extracting IP details...')
        print('Extracting DNS details...')
        print('Extracting EAPOL details...')
        self.extract_network_info(json_data)
        print('Extracting TCP STREAMS details...')
        print('TCP streams can take some time..')
        self.stream(service_list=self.services, source_list=self.source_addresses, tcp_streams_list=self.tcp_streams, max_workers=max_workers)
        print('Completed')
        filtered_stream_data = self.combined_json
        values = {'PacketAnalysis': {'Services': self.services, 'TCP Streams': self.tcp_streams, 'Sources Address': self.source_addresses, 'Destination Address': self.destination_addresses, 'DNS Resolved': self.resolved_sources, 'DNS Query': self.dns_query_names, 'DNS Response': self.dns_resp_names, 'EAPOL Data': self.unique_eapol_data, 'Stream Data': filtered_stream_data}}
        table_val = {'PacketAnalysis': {'Services': self.services, 'TCP Streams': self.tcp_streams, 'Sources Address': self.source_addresses, 'Destination Address': self.destination_addresses, 'DNS Resolved': self.resolved_sources, 'DNS Query': self.dns_query_names, 'DNS Response': self.dns_resp_names, 'EAPOL Data': self.unique_eapol_data, ' Total Streams Data': str(len(filtered_stream_data))}}
        table = Table(title='GVA Report for PCAP', show_header=True, header_style='bold magenta')
        table.add_column('Identifiers', style='cyan')
        table.add_column('Data', style='green')
        flattened_data: dict = self.flatten_json(table_val, separator='.')
        for key, value in flattened_data.items():
            value_str = str(value)
            table.add_row(key, str(value_str))
        console = Console()
        console.print(table)
        with open(f'{json_path}', 'w+') as file:
            file.write(str(json.dumps(values)))

def stream(self, service_list, source_list, tcp_streams_list, max_workers=20):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        command_params = [(service, source, streams) for service in service_list for source in source_list for streams in tcp_streams_list]
        print('Total Streams combination: ', len(command_params))
        print('Number of workers in progress: ', max_workers)
        results = list(executor.map(lambda params: self.run_tshark_command(*params), command_params))
    results = [result for result in results if result]
    self.combined_json = results

