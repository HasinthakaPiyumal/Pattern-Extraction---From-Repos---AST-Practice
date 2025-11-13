# Cluster 5

class NetworkScanner:
    profile_arguments = {1: '-Pn -sV -T4 -O -F', 2: '-Pn -T4 -A -v', 3: '-Pn -sS -sU -T4 -A -v', 4: '-Pn -p- -T4 -A -v', 5: '-Pn -sS -sU -T4 -A -PE -PP  -PY -g 53 --script=vuln', 6: '-Pn -sV -p- -A', 7: '-Pn -sS -sV -O -T4 -A', 8: '-Pn -sC', 9: '-Pn -p 1-65535 -T4 -A -v', 10: '-Pn -sU -T4', 11: '-Pn -sV --top-ports 100', 12: '-Pn -sS -sV -T4 --script=default,discovery,vuln', 13: '-Pn -F'}

    def scanner(self, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
        nm.scan(ip, arguments=self.profile_arguments.get(profile))
        json_data = nm.analyse_nmap_xml_scan()
        analyze = json_data['scan']
        try:
            ai_methods = {'openai': lambda: AIModels.GPT_AI(akey, analyze), 'bard': lambda: AIModels.BardAI(bkey, analyze), 'llama': lambda: AIModels.Llama_AI(analyze, 'local', lkey, lendpoint), 'llama-api': lambda: AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)}
            if AI in ai_methods and (akey or bkey):
                response = ai_methods[AI]()
            else:
                raise ValueError('Invalid AI type or missing keys')
        except KeyboardInterrupt:
            print('Bye')
            quit()
        return str(response)

def scanner(self, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
    nm.scan(ip, arguments=self.profile_arguments.get(profile))
    json_data = nm.analyse_nmap_xml_scan()
    analyze = json_data['scan']
    try:
        ai_methods = {'openai': lambda: AIModels.GPT_AI(akey, analyze), 'bard': lambda: AIModels.BardAI(bkey, analyze), 'llama': lambda: AIModels.Llama_AI(analyze, 'local', lkey, lendpoint), 'llama-api': lambda: AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)}
        if AI in ai_methods and (akey or bkey):
            response = ai_methods[AI]()
        else:
            raise ValueError('Invalid AI type or missing keys')
    except KeyboardInterrupt:
        print('Bye')
        quit()
    return str(response)

class geo_ip_recon:

    def geoip(key: Optional[str], target: str) -> Any:
        if key is None:
            raise ValueError('KeyNotFound: Key Not Provided')
        assert key is not None
        if target is None:
            raise ValueError('InvalidTarget: Target Not Provided')
        url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
        response = requests.get(url)
        content = response.text
        return content

def geoip(key: Optional[str], target: str) -> Any:
    if key is None:
        raise ValueError('KeyNotFound: Key Not Provided')
    assert key is not None
    if target is None:
        raise ValueError('InvalidTarget: Target Not Provided')
    url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
    response = requests.get(url)
    content = response.text
    return content

class DNSRecon:
    analyze = ''

    def dns_resolver(self, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
        if target is not None:
            pass
        else:
            raise ValueError('InvalidTarget: Target Not Provided')
        try:
            print('✅ Domain Name Scanned')
            Domain_scans = requests.get(f'https://api.hackertarget.com/dnslookup/?q={target}')
            print('✅ Reverse DNS Scanned')
            reverse_dns = requests.get(f'https://api.hackertarget.com/reversedns/?q={target}')
            print('✅ Zone Transfer Scanned')
            zone_transfer = requests.get(f'https://api.hackertarget.com/zonetransfer/?q={target}')
            self.analyze = f'\nDomain Names:\n{Domain_scans.text}\n\nReverse Dns:\n{reverse_dns.text}\n\nZone Transfer:\n{zone_transfer.text}\n'
        except requests.Timeout:
            print('❌ Request timeout error')
            pass
        match AI:
            case 'openai':
                try:
                    if akey is not None:
                        akey = akey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    print(self.analyze)
                    response = AIModels.gpt_ai(key=akey, analyze=self.analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bkey is not None:
                        bkey = bkey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bkey, self.analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.llama_AI(self.analyze, 'local', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.llama_AI(self.analyze, 'runpod', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        return str(response)

def dns_resolver(self, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
    if target is not None:
        pass
    else:
        raise ValueError('InvalidTarget: Target Not Provided')
    try:
        print('✅ Domain Name Scanned')
        Domain_scans = requests.get(f'https://api.hackertarget.com/dnslookup/?q={target}')
        print('✅ Reverse DNS Scanned')
        reverse_dns = requests.get(f'https://api.hackertarget.com/reversedns/?q={target}')
        print('✅ Zone Transfer Scanned')
        zone_transfer = requests.get(f'https://api.hackertarget.com/zonetransfer/?q={target}')
        self.analyze = f'\nDomain Names:\n{Domain_scans.text}\n\nReverse Dns:\n{reverse_dns.text}\n\nZone Transfer:\n{zone_transfer.text}\n'
    except requests.Timeout:
        print('❌ Request timeout error')
        pass
    match AI:
        case 'openai':
            try:
                if akey is not None:
                    akey = akey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                print(self.analyze)
                response = AIModels.gpt_ai(key=akey, analyze=self.analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'bard':
            try:
                if bkey is not None:
                    bkey = bkey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.BardAI(bkey, self.analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama':
            try:
                response = AIModels.llama_AI(self.analyze, 'local', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama-api':
            try:
                response = AIModels.llama_AI(self.analyze, 'runpod', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
    return str(response)

class JWTAnalyzer:

    def __init__(self):
        self.AI_models = JWT_AI_MODEL()
        self.model_map = {'openai': self.call_openai_model, 'bard': self.call_bard_model, 'llama': self.call_llama_model, 'llama-api': self.call_llama_api_model}

    @staticmethod
    def base64_url_decode(input_str):
        padding = '=' * (4 - len(input_str) % 4)
        return base64.urlsafe_b64decode(input_str + padding).decode('utf-8', 'replace')

    @staticmethod
    def decode_jwt(token):
        try:
            decoded = jwt.decode(token, algorithms=['HS256'], options={'verify_signature': False})
            return decoded
        except jwt.ExpiredSignatureError:
            return {'Error': 'Token has expired.'}
        except jwt.InvalidTokenError as e:
            return {'Error': f'Invalid token: {e}'}

    def analyze(self, token, **api_tokens):
        decoded_payload = self.decode_jwt(token)
        if 'Error' in decoded_payload:
            return decoded_payload
        algorithm_used = decoded_payload.get('alg', 'Unknown Algorithm')
        expiration_time = datetime.utcfromtimestamp(decoded_payload['exp']) if 'exp' in decoded_payload else ''
        analysis_result = {'Algorithm Used': algorithm_used, 'Decoded Payload': decoded_payload, 'Claims': decoded_payload, 'Expiration Time': expiration_time}
        return self.call_ai_model(api_tokens['AI'], str(analysis_result), **api_tokens)

    def call_ai_model(self, ai_name, data, **tokens):
        ai_function = self.model_map.get(ai_name)
        if ai_function and tokens.get(f'{ai_name}_api_token'):
            return ai_function(data, tokens[f'{ai_name}_api_token'], tokens.get(f'{ai_name}_endpoint'))
        else:
            return 'Error: AI model or token not provided.'

    def call_openai_model(self, data, token, _):
        return self.AI_models.gpt_ai(data, token)

    def call_bard_model(self, data, token, _):
        return self.AI_models.BardAI(token, data)

    def call_llama_model(self, data, token, endpoint):
        return self.AI_models.llama_AI(data, 'local', token, endpoint)

    def call_llama_api_model(self, data, token, endpoint):
        return self.AI_models.Llama_AI(data, 'runpod', token, endpoint)

@staticmethod
def base64_url_decode(input_str):
    padding = '=' * (4 - len(input_str) % 4)
    return base64.urlsafe_b64decode(input_str + padding).decode('utf-8', 'replace')

@staticmethod
def decode_jwt(token):
    try:
        decoded = jwt.decode(token, algorithms=['HS256'], options={'verify_signature': False})
        return decoded
    except jwt.ExpiredSignatureError:
        return {'Error': 'Token has expired.'}
    except jwt.InvalidTokenError as e:
        return {'Error': f'Invalid token: {e}'}

def analyze(self, token, **api_tokens):
    decoded_payload = self.decode_jwt(token)
    if 'Error' in decoded_payload:
        return decoded_payload
    algorithm_used = decoded_payload.get('alg', 'Unknown Algorithm')
    expiration_time = datetime.utcfromtimestamp(decoded_payload['exp']) if 'exp' in decoded_payload else ''
    analysis_result = {'Algorithm Used': algorithm_used, 'Decoded Payload': decoded_payload, 'Claims': decoded_payload, 'Expiration Time': expiration_time}
    return self.call_ai_model(api_tokens['AI'], str(analysis_result), **api_tokens)

def call_ai_model(self, ai_name, data, **tokens):
    ai_function = self.model_map.get(ai_name)
    if ai_function and tokens.get(f'{ai_name}_api_token'):
        return ai_function(data, tokens[f'{ai_name}_api_token'], tokens.get(f'{ai_name}_endpoint'))
    else:
        return 'Error: AI model or token not provided.'

def call_openai_model(self, data, token, _):
    return self.AI_models.gpt_ai(data, token)

def call_bard_model(self, data, token, _):
    return self.AI_models.BardAI(token, data)

def call_llama_model(self, data, token, endpoint):
    return self.AI_models.llama_AI(data, 'local', token, endpoint)

def call_llama_api_model(self, data, token, endpoint):
    return self.AI_models.Llama_AI(data, 'runpod', token, endpoint)

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

def detect_dns_requests(self):
    dns_requests = [pkt[DNSQR].qname.decode() for pkt in self.packets if DNSQR in pkt and UDP in pkt and (pkt[UDP].dport == 53)]
    self.analysis_results['DNS Requests'] = dns_requests

def geoip(key: Optional[str], target: str) -> Any:
    if key is None:
        raise ValueError('KeyNotFound: Key Not Provided')
    assert key is not None
    if target is None:
        raise ValueError('InvalidTarget: Target Not Provided')
    url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
    response = requests.get(url)
    content = response.text
    return content

def scanner(ip: Optional[str], profile: int, key: str) -> str:
    if key is not None:
        pass
    else:
        raise ValueError('KeyNotFound: Key Not Provided')
    profile_argument = ''
    if profile == 1:
        profile_argument = '-Pn -sV -T4 -O -F'
    elif profile == 2:
        profile_argument = '-Pn -T4 -A -v'
    elif profile == 3:
        profile_argument = '-Pn -sS -sU -T4 -A -v'
    elif profile == 4:
        profile_argument = '-Pn -p- -T4 -A -v'
    elif profile == 5:
        profile_argument = '-Pn -sS -sU -T4 -A -PE -PP -PS80,443 -PA3389 -PU40125 -PY -g 53 --script=vuln'
    else:
        raise ValueError(f'Invalid Argument: {profile}')
    nm.scan('{}'.format(ip), arguments='{}'.format(profile_argument))
    json_data = nm.analyse_nmap_xml_scan()
    analyze = json_data['scan']
    try:
        response = PortAI(key, analyze)
    except KeyboardInterrupt:
        print('Bye')
        quit()
    return str(response)

class geo_ip_recon:

    def geoip(key: Optional[str], target: str) -> Any:
        if key is None:
            raise ValueError('KeyNotFound: Key Not Provided')
        assert key is not None
        if target is None:
            raise ValueError('InvalidTarget: Target Not Provided')
        url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
        response = requests.get(url)
        content = response.text
        return content

def geoip(key: Optional[str], target: str) -> Any:
    if key is None:
        raise ValueError('KeyNotFound: Key Not Provided')
    assert key is not None
    if target is None:
        raise ValueError('InvalidTarget: Target Not Provided')
    url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
    response = requests.get(url)
    content = response.text
    return content

class DNSRecon:

    def dns_resolver(self, AIModels, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
        if target is not None:
            pass
        else:
            raise ValueError('InvalidTarget: Target Not Provided')
        analyze = ''
        record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
        for record_type in track(record_types):
            try:
                answer = dns_resolver_module.resolve(target, record_type)
                for server in answer:
                    st = server.to_text()
                    analyze += f'\n{record_type} : {st}'
            except dns_resolver_module.NoAnswer:
                print('No record Found')
                pass
            except dns_resolver_module.NXDOMAIN:
                print('NXDOMAIN record NOT Found')
                pass
            except dns_resolver_module.LifetimeTimeout:
                print('Timed out, check your internet')
                pass
            except requests.exceptions.InvalidHeader:
                pass
            except KeyboardInterrupt:
                print('Bye')
                quit()
        response = ''
        match AI:
            case 'openai':
                try:
                    if akey is not None:
                        akey = akey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.gpt_ai(akey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bkey is not None:
                        bkey = bkey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bkey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.llama_AI(analyze, 'local', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.llama_AI(analyze, 'runpod', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        return str(response)

def dns_resolver(self, AIModels, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
    if target is not None:
        pass
    else:
        raise ValueError('InvalidTarget: Target Not Provided')
    analyze = ''
    record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
    for record_type in track(record_types):
        try:
            answer = dns_resolver_module.resolve(target, record_type)
            for server in answer:
                st = server.to_text()
                analyze += f'\n{record_type} : {st}'
        except dns_resolver_module.NoAnswer:
            print('No record Found')
            pass
        except dns_resolver_module.NXDOMAIN:
            print('NXDOMAIN record NOT Found')
            pass
        except dns_resolver_module.LifetimeTimeout:
            print('Timed out, check your internet')
            pass
        except requests.exceptions.InvalidHeader:
            pass
        except KeyboardInterrupt:
            print('Bye')
            quit()
    response = ''
    match AI:
        case 'openai':
            try:
                if akey is not None:
                    akey = akey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.gpt_ai(akey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'bard':
            try:
                if bkey is not None:
                    bkey = bkey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.BardAI(bkey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama':
            try:
                response = AIModels.llama_AI(analyze, 'local', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama-api':
            try:
                response = AIModels.llama_AI(analyze, 'runpod', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
    return str(response)

class NetworkScanner:

    def scanner(self, AIModels, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
        profile_arguments = {1: '-Pn -sV -T4 -O -F', 2: '-Pn -T4 -A -v', 3: '-Pn -sS -sU -T4 -A -v', 4: '-Pn -p- -T4 -A -v', 5: '-Pn -sS -sU -T4 -A -PE -PP  -PY -g 53 --script=vuln', 6: '-Pn -sV -p- -A', 7: '-Pn -sS -sV -O -T4 -A', 8: '-Pn -sC', 9: '-Pn -p 1-65535 -T4 -A -v', 10: '-Pn -sU -T4', 11: '-Pn -sV --top-ports 100', 12: '-Pn -sS -sV -T4 --script=default,discovery,vuln', 13: '-Pn -F'}
        nm.scan('{}'.format(ip), arguments='{}'.format(profile_arguments.get(profile)))
        json_data = nm.analyse_nmap_xml_scan()
        analyze = json_data['scan']
        match AI:
            case 'openai':
                try:
                    if akey is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.GPT_AI(akey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bkey is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bkey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.Llama_AI(analyze, 'local', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        self.response = response
        text = str(self.response)
        return text

def scanner(self, AIModels, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
    profile_arguments = {1: '-Pn -sV -T4 -O -F', 2: '-Pn -T4 -A -v', 3: '-Pn -sS -sU -T4 -A -v', 4: '-Pn -p- -T4 -A -v', 5: '-Pn -sS -sU -T4 -A -PE -PP  -PY -g 53 --script=vuln', 6: '-Pn -sV -p- -A', 7: '-Pn -sS -sV -O -T4 -A', 8: '-Pn -sC', 9: '-Pn -p 1-65535 -T4 -A -v', 10: '-Pn -sU -T4', 11: '-Pn -sV --top-ports 100', 12: '-Pn -sS -sV -T4 --script=default,discovery,vuln', 13: '-Pn -F'}
    nm.scan('{}'.format(ip), arguments='{}'.format(profile_arguments.get(profile)))
    json_data = nm.analyse_nmap_xml_scan()
    analyze = json_data['scan']
    match AI:
        case 'openai':
            try:
                if akey is not None:
                    pass
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.GPT_AI(akey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'bard':
            try:
                if bkey is not None:
                    pass
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.BardAI(bkey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama':
            try:
                response = AIModels.Llama_AI(analyze, 'local', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama-api':
            try:
                response = AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
    self.response = response
    text = str(self.response)
    return text

class JWTAnalyzer:

    def analyze(self, AIModels, token, openai_api_token: Optional[str], bard_api_token: Optional[str], llama_api_token: Optional[str], llama_endpoint: Optional[str], AI: str) -> str:
        try:
            self.algorithm_used = ''
            self.decoded_payload = ''
            self.expiration_time = ''
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError('Invalid token format. Expected 3 parts.')
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '===').decode('utf-8', 'replace'))
            self.algorithm_used = header.get('alg', 'Unknown Algorithm')
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '===').decode('utf-8', 'replace'))
            self.decoded_payload = payload
            self.claims = {key: value for key, value in payload.items()}
            if 'exp' in payload:
                self.expiration_time = datetime.utcfromtimestamp(payload['exp'])
            self.analysis_result = {'Algorithm Used': self.algorithm_used, 'Decoded Payload': self.decoded_payload, 'Claims': self.claims, 'Expiration Time': self.expiration_time}
            str_data = str(self.analysis_result)
            match AI:
                case 'openai':
                    try:
                        if openai_api_token is not None:
                            pass
                        else:
                            raise ValueError('KeyNotFound: Key Not Provided')
                        response = AIModels.gpt_ai(str_data, openai_api_token)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'bard':
                    try:
                        if bard_api_token is not None:
                            pass
                        else:
                            raise ValueError('KeyNotFound: Key Not Provided')
                        response = AIModels.BardAI(bard_api_token, str_data)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'llama':
                    try:
                        response = AIModels.llama_AI(str_data, 'local', llama_api_token, llama_endpoint)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'llama-api':
                    try:
                        response = AIModels.Llama_AI(str_data, 'runpod', llama_api_token, llama_endpoint)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
            final_data = str(response)
            return final_data
        except jwt.ExpiredSignatureError:
            self.analysis_result = {'Error': 'Token has expired.'}
        except jwt.InvalidTokenError as e:
            self.analysis_result = {'Error': f'Invalid token: {e}'}

def analyze(self, AIModels, token, openai_api_token: Optional[str], bard_api_token: Optional[str], llama_api_token: Optional[str], llama_endpoint: Optional[str], AI: str) -> str:
    try:
        self.algorithm_used = ''
        self.decoded_payload = ''
        self.expiration_time = ''
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError('Invalid token format. Expected 3 parts.')
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '===').decode('utf-8', 'replace'))
        self.algorithm_used = header.get('alg', 'Unknown Algorithm')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '===').decode('utf-8', 'replace'))
        self.decoded_payload = payload
        self.claims = {key: value for key, value in payload.items()}
        if 'exp' in payload:
            self.expiration_time = datetime.utcfromtimestamp(payload['exp'])
        self.analysis_result = {'Algorithm Used': self.algorithm_used, 'Decoded Payload': self.decoded_payload, 'Claims': self.claims, 'Expiration Time': self.expiration_time}
        str_data = str(self.analysis_result)
        match AI:
            case 'openai':
                try:
                    if openai_api_token is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.gpt_ai(str_data, openai_api_token)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bard_api_token is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bard_api_token, str_data)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.llama_AI(str_data, 'local', llama_api_token, llama_endpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.Llama_AI(str_data, 'runpod', llama_api_token, llama_endpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        final_data = str(response)
        return final_data
    except jwt.ExpiredSignatureError:
        self.analysis_result = {'Error': 'Token has expired.'}
    except jwt.InvalidTokenError as e:
        self.analysis_result = {'Error': f'Invalid token: {e}'}

def geoip(key: Optional[str], target: str) -> Any:
    if key is None:
        raise ValueError('KeyNotFound: Key Not Provided')
    assert key is not None
    if target is None:
        raise ValueError('InvalidTarget: Target Not Provided')
    url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
    response = requests.get(url)
    content = response.text
    return content

def scanner(ip: Optional[str], profile: int, key: str) -> str:
    if key is not None:
        pass
    else:
        raise ValueError('KeyNotFound: Key Not Provided')
    profile_argument = ''
    if profile == 1:
        profile_argument = '-Pn -sV -T4 -O -F'
    elif profile == 2:
        profile_argument = '-Pn -T4 -A -v'
    elif profile == 3:
        profile_argument = '-Pn -sS -sU -T4 -A -v'
    elif profile == 4:
        profile_argument = '-Pn -p- -T4 -A -v'
    elif profile == 5:
        profile_argument = '-Pn -sS -sU -T4 -A -PE -PP -PS80,443 -PA3389 -PU40125 -PY -g 53 --script=vuln'
    else:
        raise ValueError(f'Invalid Argument: {profile}')
    nm.scan('{}'.format(ip), arguments='{}'.format(profile_argument))
    json_data = nm.analyse_nmap_xml_scan()
    analyze = json_data['scan']
    try:
        response = PortAI(key, analyze)
    except KeyboardInterrupt:
        print('Bye')
        quit()
    return str(response)

class geo_ip_recon:

    def geoip(key: Optional[str], target: str) -> Any:
        if key is None:
            raise ValueError('KeyNotFound: Key Not Provided')
        assert key is not None
        if target is None:
            raise ValueError('InvalidTarget: Target Not Provided')
        url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
        response = requests.get(url)
        content = response.text
        return content

def geoip(key: Optional[str], target: str) -> Any:
    if key is None:
        raise ValueError('KeyNotFound: Key Not Provided')
    assert key is not None
    if target is None:
        raise ValueError('InvalidTarget: Target Not Provided')
    url = f'https://api.ipgeolocation.io/ipgeo?apiKey={key}&ip={target}'
    response = requests.get(url)
    content = response.text
    return content

class DNSRecon:

    def dns_resolver(self, AIModels, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
        if target is not None:
            pass
        else:
            raise ValueError('InvalidTarget: Target Not Provided')
        analyze = ''
        record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
        for record_type in track(record_types):
            try:
                answer = dns_resolver_module.resolve(target, record_type)
                for server in answer:
                    st = server.to_text()
                    analyze += f'\n{record_type} : {st}'
            except dns_resolver_module.NoAnswer:
                print('No record Found')
                pass
            except dns_resolver_module.NXDOMAIN:
                print('NXDOMAIN record NOT Found')
                pass
            except dns_resolver_module.LifetimeTimeout:
                print('Timed out, check your internet')
                pass
            except requests.exceptions.InvalidHeader:
                pass
            except KeyboardInterrupt:
                print('Bye')
                quit()
        response = ''
        match AI:
            case 'openai':
                try:
                    if akey is not None:
                        akey = akey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.gpt_ai(akey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bkey is not None:
                        bkey = bkey.replace('\n', '')
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bkey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.llama_AI(analyze, 'local', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.llama_AI(analyze, 'runpod', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        return str(response)

def dns_resolver(self, AIModels, target: str, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> Any:
    if target is not None:
        pass
    else:
        raise ValueError('InvalidTarget: Target Not Provided')
    analyze = ''
    record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
    for record_type in track(record_types):
        try:
            answer = dns_resolver_module.resolve(target, record_type)
            for server in answer:
                st = server.to_text()
                analyze += f'\n{record_type} : {st}'
        except dns_resolver_module.NoAnswer:
            print('No record Found')
            pass
        except dns_resolver_module.NXDOMAIN:
            print('NXDOMAIN record NOT Found')
            pass
        except dns_resolver_module.LifetimeTimeout:
            print('Timed out, check your internet')
            pass
        except requests.exceptions.InvalidHeader:
            pass
        except KeyboardInterrupt:
            print('Bye')
            quit()
    response = ''
    match AI:
        case 'openai':
            try:
                if akey is not None:
                    akey = akey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.gpt_ai(akey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'bard':
            try:
                if bkey is not None:
                    bkey = bkey.replace('\n', '')
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.BardAI(bkey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama':
            try:
                response = AIModels.llama_AI(analyze, 'local', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama-api':
            try:
                response = AIModels.llama_AI(analyze, 'runpod', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
    return str(response)

class NetworkScanner:

    def scanner(self, AIModels, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
        profile_arguments = {1: '-Pn -sV -T4 -O -F', 2: '-Pn -T4 -A -v', 3: '-Pn -sS -sU -T4 -A -v', 4: '-Pn -p- -T4 -A -v', 5: '-Pn -sS -sU -T4 -A -PE -PP  -PY -g 53 --script=vuln', 6: '-Pn -sV -p- -A', 7: '-Pn -sS -sV -O -T4 -A', 8: '-Pn -sC', 9: '-Pn -p 1-65535 -T4 -A -v', 10: '-Pn -sU -T4', 11: '-Pn -sV --top-ports 100', 12: '-Pn -sS -sV -T4 --script=default,discovery,vuln', 13: '-Pn -F'}
        nm.scan('{}'.format(ip), arguments='{}'.format(profile_arguments.get(profile)))
        json_data = nm.analyse_nmap_xml_scan()
        analyze = json_data['scan']
        match AI:
            case 'openai':
                try:
                    if akey is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.GPT_AI(akey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bkey is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bkey, analyze)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.Llama_AI(analyze, 'local', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        self.response = response
        text = str(self.response)
        return text

def scanner(self, AIModels, ip: Optional[str], profile: int, akey: Optional[str], bkey: Optional[str], lkey, lendpoint, AI: str) -> str:
    profile_arguments = {1: '-Pn -sV -T4 -O -F', 2: '-Pn -T4 -A -v', 3: '-Pn -sS -sU -T4 -A -v', 4: '-Pn -p- -T4 -A -v', 5: '-Pn -sS -sU -T4 -A -PE -PP  -PY -g 53 --script=vuln', 6: '-Pn -sV -p- -A', 7: '-Pn -sS -sV -O -T4 -A', 8: '-Pn -sC', 9: '-Pn -p 1-65535 -T4 -A -v', 10: '-Pn -sU -T4', 11: '-Pn -sV --top-ports 100', 12: '-Pn -sS -sV -T4 --script=default,discovery,vuln', 13: '-Pn -F'}
    nm.scan('{}'.format(ip), arguments='{}'.format(profile_arguments.get(profile)))
    json_data = nm.analyse_nmap_xml_scan()
    analyze = json_data['scan']
    match AI:
        case 'openai':
            try:
                if akey is not None:
                    pass
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.GPT_AI(akey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'bard':
            try:
                if bkey is not None:
                    pass
                else:
                    raise ValueError('KeyNotFound: Key Not Provided')
                response = AIModels.BardAI(bkey, analyze)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama':
            try:
                response = AIModels.Llama_AI(analyze, 'local', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
        case 'llama-api':
            try:
                response = AIModels.Llama_AI(analyze, 'runpod', lkey, lendpoint)
            except KeyboardInterrupt:
                print('Bye')
                quit()
    self.response = response
    text = str(self.response)
    return text

class JWTAnalyzer:

    def analyze(self, AIModels, token, openai_api_token: Optional[str], bard_api_token: Optional[str], llama_api_token: Optional[str], llama_endpoint: Optional[str], AI: str) -> str:
        try:
            self.algorithm_used = ''
            self.decoded_payload = ''
            self.expiration_time = ''
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError('Invalid token format. Expected 3 parts.')
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '===').decode('utf-8', 'replace'))
            self.algorithm_used = header.get('alg', 'Unknown Algorithm')
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '===').decode('utf-8', 'replace'))
            self.decoded_payload = payload
            self.claims = {key: value for key, value in payload.items()}
            if 'exp' in payload:
                self.expiration_time = datetime.utcfromtimestamp(payload['exp'])
            self.analysis_result = {'Algorithm Used': self.algorithm_used, 'Decoded Payload': self.decoded_payload, 'Claims': self.claims, 'Expiration Time': self.expiration_time}
            str_data = str(self.analysis_result)
            match AI:
                case 'openai':
                    try:
                        if openai_api_token is not None:
                            pass
                        else:
                            raise ValueError('KeyNotFound: Key Not Provided')
                        response = AIModels.gpt_ai(str_data, openai_api_token)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'bard':
                    try:
                        if bard_api_token is not None:
                            pass
                        else:
                            raise ValueError('KeyNotFound: Key Not Provided')
                        response = AIModels.BardAI(bard_api_token, str_data)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'llama':
                    try:
                        response = AIModels.llama_AI(str_data, 'local', llama_api_token, llama_endpoint)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
                case 'llama-api':
                    try:
                        response = AIModels.Llama_AI(str_data, 'runpod', llama_api_token, llama_endpoint)
                    except KeyboardInterrupt:
                        print('Bye')
                        quit()
            final_data = str(response)
            return final_data
        except jwt.ExpiredSignatureError:
            self.analysis_result = {'Error': 'Token has expired.'}
        except jwt.InvalidTokenError as e:
            self.analysis_result = {'Error': f'Invalid token: {e}'}

def analyze(self, AIModels, token, openai_api_token: Optional[str], bard_api_token: Optional[str], llama_api_token: Optional[str], llama_endpoint: Optional[str], AI: str) -> str:
    try:
        self.algorithm_used = ''
        self.decoded_payload = ''
        self.expiration_time = ''
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError('Invalid token format. Expected 3 parts.')
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '===').decode('utf-8', 'replace'))
        self.algorithm_used = header.get('alg', 'Unknown Algorithm')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '===').decode('utf-8', 'replace'))
        self.decoded_payload = payload
        self.claims = {key: value for key, value in payload.items()}
        if 'exp' in payload:
            self.expiration_time = datetime.utcfromtimestamp(payload['exp'])
        self.analysis_result = {'Algorithm Used': self.algorithm_used, 'Decoded Payload': self.decoded_payload, 'Claims': self.claims, 'Expiration Time': self.expiration_time}
        str_data = str(self.analysis_result)
        match AI:
            case 'openai':
                try:
                    if openai_api_token is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.gpt_ai(str_data, openai_api_token)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'bard':
                try:
                    if bard_api_token is not None:
                        pass
                    else:
                        raise ValueError('KeyNotFound: Key Not Provided')
                    response = AIModels.BardAI(bard_api_token, str_data)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama':
                try:
                    response = AIModels.llama_AI(str_data, 'local', llama_api_token, llama_endpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
            case 'llama-api':
                try:
                    response = AIModels.Llama_AI(str_data, 'runpod', llama_api_token, llama_endpoint)
                except KeyboardInterrupt:
                    print('Bye')
                    quit()
        final_data = str(response)
        return final_data
    except jwt.ExpiredSignatureError:
        self.analysis_result = {'Error': 'Token has expired.'}
    except jwt.InvalidTokenError as e:
        self.analysis_result = {'Error': f'Invalid token: {e}'}

