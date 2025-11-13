# Cluster 8

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

def print_statistics(self):
    msg = f'Password Cracked! Password: {self.matched_password}' if self.matched_password else 'Password Cracking Failed'
    message_panel = Panel(Align.center(Group('\n', Align.center(msg)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA Password Cracker', border_style='blue')
    print(message_panel)

def llama_runpod_api(prompt: str, lkey: str, lendpoint: str) -> Any:
    url = f'https://api.runpod.ai/v2/{lendpoint}/runsync'
    payload = json.dumps({'input': {'prompt': prompt, 'max_new_tokens': 4500, 'temperature': 0.9, 'top_k': 50, 'top_p': 0.7, 'repetition_penalty': 1.2, 'batch_size': 8, 'stop': ['</s>']}})
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {lkey}'}
    response = requests.request('POST', url, headers=headers, data=payload)
    response_t = json.loads(response.text)
    return response_t['output']

class PacketAnalysis:

    def load_pcap(self, pcap_file):
        self.packets = rdpcap(pcap_file)
        self.analysis_results = {'Total Packets': len(self.packets)}

    def detect_eapol(self):
        eapol_packets = [pkt for pkt in self.packets if EAPOL in pkt]
        self.analysis_results['EAPOL Packets'] = len(eapol_packets)

    def summarize_traffic(self):
        ip_packets = [pkt for pkt in self.packets if IP in pkt]
        tcp_packets = [pkt for pkt in self.packets if TCP in pkt]
        self.analysis_results['Total IP Packets'] = len(ip_packets)
        self.analysis_results['Total TCP Packets'] = len(tcp_packets)

    def list_ips(self):
        src_ips = set((pkt[IP].src for pkt in self.packets if IP in pkt))
        dst_ips = set((pkt[IP].dst for pkt in self.packets if IP in pkt))
        self.analysis_results['Unique Source IPs'] = src_ips
        self.analysis_results['Unique Destination IPs'] = dst_ips

    def detect_arp_spoofing(self):
        arp_table = {}
        arp_spoofing_detected = False
        for packet in self.packets:
            if ARP in packet and packet[ARP].op == 2:
                ip = packet[ARP].psrc
                mac = packet[ARP].hwsrc
                if ip not in arp_table:
                    arp_table[ip] = set()
                arp_table[ip].add(mac)
                if len(arp_table[ip]) > 1:
                    arp_spoofing_detected = True
        self.analysis_results['ARP Spoofing Detected'] = arp_spoofing_detected

    def count_tcp_streams(self):
        stream_set = set()
        for packet in self.packets:
            if IP in packet and TCP in packet:
                stream_identifier = (packet[IP].src, packet[IP].dst, packet[TCP].sport, packet[TCP].dport)
                stream_set.add(stream_identifier)
        self.analysis_results['Total TCP Streams'] = len(stream_set)

    def list_unique_ports(self):
        tcp_ports = set()
        udp_ports = set()
        for packet in self.packets:
            if TCP in packet:
                tcp_ports.add(packet[TCP].sport)
                tcp_ports.add(packet[TCP].dport)
            elif UDP in packet:
                udp_ports.add(packet[UDP].sport)
                udp_ports.add(packet[UDP].dport)
        self.analysis_results['Unique TCP Ports'] = tcp_ports
        self.analysis_results['Unique UDP Ports'] = udp_ports

    def detect_mac_spoofing(self):
        ip_mac_mapping = defaultdict(set)
        mac_spoofing_detected = False
        for packet in self.packets:
            if ARP in packet and packet[ARP].op in (1, 2):
                ip_address = packet[ARP].psrc
                mac_address = packet[ARP].hwsrc
                ip_mac_mapping[ip_address].add(mac_address)
                if len(ip_mac_mapping[ip_address]) > 1:
                    mac_spoofing_detected = True
        self.analysis_results['MAC Spoofing Detected'] = mac_spoofing_detected

    def common_ports(self):
        ports = [pkt[TCP].dport for pkt in self.packets if TCP in pkt]
        port_counts = Counter(ports).most_common(5)
        self.analysis_results['Common Ports'] = port_counts

    def detect_dns_requests(self):
        dns_requests = [pkt[DNSQR].qname.decode() for pkt in self.packets if DNSQR in pkt and UDP in pkt and (pkt[UDP].dport == 53)]
        self.analysis_results['DNS Requests'] = dns_requests

    def detect_credentials(self):
        credential_patterns = ['username', 'password', 'passwd', 'user', 'pass']
        credential_packets = [pkt for pkt in self.packets if TCP in pkt and Raw in pkt and any((re.search(pattern, str(pkt[Raw].load), re.IGNORECASE) for pattern in credential_patterns))]
        self.analysis_results['Potential Credential Packets'] = len(credential_packets)

    def display_results(self):
        console = Console()
        table = Table(show_header=True, header_style='bold blue')
        table.add_column('Metric', style='dim')
        table.add_column('Value')
        for key, value in self.analysis_results.items():
            if isinstance(value, set):
                value_str = ', '.join(value)
            else:
                value_str = str(value)
            table.add_row(key, value_str)
        console.print(table)

    def save_results_to_json(self, json_file):
        with open(json_file, 'w') as file:
            output_data = {k: list(v) if isinstance(v, set) else v for k, v in self.analysis_results.items()}
            json.dump(output_data, file, indent=4)

    def perform_full_analysis(self, pcap_path, json_path):
        self.load_pcap(pcap_path)
        self.summarize_traffic()
        self.list_ips()
        self.common_ports()
        self.detect_dns_requests()
        self.detect_credentials()
        self.detect_arp_spoofing()
        self.detect_mac_spoofing()
        self.detect_eapol()
        self.display_results()
        self.save_results_to_json(json_path)

def display_results(self):
    console = Console()
    table = Table(show_header=True, header_style='bold blue')
    table.add_column('Metric', style='dim')
    table.add_column('Value')
    for key, value in self.analysis_results.items():
        if isinstance(value, set):
            value_str = ', '.join(value)
        else:
            value_str = str(value)
        table.add_row(key, value_str)
    console.print(table)

def save_results_to_json(self, json_file):
    with open(json_file, 'w') as file:
        output_data = {k: list(v) if isinstance(v, set) else v for k, v in self.analysis_results.items()}
        json.dump(output_data, file, indent=4)

class Assets:

    def clearscr(self) -> None:
        try:
            osp = platform.system()
            match osp:
                case 'Darwin':
                    os.system('clear')
                case 'Linux':
                    os.system('clear')
                case 'Windows':
                    os.system('cls')
        except Exception:
            pass

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

    def run_docker_container(self):
        client = docker.from_env()
        image_name = 'ollama/ollama'
        container_name = 'ollama'
        volume_mapping = {'/path/to/ollama': {'bind': '/root/.ollama', 'mode': 'rw'}}
        port_mapping = {'11434/tcp': 11434}
        try:
            client.images.pull(image_name)
            container = client.containers.run(image=image_name, name=container_name, volumes=volume_mapping, ports=port_mapping, detach=True, auto_remove=True)
            print(f"Container '{container.id}' is running in background.")
        except docker.errors.ImageNotFound:
            print(f"Image '{image_name}' not found.")
        except docker.errors.APIError as api_error:
            print(f'Docker API error: {api_error}')
        except Exception as e:
            print(f'Unexpected error: {e}')

    def help_menu() -> None:
        table = Table(title='Help Menu for GVA')
        table.add_column('Options', style='cyan')
        table.add_column('Input Type', style='green')
        table.add_column('Argument Input', style='green')
        table.add_column('Discription', style='green')
        table.add_column('Other internal options', style='green')
        table.add_row('Attack', '--attack', 'TXT/STRING', 'The Attack the user whats to run', 'sub / dns / nmap / geo/ jwt/ pcap')
        table.add_row('Target', '--target', 'IP/HOSTNAME/TOKEN/PCAP-FILE', 'The target of the user', 'None')
        table.add_row('Domain List', '--list', 'Path to text file', 'subdomain dictionary list', 'Path')
        table.add_row('Output', '--output', 'Path to text file', 'Outputs the PCAP analysis', 'Path')
        table.add_row('Profile', '--profile', 'INT (1-13)', 'The type of Nmap Scan the user intends', 'None')
        table.add_row('AI', '--ai', 'STRING', 'Choose your AI of choice', '/ LLAMA (RUNPOD OR LOCAL) /bard / openai (default)')
        table.add_row('menu', '--menu', 'BOOL', 'Interactive UI menu', 'True / False (Default)')
        table.add_row('Rich Help', '--r', 'STRING', 'Pritty Help menu', 'help')
        console.print(table)

    def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
        jdata = str(jdata)
        match attack_type:
            case 'Nmap':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            val = str(value)
                            table.add_row(key, str(val))
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            val = str(value)
                            table.add_row(key, str(val))
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'JWT':
                match ai:
                    case 'openai':
                        try:
                            data = json.loads(jdata)
                        except json.JSONDecodeError as e:
                            print('Error decoding JSON: ', e)
                            print('JSON data received: ', jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(str(key), str(value))
                        print(table)
                    case 'bard':
                        try:
                            data = json.loads(jdata)
                        except json.JSONDecodeError as e:
                            print('Error decoding JSON: ', e)
                            print('JSON data received: ', jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(str(key), str(value))
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'DNS':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            val = str(value)
                            table.add_row(key, str(val))
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            val = str(value)
                            table.add_row(key, str(val))
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'GeoIP':
                data = json.loads(jdata)
                table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
                table.add_column('Identifiers', style='cyan')
                table.add_column('Data', style='green')
                flattened_data: dict = self.flatten_json(data, separator='.')
                for key, value in flattened_data.items():
                    value_str = str(value)
                    table.add_row(key, value_str)
                console = Console()
                console.print(table)
            case 'PCAP':
                data = json.loads(jdata)
                table = Table(title='GVA Report for PCAP', show_header=True, header_style='bold magenta')
                table.add_column('Identifiers', style='cyan')
                table.add_column('Data', style='green')
                flattened_data: dict = self.flatten_json(data, separator='.')
                for key, value in flattened_data.items():
                    value_str = str(value)
                    table.add_row(key, str(value_str))
                console = Console()
                console.print(table)

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

def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
    jdata = str(jdata)
    match attack_type:
        case 'Nmap':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        val = str(value)
                        table.add_row(key, str(val))
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        val = str(value)
                        table.add_row(key, str(val))
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'JWT':
            match ai:
                case 'openai':
                    try:
                        data = json.loads(jdata)
                    except json.JSONDecodeError as e:
                        print('Error decoding JSON: ', e)
                        print('JSON data received: ', jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(str(key), str(value))
                    print(table)
                case 'bard':
                    try:
                        data = json.loads(jdata)
                    except json.JSONDecodeError as e:
                        print('Error decoding JSON: ', e)
                        print('JSON data received: ', jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(str(key), str(value))
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'DNS':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        val = str(value)
                        table.add_row(key, str(val))
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        val = str(value)
                        table.add_row(key, str(val))
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'GeoIP':
            data = json.loads(jdata)
            table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
            table.add_column('Identifiers', style='cyan')
            table.add_column('Data', style='green')
            flattened_data: dict = self.flatten_json(data, separator='.')
            for key, value in flattened_data.items():
                value_str = str(value)
                table.add_row(key, value_str)
            console = Console()
            console.print(table)
        case 'PCAP':
            data = json.loads(jdata)
            table = Table(title='GVA Report for PCAP', show_header=True, header_style='bold magenta')
            table.add_column('Identifiers', style='cyan')
            table.add_column('Data', style='green')
            flattened_data: dict = self.flatten_json(data, separator='.')
            for key, value in flattened_data.items():
                value_str = str(value)
                table.add_row(key, str(value_str))
            console = Console()
            console.print(table)

def output_save(output: Any, outf: Any) -> Any:
    top = customtkinter.CTkToplevel(root)
    top.title('GVA Output')
    top.grid_rowconfigure(0, weight=1)
    top.grid_columnconfigure(0, weight=1)
    top.textbox = customtkinter.CTkTextbox(master=top, height=500, width=400, corner_radius=0)
    top.textbox.grid(row=0, column=0, sticky='nsew')
    try:
        file = open(outf, 'x')
    except FileExistsError:
        file = open(outf, 'r+')
    file.write(str(output))
    file.close
    top.textbox.insert('0.0', text=output)

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

def llama_runpod_api(prompt: str, lkey: str, lendpoint: str) -> Any:
    url = f'https://api.runpod.ai/v2/{lendpoint}/runsync'
    payload = json.dumps({'input': {'prompt': prompt, 'max_new_tokens': 4500, 'temperature': 0.9, 'top_k': 50, 'top_p': 0.7, 'repetition_penalty': 1.2, 'batch_size': 8, 'stop': ['</s>']}})
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {lkey}'}
    response = requests.request('POST', url, headers=headers, data=payload)
    response_t = json.loads(response.text)
    return response_t['output']

class Assets:

    def clearscr() -> None:
        try:
            osp = platform.system()
            match osp:
                case 'Darwin':
                    os.system('clear')
                case 'Linux':
                    os.system('clear')
                case 'Windows':
                    os.system('cls')
        except Exception:
            pass

    def start_api_app():
        CREATE_NEW_CONSOLE = 16
        osp = platform.system()
        match osp:
            case 'Darwin':
                subprocess.Popen(['python3', 'llama_api.py'], creationflags=CREATE_NEW_CONSOLE)
            case 'Linux':
                subprocess.Popen(['python3', 'llama_api.py'])
            case 'Windows':
                subprocess.Popen(['python', 'llama_api.py'], creationflags=CREATE_NEW_CONSOLE)

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

    def help_menu() -> None:
        table = Table(title='Help Menu for GVA')
        table.add_column('Options', style='cyan')
        table.add_column('Input Type', style='green')
        table.add_column('Argument Input', style='green')
        table.add_column('Discription', style='green')
        table.add_column('Other internal options', style='green')
        table.add_row('Attack', '--attack', 'TXT/STRING', 'The Attack the user whats to run', 'sub / dns / nmap / geo')
        table.add_row('Target', '--target', 'IP/HOSTNAME', 'The target of the user', 'None')
        table.add_row('Domain List', '--list', 'Path to text file', 'subdomain dictionary list', 'Path')
        table.add_row('Profile', '--profile', 'INT (1-5)', 'The type of Nmap Scan the user intends', 'None')
        table.add_row('AI', '--ai', 'STRING', 'Choose your AI of choice', 'bard / openai (default)')
        table.add_row('menu', '--menu', 'BOOL', 'Interactive UI menu', 'True / False (Default)')
        table.add_row('Rich Help', '--r', 'STRING', 'Pritty Help menu', 'help')
        console.print(table)

    def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
        match attack_type:
            case 'Nmap':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'DNS':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'GeoIP':
                data = json.loads(jdata)
                table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
                table.add_column('Identifiers', style='cyan')
                table.add_column('Data', style='green')
                flattened_data: dict = self.flatten_json(data, separator='.')
                for key, value in flattened_data.items():
                    value_str = str(value)
                    table.add_row(key, value_str)
                console = Console()
                console.print(table)

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

def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
    match attack_type:
        case 'Nmap':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'DNS':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'GeoIP':
            data = json.loads(jdata)
            table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
            table.add_column('Identifiers', style='cyan')
            table.add_column('Data', style='green')
            flattened_data: dict = self.flatten_json(data, separator='.')
            for key, value in flattened_data.items():
                value_str = str(value)
                table.add_row(key, value_str)
            console = Console()
            console.print(table)

def output_save(output: Any, outf: Any) -> Any:
    top = customtkinter.CTkToplevel(root)
    top.title('GVA Output')
    top.grid_rowconfigure(0, weight=1)
    top.grid_columnconfigure(0, weight=1)
    top.textbox = customtkinter.CTkTextbox(master=top, height=500, width=400, corner_radius=0)
    top.textbox.grid(row=0, column=0, sticky='nsew')
    try:
        file = open(outf, 'x')
    except FileExistsError:
        file = open(outf, 'r+')
    file.write(str(output))
    file.close
    top.textbox.insert('0.0', text=output)

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

def __init__(self):
    self.detect_tshark()

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

def llama_runpod_api(prompt: str, lkey: str, lendpoint: str) -> Any:
    url = f'https://api.runpod.ai/v2/{lendpoint}/runsync'
    payload = json.dumps({'input': {'prompt': prompt, 'max_new_tokens': 4500, 'temperature': 0.9, 'top_k': 50, 'top_p': 0.7, 'repetition_penalty': 1.2, 'batch_size': 8, 'stop': ['</s>']}})
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {lkey}'}
    response = requests.request('POST', url, headers=headers, data=payload)
    response_t = json.loads(response.text)
    return response_t['output']

class Assets:

    def clearscr() -> None:
        try:
            osp = platform.system()
            match osp:
                case 'Darwin':
                    os.system('clear')
                case 'Linux':
                    os.system('clear')
                case 'Windows':
                    os.system('cls')
        except Exception:
            pass

    def start_api_app():
        CREATE_NEW_CONSOLE = 16
        osp = platform.system()
        match osp:
            case 'Darwin':
                subprocess.Popen(['python3', 'llama_api.py'], creationflags=CREATE_NEW_CONSOLE)
            case 'Linux':
                subprocess.Popen(['python3', 'llama_api.py'])
            case 'Windows':
                subprocess.Popen(['python', 'llama_api.py'], creationflags=CREATE_NEW_CONSOLE)

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

    def help_menu() -> None:
        table = Table(title='Help Menu for GVA')
        table.add_column('Options', style='cyan')
        table.add_column('Input Type', style='green')
        table.add_column('Argument Input', style='green')
        table.add_column('Discription', style='green')
        table.add_column('Other internal options', style='green')
        table.add_row('Attack', '--attack', 'TXT/STRING', 'The Attack the user whats to run', 'sub / dns / nmap / geo')
        table.add_row('Target', '--target', 'IP/HOSTNAME', 'The target of the user', 'None')
        table.add_row('Domain List', '--list', 'Path to text file', 'subdomain dictionary list', 'Path')
        table.add_row('Profile', '--profile', 'INT (1-5)', 'The type of Nmap Scan the user intends', 'None')
        table.add_row('AI', '--ai', 'STRING', 'Choose your AI of choice', 'bard / openai (default)')
        table.add_row('menu', '--menu', 'BOOL', 'Interactive UI menu', 'True / False (Default)')
        table.add_row('Rich Help', '--r', 'STRING', 'Pritty Help menu', 'help')
        console.print(table)

    def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
        match attack_type:
            case 'Nmap':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'DNS':
                match ai:
                    case 'openai':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'bard':
                        data = json.loads(jdata)
                        table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                        table.add_column('Variables', style='cyan')
                        table.add_column('Results', style='green')
                        for key, value in data.items():
                            table.add_row(key, value)
                        print(table)
                    case 'llama':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
                    case 'llama-api':
                        ai_out = Markdown(jdata)
                        message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                        print(message_panel)
            case 'GeoIP':
                data = json.loads(jdata)
                table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
                table.add_column('Identifiers', style='cyan')
                table.add_column('Data', style='green')
                flattened_data: dict = self.flatten_json(data, separator='.')
                for key, value in flattened_data.items():
                    value_str = str(value)
                    table.add_row(key, value_str)
                console = Console()
                console.print(table)

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

def print_output(self, attack_type: str, jdata: str, ai: str) -> Any:
    match attack_type:
        case 'Nmap':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'DNS':
            match ai:
                case 'openai':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'bard':
                    data = json.loads(jdata)
                    table = Table(title=f'GVA Report for {attack_type}', show_header=True, header_style='bold magenta')
                    table.add_column('Variables', style='cyan')
                    table.add_column('Results', style='green')
                    for key, value in data.items():
                        table.add_row(key, value)
                    print(table)
                case 'llama':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
                case 'llama-api':
                    ai_out = Markdown(jdata)
                    message_panel = Panel(Align.center(Group('\n', Align.center(ai_out)), vertical='middle'), box=box.ROUNDED, padding=(1, 2), title='[b red]The GVA LLama2', border_style='blue')
                    print(message_panel)
        case 'GeoIP':
            data = json.loads(jdata)
            table = Table(title='GVA Report for GeoIP', show_header=True, header_style='bold magenta')
            table.add_column('Identifiers', style='cyan')
            table.add_column('Data', style='green')
            flattened_data: dict = self.flatten_json(data, separator='.')
            for key, value in flattened_data.items():
                value_str = str(value)
                table.add_row(key, value_str)
            console = Console()
            console.print(table)

