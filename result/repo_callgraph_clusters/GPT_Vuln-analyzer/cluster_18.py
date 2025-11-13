# Cluster 18

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

