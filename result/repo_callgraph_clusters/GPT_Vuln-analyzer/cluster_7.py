# Cluster 7

def output_save(output: str) -> None:
    if output == 'Done':
        output_data = 'Status: Successful'
        output_textbox.insert('1.0', output_data)
    else:
        output_textbox.delete('1.0', 'end')
        json_data = json.loads(output)
        formatted_json = json.dumps(json_data, indent=2)
        output_textbox.insert('1.0', formatted_json)

def select_frame_by_name(name):
    global frame
    frame.destroy()
    frame = customtkinter.CTkFrame(master=input_frame)
    frame.pack(pady=20, padx=20, fill='both', expand=True)
    label_text = f'GVA System - {name.capitalize()}'
    label = customtkinter.CTkLabel(master=frame, text=label_text)
    label.pack(pady=12, padx=10)
    entry2 = customtkinter.CTkEntry(master=frame, placeholder_text='Target/capfile/token')
    entry2.pack(pady=12, padx=10)
    if name in ['nmap', 'dns', 'jwt']:
        ai_choices_val = ['openai', 'bard', 'llama-api']
        entry_ai = customtkinter.CTkComboBox(master=frame, values=ai_choices_val, state='readonly')
        entry_ai.set('Select AI Input')
        entry_ai.pack(pady=12, padx=10)
    else:
        entry_ai = None
    entry3 = None
    entry5 = None
    if name == 'nmap':
        entry3 = customtkinter.CTkEntry(master=frame, placeholder_text='Profile')
        entry3.pack(pady=12, padx=10)
    elif name == 'sub':
        entry3 = customtkinter.CTkEntry(master=frame, placeholder_text='File Location')
        entry3.pack(pady=12, padx=10)
    elif name == 'pcap':
        entry5 = customtkinter.CTkEntry(master=frame, placeholder_text='Save Location')
        entry5.pack(pady=12, padx=10)
    button = customtkinter.CTkButton(master=frame, text='Run', command=lambda: application(attack=name, entry2=entry2, entry3=entry3, entry_ai=entry_ai, entry5=entry5))
    button.pack(pady=12, padx=10)

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

class CTkTable(customtkinter.CTkFrame):

    def __init__(self, master: any, row: int=None, column: int=None, padx: int=1, pady: int=0, values: list=[[None]], colors: list=[None, None], orientation: str='horizontal', color_phase: str='horizontal', border_width: int=0, text_color: str=None, border_color: str=None, font: tuple=None, header_color: str=None, corner_radius: int=25, write: str=False, command=None, anchor='c', hover_color=None, hover=False, justify='center', wraplength: int=1000, **kwargs):
        super().__init__(master, fg_color='transparent')
        self.master = master
        self.rows = row if row else len(values)
        self.columns = column if column else len(values[0])
        self.padx = padx
        self.pady = pady
        self.command = command
        self.values = values
        self.colors = colors
        self.header_color = header_color
        self.phase = color_phase
        self.corner = corner_radius
        self.write = write
        self.justify = justify
        if self.write:
            border_width = border_width = +1
        if hover_color is not None:
            hover = True
        else:
            hover = False
        self.anchor = anchor
        self.wraplength = wraplength
        self.hover = hover
        self.border_width = border_width
        self.hover_color = customtkinter.ThemeManager.theme['CTkButton']['hover_color'] if hover_color is None else hover_color
        self.orient = orientation
        self.border_color = customtkinter.ThemeManager.theme['CTkButton']['border_color'] if border_color is None else border_color
        self.text_color = customtkinter.ThemeManager.theme['CTkLabel']['text_color'] if text_color is None else text_color
        self.font = font
        self.data = {}
        self.fg_color = customtkinter.ThemeManager.theme['CTkFrame']['fg_color'] if not self.colors[0] else self.colors[0]
        self.fg_color2 = customtkinter.ThemeManager.theme['CTkFrame']['top_fg_color'] if not self.colors[1] else self.colors[1]
        if self.colors[0] is None and self.colors[1] is None:
            if self.fg_color == self.master.cget('fg_color'):
                self.fg_color = customtkinter.ThemeManager.theme['CTk']['fg_color']
            if self.fg_color2 == self.master.cget('fg_color'):
                self.fg_color2 = customtkinter.ThemeManager.theme['CTk']['fg_color']
        self.frame = {}
        self.draw_table(**kwargs)

    def draw_table(self, **kwargs):
        """ draw the table """
        for i in range(self.rows):
            for j in range(self.columns):
                if self.phase == 'horizontal':
                    if i % 2 == 0:
                        fg = self.fg_color
                    else:
                        fg = self.fg_color2
                elif j % 2 == 0:
                    fg = self.fg_color
                else:
                    fg = self.fg_color2
                if self.header_color:
                    if self.orient == 'horizontal':
                        if i == 0:
                            fg = self.header_color
                    elif j == 0:
                        fg = self.header_color
                corner_radius = self.corner
                if i == 0 and j == 0:
                    corners = ['', fg, fg, fg]
                elif i == self.rows - 1 and j == self.columns - 1:
                    corners = [fg, fg, '', fg]
                elif i == self.rows - 1 and j == 0:
                    corners = [fg, fg, fg, '']
                elif i == 0 and j == self.columns - 1:
                    corners = [fg, '', fg, fg]
                else:
                    corners = [fg, fg, fg, fg]
                    corner_radius = 0
                if self.values:
                    try:
                        if self.orient == 'horizontal':
                            value = self.values[i][j]
                        else:
                            value = self.values[j][i]
                    except IndexError:
                        value = ' '
                else:
                    value = ' '
                if value == '':
                    value = ' '
                if (i, j) in self.data.keys():
                    if self.data[i, j]['args']:
                        args = self.data[i, j]['args']
                    else:
                        args = copy.deepcopy(kwargs)
                else:
                    args = copy.deepcopy(kwargs)
                self.data[i, j] = {'row': i, 'column': j, 'value': value, 'args': args}
                args = self.data[i, j]['args']
                if 'text_color' not in args:
                    args['text_color'] = self.text_color
                if 'border_width' not in args:
                    args['border_width'] = self.border_width
                if 'border_color' not in args:
                    args['border_color'] = self.border_color
                if 'fg_color' not in args:
                    args['fg_color'] = fg
                if self.write:
                    if 'justify' not in args:
                        args['justify'] = self.justify
                    if self.padx == 1:
                        self.padx = 0
                    self.frame[i, j] = customtkinter.CTkEntry(self, font=self.font, corner_radius=0, **args)
                    self.frame[i, j].insert('0', value)
                    self.frame[i, j].bind('<Key>', lambda e, row=i, column=j, data=self.data: self.after(100, lambda: self.manipulate_data(row, column)))
                    self.frame[i, j].grid(column=j, row=i, padx=self.padx, pady=self.pady, sticky='nsew')
                    if self.header_color:
                        if i == 0:
                            self.frame[i, j].configure(state='readonly')
                else:
                    if 'anchor' not in args:
                        args['anchor'] = self.anchor
                    if 'hover_color' not in args:
                        args['hover_color'] = self.hover_color
                    if 'hover' not in args:
                        args['hover'] = self.hover
                    self.frame[i, j] = customtkinter.CTkButton(self, background_corner_colors=corners, font=self.font, corner_radius=corner_radius, text=value, command=(lambda e=self.data[i, j]: self.command(e)) if self.command else None, **args)
                    self.frame[i, j].grid(column=j, row=i, padx=self.padx, pady=self.pady, sticky='nsew')
                    self.frame[i, j]._text_label.config(wraplength=self.wraplength)
                self.rowconfigure(i, weight=1)
                self.columnconfigure(j, weight=1)

    def manipulate_data(self, row, column):
        """ entry callback """
        self.update_data()
        data = self.data[row, column]
        if self.command:
            self.command(data)

    def update_data(self):
        """ update the data when values are changes """
        for i in self.frame:
            if self.write:
                self.data[i]['value'] = self.frame[i].get()
            else:
                self.data[i]['value'] = self.frame[i].cget('text')
        self.values = []
        for i in range(self.rows):
            row_data = []
            for j in range(self.columns):
                row_data.append(self.data[i, j]['value'])
            self.values.append(row_data)

    def edit_row(self, row, value=None, **kwargs):
        """ edit all parameters of a single row """
        for i in range(self.columns):
            self.frame[row, i].configure(**kwargs)
            self.data[row, i]['args'].update(kwargs)
            if value:
                self.insert(row, i, value)
        self.update_data()

    def edit_column(self, column, value=None, **kwargs):
        """ edit all parameters of a single column """
        for i in range(self.rows):
            self.frame[i, column].configure(**kwargs)
            self.data[i, column]['args'].update(kwargs)
            if value:
                self.insert(i, column, value)
        self.update_data()

    def update_values(self, values, **kwargs):
        """ update all values at once """
        for i in self.frame.values():
            i.destroy()
        self.frame = {}
        self.values = values
        self.draw_table(**kwargs)
        self.update_data()

    def add_row(self, values, index=None, **kwargs):
        """ add a new row """
        for i in self.frame.values():
            i.destroy()
        self.frame = {}
        if index is None:
            index = len(self.values)
        try:
            self.values.insert(index, values)
            self.rows += 1
        except IndexError:
            pass
        self.draw_table(**kwargs)
        self.update_data()

    def add_column(self, values, index=None, **kwargs):
        """ add a new column """
        for i in self.frame.values():
            i.destroy()
        self.frame = {}
        if index is None:
            index = len(self.values[0])
        x = 0
        for i in self.values:
            try:
                i.insert(index, values[x])
                x += 1
            except IndexError:
                pass
        self.columns += 1
        self.draw_table(**kwargs)
        self.update_data()

    def delete_row(self, index=None):
        """ delete a particular row """
        if index is None or index >= len(self.values):
            index = len(self.values) - 1
        self.values.pop(index)
        for i in self.frame.values():
            i.destroy()
        self.rows -= 1
        self.frame = {}
        self.draw_table()
        self.update_data()

    def delete_column(self, index=None):
        """ delete a particular column """
        if index is None or index >= len(self.values[0]):
            index = len(self.values) - 1
        for i in self.values:
            i.pop(index)
        for i in self.frame.values():
            i.destroy()
        self.columns -= 1
        self.frame = {}
        self.draw_table()
        self.update_data()

    def delete_rows(self, indices=[]):
        """ delete a particular row """
        if len(indices) == 0:
            return
        self.values = [v for i, v in enumerate(self.values) if i not in indices]
        for i in indices:
            for j in range(self.columns):
                self.data[i, j]['args'] = ''
        for i in self.frame.values():
            i.destroy()
        self.rows -= len(set(indices))
        self.frame = {}
        self.draw_table()
        self.update_data()

    def delete_columns(self, indices=[]):
        """ delete a particular column """
        if len(indices) == 0:
            return
        x = 0
        for k in self.values:
            self.values[x] = [v for i, v in enumerate(k) if i not in indices]
            x += 1
        for i in indices:
            for j in range(self.rows):
                self.data[j, i]['args'] = ''
        for i in self.frame.values():
            i.destroy()
        self.columns -= len(set(indices))
        self.frame = {}
        self.draw_table()
        self.update_data()

    def get_row(self, row):
        return self.values[row]

    def get_column(self, column):
        column_list = []
        for i in self.values:
            column_list.append(i[column])
        return column_list

    def select_row(self, row):
        self.edit_row(row, fg_color=self.hover_color)
        if self.orient != 'horizontal':
            if self.header_color:
                self.edit_column(0, fg_color=self.header_color)
        elif self.header_color:
            self.edit_row(0, fg_color=self.header_color)
        return self.get_row(row)

    def select_column(self, column):
        self.edit_column(column, fg_color=self.hover_color)
        if self.orient != 'horizontal':
            if self.header_color:
                self.edit_column(0, fg_color=self.header_color)
        elif self.header_color:
            self.edit_row(0, fg_color=self.header_color)
        return self.get_column(column)

    def deselect_row(self, row):
        self.edit_row(row, fg_color=self.fg_color if row % 2 == 0 else self.fg_color2)
        if self.orient != 'horizontal':
            if self.header_color:
                self.edit_column(0, fg_color=self.header_color)
        elif self.header_color:
            self.edit_row(0, fg_color=self.header_color)

    def deselect_column(self, column):
        for i in range(self.rows):
            self.frame[i, column].configure(fg_color=self.fg_color if i % 2 == 0 else self.fg_color2)
        if self.orient != 'horizontal':
            if self.header_color:
                self.edit_column(0, fg_color=self.header_color)
        elif self.header_color:
            self.edit_row(0, fg_color=self.header_color)

    def select(self, row, column):
        self.frame[row, column].configure(fg_color=self.hover_color)

    def deselect(self, row, column):
        self.frame[row, column].configure(fg_color=self.fg_color if row % 2 == 0 else self.fg_color2)

    def insert(self, row, column, value, **kwargs):
        """ insert value in a specific block [row, column] """
        if self.write:
            self.frame[row, column].delete(0, customtkinter.END)
            self.frame[row, column].insert(0, value)
            self.frame[row, column].configure(**kwargs)
        else:
            self.frame[row, column].configure(text=value, **kwargs)
        if kwargs:
            self.data[row, column]['args'].update(kwargs)
        self.update_data()

    def delete(self, row, column, **kwargs):
        """ delete a value from a specific block [row, column] """
        if self.write:
            self.frame[row, column].delete(0, customtkinter.END)
            self.frame[row, column].configure(**kwargs)
        else:
            self.frame[row, column].configure(text='', **kwargs)
        if kwargs:
            self.data[row, column]['args'].update(kwargs)
        self.update_data()

    def get(self, row=None, column=None):
        if row and column:
            return self.data[row, column]['value']
        else:
            return self.values

    def configure(self, **kwargs):
        """ configure table widget attributes"""
        if 'colors' in kwargs:
            self.colors = kwargs.pop('colors')
            self.fg_color = self.colors[0]
            self.fg_color2 = self.colors[1]
        if 'header_color' in kwargs:
            self.header_color = kwargs.pop('header_color')
        if 'rows' in kwargs:
            self.rows = kwargs.pop('rows')
        if 'columns' in kwargs:
            self.columns = kwargs.pop('columns')
        if 'values' in kwargs:
            self.values = kwargs.pop('values')
        if 'padx' in kwargs:
            self.padx = kwargs.pop('padx')
        if 'padx' in kwargs:
            self.pady = kwargs.pop('pady')
        if 'wraplength' in kwargs:
            self.wraplength = kwargs.pop('wraplength')
        self.update_values(self.values, **kwargs)

def __init__(self, master: any, row: int=None, column: int=None, padx: int=1, pady: int=0, values: list=[[None]], colors: list=[None, None], orientation: str='horizontal', color_phase: str='horizontal', border_width: int=0, text_color: str=None, border_color: str=None, font: tuple=None, header_color: str=None, corner_radius: int=25, write: str=False, command=None, anchor='c', hover_color=None, hover=False, justify='center', wraplength: int=1000, **kwargs):
    super().__init__(master, fg_color='transparent')
    self.master = master
    self.rows = row if row else len(values)
    self.columns = column if column else len(values[0])
    self.padx = padx
    self.pady = pady
    self.command = command
    self.values = values
    self.colors = colors
    self.header_color = header_color
    self.phase = color_phase
    self.corner = corner_radius
    self.write = write
    self.justify = justify
    if self.write:
        border_width = border_width = +1
    if hover_color is not None:
        hover = True
    else:
        hover = False
    self.anchor = anchor
    self.wraplength = wraplength
    self.hover = hover
    self.border_width = border_width
    self.hover_color = customtkinter.ThemeManager.theme['CTkButton']['hover_color'] if hover_color is None else hover_color
    self.orient = orientation
    self.border_color = customtkinter.ThemeManager.theme['CTkButton']['border_color'] if border_color is None else border_color
    self.text_color = customtkinter.ThemeManager.theme['CTkLabel']['text_color'] if text_color is None else text_color
    self.font = font
    self.data = {}
    self.fg_color = customtkinter.ThemeManager.theme['CTkFrame']['fg_color'] if not self.colors[0] else self.colors[0]
    self.fg_color2 = customtkinter.ThemeManager.theme['CTkFrame']['top_fg_color'] if not self.colors[1] else self.colors[1]
    if self.colors[0] is None and self.colors[1] is None:
        if self.fg_color == self.master.cget('fg_color'):
            self.fg_color = customtkinter.ThemeManager.theme['CTk']['fg_color']
        if self.fg_color2 == self.master.cget('fg_color'):
            self.fg_color2 = customtkinter.ThemeManager.theme['CTk']['fg_color']
    self.frame = {}
    self.draw_table(**kwargs)

def draw_table(self, **kwargs):
    """ draw the table """
    for i in range(self.rows):
        for j in range(self.columns):
            if self.phase == 'horizontal':
                if i % 2 == 0:
                    fg = self.fg_color
                else:
                    fg = self.fg_color2
            elif j % 2 == 0:
                fg = self.fg_color
            else:
                fg = self.fg_color2
            if self.header_color:
                if self.orient == 'horizontal':
                    if i == 0:
                        fg = self.header_color
                elif j == 0:
                    fg = self.header_color
            corner_radius = self.corner
            if i == 0 and j == 0:
                corners = ['', fg, fg, fg]
            elif i == self.rows - 1 and j == self.columns - 1:
                corners = [fg, fg, '', fg]
            elif i == self.rows - 1 and j == 0:
                corners = [fg, fg, fg, '']
            elif i == 0 and j == self.columns - 1:
                corners = [fg, '', fg, fg]
            else:
                corners = [fg, fg, fg, fg]
                corner_radius = 0
            if self.values:
                try:
                    if self.orient == 'horizontal':
                        value = self.values[i][j]
                    else:
                        value = self.values[j][i]
                except IndexError:
                    value = ' '
            else:
                value = ' '
            if value == '':
                value = ' '
            if (i, j) in self.data.keys():
                if self.data[i, j]['args']:
                    args = self.data[i, j]['args']
                else:
                    args = copy.deepcopy(kwargs)
            else:
                args = copy.deepcopy(kwargs)
            self.data[i, j] = {'row': i, 'column': j, 'value': value, 'args': args}
            args = self.data[i, j]['args']
            if 'text_color' not in args:
                args['text_color'] = self.text_color
            if 'border_width' not in args:
                args['border_width'] = self.border_width
            if 'border_color' not in args:
                args['border_color'] = self.border_color
            if 'fg_color' not in args:
                args['fg_color'] = fg
            if self.write:
                if 'justify' not in args:
                    args['justify'] = self.justify
                if self.padx == 1:
                    self.padx = 0
                self.frame[i, j] = customtkinter.CTkEntry(self, font=self.font, corner_radius=0, **args)
                self.frame[i, j].insert('0', value)
                self.frame[i, j].bind('<Key>', lambda e, row=i, column=j, data=self.data: self.after(100, lambda: self.manipulate_data(row, column)))
                self.frame[i, j].grid(column=j, row=i, padx=self.padx, pady=self.pady, sticky='nsew')
                if self.header_color:
                    if i == 0:
                        self.frame[i, j].configure(state='readonly')
            else:
                if 'anchor' not in args:
                    args['anchor'] = self.anchor
                if 'hover_color' not in args:
                    args['hover_color'] = self.hover_color
                if 'hover' not in args:
                    args['hover'] = self.hover
                self.frame[i, j] = customtkinter.CTkButton(self, background_corner_colors=corners, font=self.font, corner_radius=corner_radius, text=value, command=(lambda e=self.data[i, j]: self.command(e)) if self.command else None, **args)
                self.frame[i, j].grid(column=j, row=i, padx=self.padx, pady=self.pady, sticky='nsew')
                self.frame[i, j]._text_label.config(wraplength=self.wraplength)
            self.rowconfigure(i, weight=1)
            self.columnconfigure(j, weight=1)

def manipulate_data(self, row, column):
    """ entry callback """
    self.update_data()
    data = self.data[row, column]
    if self.command:
        self.command(data)

def update_data(self):
    """ update the data when values are changes """
    for i in self.frame:
        if self.write:
            self.data[i]['value'] = self.frame[i].get()
        else:
            self.data[i]['value'] = self.frame[i].cget('text')
    self.values = []
    for i in range(self.rows):
        row_data = []
        for j in range(self.columns):
            row_data.append(self.data[i, j]['value'])
        self.values.append(row_data)

def edit_row(self, row, value=None, **kwargs):
    """ edit all parameters of a single row """
    for i in range(self.columns):
        self.frame[row, i].configure(**kwargs)
        self.data[row, i]['args'].update(kwargs)
        if value:
            self.insert(row, i, value)
    self.update_data()

def edit_column(self, column, value=None, **kwargs):
    """ edit all parameters of a single column """
    for i in range(self.rows):
        self.frame[i, column].configure(**kwargs)
        self.data[i, column]['args'].update(kwargs)
        if value:
            self.insert(i, column, value)
    self.update_data()

def update_values(self, values, **kwargs):
    """ update all values at once """
    for i in self.frame.values():
        i.destroy()
    self.frame = {}
    self.values = values
    self.draw_table(**kwargs)
    self.update_data()

def add_row(self, values, index=None, **kwargs):
    """ add a new row """
    for i in self.frame.values():
        i.destroy()
    self.frame = {}
    if index is None:
        index = len(self.values)
    try:
        self.values.insert(index, values)
        self.rows += 1
    except IndexError:
        pass
    self.draw_table(**kwargs)
    self.update_data()

def add_column(self, values, index=None, **kwargs):
    """ add a new column """
    for i in self.frame.values():
        i.destroy()
    self.frame = {}
    if index is None:
        index = len(self.values[0])
    x = 0
    for i in self.values:
        try:
            i.insert(index, values[x])
            x += 1
        except IndexError:
            pass
    self.columns += 1
    self.draw_table(**kwargs)
    self.update_data()

def delete_row(self, index=None):
    """ delete a particular row """
    if index is None or index >= len(self.values):
        index = len(self.values) - 1
    self.values.pop(index)
    for i in self.frame.values():
        i.destroy()
    self.rows -= 1
    self.frame = {}
    self.draw_table()
    self.update_data()

def delete_column(self, index=None):
    """ delete a particular column """
    if index is None or index >= len(self.values[0]):
        index = len(self.values) - 1
    for i in self.values:
        i.pop(index)
    for i in self.frame.values():
        i.destroy()
    self.columns -= 1
    self.frame = {}
    self.draw_table()
    self.update_data()

def delete_rows(self, indices=[]):
    """ delete a particular row """
    if len(indices) == 0:
        return
    self.values = [v for i, v in enumerate(self.values) if i not in indices]
    for i in indices:
        for j in range(self.columns):
            self.data[i, j]['args'] = ''
    for i in self.frame.values():
        i.destroy()
    self.rows -= len(set(indices))
    self.frame = {}
    self.draw_table()
    self.update_data()

def delete_columns(self, indices=[]):
    """ delete a particular column """
    if len(indices) == 0:
        return
    x = 0
    for k in self.values:
        self.values[x] = [v for i, v in enumerate(k) if i not in indices]
        x += 1
    for i in indices:
        for j in range(self.rows):
            self.data[j, i]['args'] = ''
    for i in self.frame.values():
        i.destroy()
    self.columns -= len(set(indices))
    self.frame = {}
    self.draw_table()
    self.update_data()

def select_row(self, row):
    self.edit_row(row, fg_color=self.hover_color)
    if self.orient != 'horizontal':
        if self.header_color:
            self.edit_column(0, fg_color=self.header_color)
    elif self.header_color:
        self.edit_row(0, fg_color=self.header_color)
    return self.get_row(row)

def select_column(self, column):
    self.edit_column(column, fg_color=self.hover_color)
    if self.orient != 'horizontal':
        if self.header_color:
            self.edit_column(0, fg_color=self.header_color)
    elif self.header_color:
        self.edit_row(0, fg_color=self.header_color)
    return self.get_column(column)

def deselect_row(self, row):
    self.edit_row(row, fg_color=self.fg_color if row % 2 == 0 else self.fg_color2)
    if self.orient != 'horizontal':
        if self.header_color:
            self.edit_column(0, fg_color=self.header_color)
    elif self.header_color:
        self.edit_row(0, fg_color=self.header_color)

def deselect_column(self, column):
    for i in range(self.rows):
        self.frame[i, column].configure(fg_color=self.fg_color if i % 2 == 0 else self.fg_color2)
    if self.orient != 'horizontal':
        if self.header_color:
            self.edit_column(0, fg_color=self.header_color)
    elif self.header_color:
        self.edit_row(0, fg_color=self.header_color)

def select(self, row, column):
    self.frame[row, column].configure(fg_color=self.hover_color)

def deselect(self, row, column):
    self.frame[row, column].configure(fg_color=self.fg_color if row % 2 == 0 else self.fg_color2)

def insert(self, row, column, value, **kwargs):
    """ insert value in a specific block [row, column] """
    if self.write:
        self.frame[row, column].delete(0, customtkinter.END)
        self.frame[row, column].insert(0, value)
        self.frame[row, column].configure(**kwargs)
    else:
        self.frame[row, column].configure(text=value, **kwargs)
    if kwargs:
        self.data[row, column]['args'].update(kwargs)
    self.update_data()

def delete(self, row, column, **kwargs):
    """ delete a value from a specific block [row, column] """
    if self.write:
        self.frame[row, column].delete(0, customtkinter.END)
        self.frame[row, column].configure(**kwargs)
    else:
        self.frame[row, column].configure(text='', **kwargs)
    if kwargs:
        self.data[row, column]['args'].update(kwargs)
    self.update_data()

def configure(self, **kwargs):
    """ configure table widget attributes"""
    if 'colors' in kwargs:
        self.colors = kwargs.pop('colors')
        self.fg_color = self.colors[0]
        self.fg_color2 = self.colors[1]
    if 'header_color' in kwargs:
        self.header_color = kwargs.pop('header_color')
    if 'rows' in kwargs:
        self.rows = kwargs.pop('rows')
    if 'columns' in kwargs:
        self.columns = kwargs.pop('columns')
    if 'values' in kwargs:
        self.values = kwargs.pop('values')
    if 'padx' in kwargs:
        self.padx = kwargs.pop('padx')
    if 'padx' in kwargs:
        self.pady = kwargs.pop('pady')
    if 'wraplength' in kwargs:
        self.wraplength = kwargs.pop('wraplength')
    self.update_values(self.values, **kwargs)

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

