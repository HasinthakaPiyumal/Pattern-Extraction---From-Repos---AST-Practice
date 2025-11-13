# Cluster 9

def dns_ai_data_regex(json_string: str) -> Any:
    A_pattern = '"A": \\["(.*?)"\\]'
    AAA_pattern = '"AAAA": \\["(.*?)"\\]'
    NS_pattern = '"NS": \\["(.*?)"\\]'
    MX_pattern = '"MX": \\["(.*?)"\\]'
    PTR_pattern = '"PTR": \\["(.*?)"\\]'
    SOA_pattern = '"SOA": \\["(.*?)"\\]'
    TXT_pattern = '"TXT": \\["(.*?)"\\]'
    Reverse_DNS_pattern = '"Reverse_DNS": \\{ "IP_Address": "(.*?)", "Domain": "(.*?)" \\}'
    Zone_Transfer_Scan_pattern = '"Zone_Transfer_Scan": \\{ "Allowed": (.*?), "Name_Servers": \\["(.*?)"\\] \\}'
    A = None
    AAA = None
    NS = None
    MX = None
    PTR = None
    SOA = None
    TXT = None
    Reverse_DNS_IP = None
    Reverse_DNS_Domain = None
    Zone_Transfer_Allowed = None
    Zone_Transfer_Name_Servers = None
    match = re.search(A_pattern, json_string)
    if match:
        A = match.group(1)
    match = re.search(AAA_pattern, json_string)
    if match:
        AAA = match.group(1)
    match = re.search(NS_pattern, json_string)
    if match:
        NS = match.group(1)
    match = re.search(MX_pattern, json_string)
    if match:
        MX = match.group(1)
    match = re.search(PTR_pattern, json_string)
    if match:
        PTR = match.group(1)
    match = re.search(SOA_pattern, json_string)
    if match:
        SOA = match.group(1)
    match = re.search(TXT_pattern, json_string)
    if match:
        TXT = match.group(1)
    match = re.search(Reverse_DNS_pattern, json_string)
    if match:
        Reverse_DNS_IP = match.group(1)
        Reverse_DNS_Domain = match.group(2)
    match = re.search(Zone_Transfer_Scan_pattern, json_string)
    if match:
        Zone_Transfer_Allowed = bool(match.group(1))
        Zone_Transfer_Name_Servers = match.group(2)
    data = {'DNS_Records': {'A': A, 'AAAA': AAA, 'NS': NS, 'MX': MX, 'PTR': PTR, 'SOA': SOA, 'TXT': TXT}, 'Reverse_DNS': {'IP_Address': Reverse_DNS_IP, 'Domain': Reverse_DNS_Domain}, 'Zone_Transfer_Scan': {'Allowed': Zone_Transfer_Allowed, 'Name_Servers': [Zone_Transfer_Name_Servers] if Zone_Transfer_Name_Servers else []}}
    json_output = json.dumps(data)
    return json_output

def nmap_ai_data_regex(json_string: str) -> Any:
    critical_score_pattern = '"critical score": \\["(.*?)"\\]'
    os_information_pattern = '"os information": \\["(.*?)"\\]'
    open_ports_pattern = '"open ports": \\["(.*?)"\\]'
    open_services_pattern = '"open services": \\["(.*?)"\\]'
    vulnerable_service_pattern = '"vulnerable service": \\["(.*?)"\\]'
    found_cve_pattern = '"found cve": \\["(.*?)"\\]'
    critical_score = None
    os_information = None
    open_ports = None
    open_services = None
    vulnerable_service = None
    found_cve = None
    match = re.search(critical_score_pattern, json_string)
    if match:
        critical_score = match.group(1)
    match = re.search(os_information_pattern, json_string)
    if match:
        os_information = match.group(1)
    match = re.search(open_ports_pattern, json_string)
    if match:
        open_ports = match.group(1)
    match = re.search(open_services_pattern, json_string)
    if match:
        open_services = match.group(1)
    match = re.search(vulnerable_service_pattern, json_string)
    if match:
        vulnerable_service = match.group(1)
    match = re.search(found_cve_pattern, json_string)
    if match:
        found_cve = match.group(1)
    data = {'critical score': critical_score, 'os information': os_information, 'open ports': open_ports, 'open services': open_services, 'vulnerable service': vulnerable_service, 'found cve': found_cve}
    json_output = json.dumps(data)
    return json_output

def jwt_ai_data_regex(json_string: str) -> Any:
    header_pattern = '"Header": \\{\\s*"alg": "(.*?)",\\s*"typ": "(.*?)"\\s*\\}'
    payload_pattern = '"Payload": \\{\\s*"iss": "(.*?)",\\s*"sub": "(.*?)",\\s*"aud": "(.*?)",\\s*"exp": "(.*?)",\\s*"nbf": "(.*?)",\\s*"iat": "(.*?)"\\s*\\}'
    signature_pattern = '"Signature": "(.*?)"'
    possible_attacks_pattern = '"PossibleAttacks": "(.*?)"'
    vulnerable_endpoints_pattern = '"VulnerableEndpoints": "(.*?)"'
    header = {}
    payload = {}
    signature = ''
    possible_attacks = ''
    vulnerable_endpoints = ''
    match_header = re.search(header_pattern, json_string)
    if match_header:
        header = {'alg': match_header.group(1), 'typ': match_header.group(2)}
    match_payload = re.search(payload_pattern, json_string)
    if match_payload:
        payload = {'iss': match_payload.group(1), 'sub': match_payload.group(2), 'aud': match_payload.group(3), 'exp': match_payload.group(4), 'nbf': match_payload.group(5), 'iat': match_payload.group(6)}
    match_signature = re.search(signature_pattern, json_string)
    if match_signature:
        signature = match_signature.group(1)
    match_attacks = re.search(possible_attacks_pattern, json_string)
    if match_attacks:
        possible_attacks = match_attacks.group(1)
    match_endpoints = re.search(vulnerable_endpoints_pattern, json_string)
    if match_endpoints:
        vulnerable_endpoints = match_endpoints.group(1)
    data = {'Header': header, 'Payload': payload, 'Signature': signature, 'PossibleAttacks': possible_attacks, 'VulnerableEndpoints': vulnerable_endpoints}
    json_output = json.dumps(data)
    return json_output

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

def detect_credentials(self):
    credential_patterns = ['username', 'password', 'passwd', 'user', 'pass']
    credential_packets = [pkt for pkt in self.packets if TCP in pkt and Raw in pkt and any((re.search(pattern, str(pkt[Raw].load), re.IGNORECASE) for pattern in credential_patterns))]
    self.analysis_results['Potential Credential Packets'] = len(credential_packets)

def dns_extract_data(json_string: str) -> Any:
    A_pattern = '"A": \\["(.*?)"\\]'
    AAA_pattern = '"AAA: \\["(.*?)"\\]'
    NS_pattern = '"NS": \\["(.*?)"\\]'
    MX_pattern = '"MX": \\["(.*?)"\\]'
    PTR_pattern = '"PTR": \\["(.*?)"\\]'
    SOA_pattern = '"SOA": \\["(.*?)"\\]'
    TXT_pattern = '"TXT": \\["(.*?)"\\]'
    A = None
    AAA = None
    NS = None
    MX = None
    PTR = None
    SOA = None
    TXT = None
    match = re.search(A_pattern, json_string)
    if match:
        A = match.group(1)
    match = re.search(AAA_pattern, json_string)
    if match:
        AAA = match.group(1)
    match = re.search(NS_pattern, json_string)
    if match:
        NS = match.group(1)
    match = re.search(MX_pattern, json_string)
    if match:
        MX = match.group(1)
    match = re.search(PTR_pattern, json_string)
    if match:
        PTR = match.group(1)
    match = re.search(SOA_pattern, json_string)
    if match:
        SOA = match.group(1)
    match = re.search(TXT_pattern, json_string)
    if match:
        TXT = match.group(1)
    data = {'A': A, 'AAA': AAA, 'NS': NS, 'MX': MX, 'PTR': PTR, 'SOA': SOA, 'TXT': TXT}
    json_output = json.dumps(data)
    return json_output

def port_extract_data(json_string: str) -> Any:
    critical_score_pattern = '"critical score": \\["(.*?)"\\]'
    os_information_pattern = '"os information": \\["(.*?)"\\]'
    open_ports_pattern = '"open ports": \\["(.*?)"\\]'
    open_services_pattern = '"open services": \\["(.*?)"\\]'
    vulnerable_service_pattern = '"vulnerable service": \\["(.*?)"\\]'
    found_cve_pattern = '"found cve": \\["(.*?)"\\]'
    critical_score = None
    os_information = None
    open_ports = None
    open_services = None
    vulnerable_service = None
    found_cve = None
    match = re.search(critical_score_pattern, json_string)
    if match:
        critical_score = match.group(1)
    match = re.search(os_information_pattern, json_string)
    if match:
        os_information = match.group(1)
    match = re.search(open_ports_pattern, json_string)
    if match:
        open_ports = match.group(1)
    match = re.search(open_services_pattern, json_string)
    if match:
        open_services = match.group(1)
    match = re.search(vulnerable_service_pattern, json_string)
    if match:
        vulnerable_service = match.group(1)
    match = re.search(found_cve_pattern, json_string)
    if match:
        found_cve = match.group(1)
    data = {'critical score': critical_score, 'os information': os_information, 'open ports': open_ports, 'open services': open_services, 'vulnerable service': vulnerable_service, 'found cve': found_cve}
    json_output = json.dumps(data)
    return json_output

def dns_ai_data_regex(json_string: str) -> Any:
    A_pattern = '"A": \\["(.*?)"\\]'
    AAA_pattern = '"AAA: \\["(.*?)"\\]'
    NS_pattern = '"NS": \\["(.*?)"\\]'
    MX_pattern = '"MX": \\["(.*?)"\\]'
    PTR_pattern = '"PTR": \\["(.*?)"\\]'
    SOA_pattern = '"SOA": \\["(.*?)"\\]'
    TXT_pattern = '"TXT": \\["(.*?)"\\]'
    A = None
    AAA = None
    NS = None
    MX = None
    PTR = None
    SOA = None
    TXT = None
    match = re.search(A_pattern, json_string)
    if match:
        A = match.group(1)
        match = re.search(AAA_pattern, json_string)
    if match:
        AAA = match.group(1)
        match = re.search(NS_pattern, json_string)
    if match:
        NS = match.group(1)
        match = re.search(MX_pattern, json_string)
    if match:
        MX = match.group(1)
        match = re.search(PTR_pattern, json_string)
    if match:
        PTR = match.group(1)
        match = re.search(SOA_pattern, json_string)
    if match:
        SOA = match.group(1)
        match = re.search(TXT_pattern, json_string)
    if match:
        TXT = match.group(1)
    data = {'A': A, 'AAA': AAA, 'NS': NS, 'MX': MX, 'PTR': PTR, 'SOA': SOA, 'TXT': TXT}
    json_output = json.dumps(data)
    return json_output

def nmap_ai_data_regex(json_string: str) -> Any:
    critical_score_pattern = '"critical score": \\["(.*?)"\\]'
    os_information_pattern = '"os information": \\["(.*?)"\\]'
    open_ports_pattern = '"open ports": \\["(.*?)"\\]'
    open_services_pattern = '"open services": \\["(.*?)"\\]'
    vulnerable_service_pattern = '"vulnerable service": \\["(.*?)"\\]'
    found_cve_pattern = '"found cve": \\["(.*?)"\\]'
    critical_score = None
    os_information = None
    open_ports = None
    open_services = None
    vulnerable_service = None
    found_cve = None
    match = re.search(critical_score_pattern, json_string)
    if match:
        critical_score = match.group(1)
    match = re.search(os_information_pattern, json_string)
    if match:
        os_information = match.group(1)
    match = re.search(open_ports_pattern, json_string)
    if match:
        open_ports = match.group(1)
    match = re.search(open_services_pattern, json_string)
    if match:
        open_services = match.group(1)
    match = re.search(vulnerable_service_pattern, json_string)
    if match:
        vulnerable_service = match.group(1)
    match = re.search(found_cve_pattern, json_string)
    if match:
        found_cve = match.group(1)
    data = {'critical score': critical_score, 'os information': os_information, 'open ports': open_ports, 'open services': open_services, 'vulnerable service': vulnerable_service, 'found cve': found_cve}
    json_output = json.dumps(data)
    return json_output

def jwt_ai_data_regex(json_string: str) -> Any:
    header_pattern = '"Header": \\{\\s*"alg": "(.*?)",\\s*"typ": "(.*?)"\\s*\\}'
    payload_pattern = '"Payload": \\{\\s*"iss": "(.*?)",\\s*"sub": "(.*?)",\\s*"aud": "(.*?)",\\s*"exp": "(.*?)",\\s*"nbf": "(.*?)",\\s*"iat": "(.*?)"\\s*\\}'
    signature_pattern = '"Signature": "(.*?)"'
    possible_attacks_pattern = '"PossibleAttacks": "(.*?)"'
    vulnerable_endpoints_pattern = '"VulnerableEndpoints": "(.*?)"'
    header = {}
    payload = {}
    signature = ''
    possible_attacks = ''
    vulnerable_endpoints = ''
    match_header = re.search(header_pattern, json_string)
    if match_header:
        header = {'alg': match_header.group(1), 'typ': match_header.group(2)}
    match_payload = re.search(payload_pattern, json_string)
    if match_payload:
        payload = {'iss': match_payload.group(1), 'sub': match_payload.group(2), 'aud': match_payload.group(3), 'exp': match_payload.group(4), 'nbf': match_payload.group(5), 'iat': match_payload.group(6)}
    match_signature = re.search(signature_pattern, json_string)
    if match_signature:
        signature = match_signature.group(1)
    match_attacks = re.search(possible_attacks_pattern, json_string)
    if match_attacks:
        possible_attacks = match_attacks.group(1)
    match_endpoints = re.search(vulnerable_endpoints_pattern, json_string)
    if match_endpoints:
        vulnerable_endpoints = match_endpoints.group(1)
    data = {'Header': header, 'Payload': payload, 'Signature': signature, 'PossibleAttacks': possible_attacks, 'VulnerableEndpoints': vulnerable_endpoints}
    json_output = json.dumps(data)
    return json_output

def dns_extract_data(json_string: str) -> Any:
    A_pattern = '"A": \\["(.*?)"\\]'
    AAA_pattern = '"AAA: \\["(.*?)"\\]'
    NS_pattern = '"NS": \\["(.*?)"\\]'
    MX_pattern = '"MX": \\["(.*?)"\\]'
    PTR_pattern = '"PTR": \\["(.*?)"\\]'
    SOA_pattern = '"SOA": \\["(.*?)"\\]'
    TXT_pattern = '"TXT": \\["(.*?)"\\]'
    A = None
    AAA = None
    NS = None
    MX = None
    PTR = None
    SOA = None
    TXT = None
    match = re.search(A_pattern, json_string)
    if match:
        A = match.group(1)
    match = re.search(AAA_pattern, json_string)
    if match:
        AAA = match.group(1)
    match = re.search(NS_pattern, json_string)
    if match:
        NS = match.group(1)
    match = re.search(MX_pattern, json_string)
    if match:
        MX = match.group(1)
    match = re.search(PTR_pattern, json_string)
    if match:
        PTR = match.group(1)
    match = re.search(SOA_pattern, json_string)
    if match:
        SOA = match.group(1)
    match = re.search(TXT_pattern, json_string)
    if match:
        TXT = match.group(1)
    data = {'A': A, 'AAA': AAA, 'NS': NS, 'MX': MX, 'PTR': PTR, 'SOA': SOA, 'TXT': TXT}
    json_output = json.dumps(data)
    return json_output

def port_extract_data(json_string: str) -> Any:
    critical_score_pattern = '"critical score": \\["(.*?)"\\]'
    os_information_pattern = '"os information": \\["(.*?)"\\]'
    open_ports_pattern = '"open ports": \\["(.*?)"\\]'
    open_services_pattern = '"open services": \\["(.*?)"\\]'
    vulnerable_service_pattern = '"vulnerable service": \\["(.*?)"\\]'
    found_cve_pattern = '"found cve": \\["(.*?)"\\]'
    critical_score = None
    os_information = None
    open_ports = None
    open_services = None
    vulnerable_service = None
    found_cve = None
    match = re.search(critical_score_pattern, json_string)
    if match:
        critical_score = match.group(1)
    match = re.search(os_information_pattern, json_string)
    if match:
        os_information = match.group(1)
    match = re.search(open_ports_pattern, json_string)
    if match:
        open_ports = match.group(1)
    match = re.search(open_services_pattern, json_string)
    if match:
        open_services = match.group(1)
    match = re.search(vulnerable_service_pattern, json_string)
    if match:
        vulnerable_service = match.group(1)
    match = re.search(found_cve_pattern, json_string)
    if match:
        found_cve = match.group(1)
    data = {'critical score': critical_score, 'os information': os_information, 'open ports': open_ports, 'open services': open_services, 'vulnerable service': vulnerable_service, 'found cve': found_cve}
    json_output = json.dumps(data)
    return json_output

def dns_ai_data_regex(json_string: str) -> Any:
    A_pattern = '"A": \\["(.*?)"\\]'
    AAA_pattern = '"AAA: \\["(.*?)"\\]'
    NS_pattern = '"NS": \\["(.*?)"\\]'
    MX_pattern = '"MX": \\["(.*?)"\\]'
    PTR_pattern = '"PTR": \\["(.*?)"\\]'
    SOA_pattern = '"SOA": \\["(.*?)"\\]'
    TXT_pattern = '"TXT": \\["(.*?)"\\]'
    A = None
    AAA = None
    NS = None
    MX = None
    PTR = None
    SOA = None
    TXT = None
    match = re.search(A_pattern, json_string)
    if match:
        A = match.group(1)
        match = re.search(AAA_pattern, json_string)
    if match:
        AAA = match.group(1)
        match = re.search(NS_pattern, json_string)
    if match:
        NS = match.group(1)
        match = re.search(MX_pattern, json_string)
    if match:
        MX = match.group(1)
        match = re.search(PTR_pattern, json_string)
    if match:
        PTR = match.group(1)
        match = re.search(SOA_pattern, json_string)
    if match:
        SOA = match.group(1)
        match = re.search(TXT_pattern, json_string)
    if match:
        TXT = match.group(1)
    data = {'A': A, 'AAA': AAA, 'NS': NS, 'MX': MX, 'PTR': PTR, 'SOA': SOA, 'TXT': TXT}
    json_output = json.dumps(data)
    return json_output

def nmap_ai_data_regex(json_string: str) -> Any:
    critical_score_pattern = '"critical score": \\["(.*?)"\\]'
    os_information_pattern = '"os information": \\["(.*?)"\\]'
    open_ports_pattern = '"open ports": \\["(.*?)"\\]'
    open_services_pattern = '"open services": \\["(.*?)"\\]'
    vulnerable_service_pattern = '"vulnerable service": \\["(.*?)"\\]'
    found_cve_pattern = '"found cve": \\["(.*?)"\\]'
    critical_score = None
    os_information = None
    open_ports = None
    open_services = None
    vulnerable_service = None
    found_cve = None
    match = re.search(critical_score_pattern, json_string)
    if match:
        critical_score = match.group(1)
    match = re.search(os_information_pattern, json_string)
    if match:
        os_information = match.group(1)
    match = re.search(open_ports_pattern, json_string)
    if match:
        open_ports = match.group(1)
    match = re.search(open_services_pattern, json_string)
    if match:
        open_services = match.group(1)
    match = re.search(vulnerable_service_pattern, json_string)
    if match:
        vulnerable_service = match.group(1)
    match = re.search(found_cve_pattern, json_string)
    if match:
        found_cve = match.group(1)
    data = {'critical score': critical_score, 'os information': os_information, 'open ports': open_ports, 'open services': open_services, 'vulnerable service': vulnerable_service, 'found cve': found_cve}
    json_output = json.dumps(data)
    return json_output

def jwt_ai_data_regex(json_string: str) -> Any:
    header_pattern = '"Header": \\{\\s*"alg": "(.*?)",\\s*"typ": "(.*?)"\\s*\\}'
    payload_pattern = '"Payload": \\{\\s*"iss": "(.*?)",\\s*"sub": "(.*?)",\\s*"aud": "(.*?)",\\s*"exp": "(.*?)",\\s*"nbf": "(.*?)",\\s*"iat": "(.*?)"\\s*\\}'
    signature_pattern = '"Signature": "(.*?)"'
    possible_attacks_pattern = '"PossibleAttacks": "(.*?)"'
    vulnerable_endpoints_pattern = '"VulnerableEndpoints": "(.*?)"'
    header = {}
    payload = {}
    signature = ''
    possible_attacks = ''
    vulnerable_endpoints = ''
    match_header = re.search(header_pattern, json_string)
    if match_header:
        header = {'alg': match_header.group(1), 'typ': match_header.group(2)}
    match_payload = re.search(payload_pattern, json_string)
    if match_payload:
        payload = {'iss': match_payload.group(1), 'sub': match_payload.group(2), 'aud': match_payload.group(3), 'exp': match_payload.group(4), 'nbf': match_payload.group(5), 'iat': match_payload.group(6)}
    match_signature = re.search(signature_pattern, json_string)
    if match_signature:
        signature = match_signature.group(1)
    match_attacks = re.search(possible_attacks_pattern, json_string)
    if match_attacks:
        possible_attacks = match_attacks.group(1)
    match_endpoints = re.search(vulnerable_endpoints_pattern, json_string)
    if match_endpoints:
        vulnerable_endpoints = match_endpoints.group(1)
    data = {'Header': header, 'Payload': payload, 'Signature': signature, 'PossibleAttacks': possible_attacks, 'VulnerableEndpoints': vulnerable_endpoints}
    json_output = json.dumps(data)
    return json_output

