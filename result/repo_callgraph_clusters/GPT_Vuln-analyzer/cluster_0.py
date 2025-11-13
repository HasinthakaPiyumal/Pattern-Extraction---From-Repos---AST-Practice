# Cluster 0

def parse_arguments():
    parser = argparse.ArgumentParser(description='Python-Nmap and chatGPT integrated Vulnerability scanner')
    parser.add_argument('--target', type=str, help='Target IP, hostname, JWT token or pcap file location')
    parser.add_argument('--profile', type=int, default=1, help='Enter Profile of scan 1-13 (Default: 1)')
    parser.add_argument('--attack', type=str, help='Attack type: nmap, dns, sub, jwt, pcap, passcracker')
    parser.add_argument('--sub_list', type=str, default=DEFAULT_LIST_LOC, help='Path to the subdomain list file (txt)')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_LOC, help='Pcap analysis output file')
    parser.add_argument('--rich_menu', type=str, help='Shows a clean help menu using rich')
    parser.add_argument('--menu', action='store_true', default=False, help='Terminal Interactive Menu')
    parser.add_argument('--ai', type=str, default='openai', help='AI options: openai, bard, llama, llama-api')
    parser.add_argument('--password_hash', help='Password hash')
    parser.add_argument('--wordlist_file', help='Wordlist File')
    parser.add_argument('--algorithm', choices=hashlib.algorithms_guaranteed, help='Hash algorithm')
    parser.add_argument('--salt', help='Salt Value')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--complexity', action='store_true', help='Check for password complexity')
    parser.add_argument('--brute_force', action='store_true', help='Perform a brute force attack')
    parser.add_argument('--min_length', type=int, default=1, help='Minimum password length for brute force attack')
    parser.add_argument('--max_length', type=int, default=6, help='Minimum password length for brute force attack')
    parser.add_argument('--character_set', default='abcdefghijklmnopqrstuvwxyz0123456789', help='Character set for brute force attack')
    return parser.parse_args()

def handle_attack(attack_type, target, ai, api_keys, additional_params=None):
    additional_params = additional_params or {}
    if attack_type == 'geo':
        output = geo_ip.geoip(api_keys['geoip_api_key'], target)
        asset_codes.print_output(attack_type.capitalize(), str(output), ai)
    elif attack_type == 'nmap':
        output = port_scanner.scanner(ip=target, profile=additional_params.get('profile'), akey=api_keys['openai_api_key'], bkey=api_keys['bard_api_key'], lkey=api_keys['runpod_api_key'], lendpoint=api_keys['runpod_endpoint_id'], AI=ai)
        asset_codes.print_output(attack_type.capitalize(), str(output), ai)
    elif attack_type == 'dns':
        output = dns_enum.dns_resolver(target=target, akey=api_keys['openai_api_key'], bkey=api_keys['bard_api_key'], lkey=api_keys['runpod_api_key'], lendpoint=api_keys['runpod_endpoint_id'], AI=ai)
        asset_codes.print_output(attack_type.capitalize(), str(output), ai)
    elif attack_type == 'sub':
        output = sub_recon.sub_enumerator(target, additional_params.get('list_loc'))
        console.print(output, style='bold underline')
        asset_codes.print_output(attack_type.capitalize(), str(output), ai)
    elif attack_type == 'jwt':
        output = jwt_analyzer.analyze(token=target, openai_api_token=api_keys['openai_api_key'], bard_api_token=api_keys['bard_api_key'], llama_api_token=api_keys['runpod_api_key'], llama_endpoint=api_keys['runpod_endpoint_id'], AI=ai)
        asset_codes.print_output('JWT', output, ai)
    elif attack_type == 'pcap':
        packet_analysis.perform_full_analysis(pcap_path=target, json_path=additional_params.get('output_loc'))
        return 'Done'
    elif attack_type == 'passcracker':
        hash = additional_params.get('password_hash')
        wordlist = additional_params.get('wordlist_file')
        salt = additional_params.get('salt')
        parallel = additional_params.get('parallel')
        complexity = additional_params.get('complexity')
        min_length = additional_params.get('min_length')
        max_length = additional_params.get('max_length')
        character_set = additional_params.get('charecter_set')
        brute_force = additional_params.get('brute_force')
        algorithm = additional_params.get('algorithm')
        Cracker = PasswordCracker(password_hash=hash, wordlist_file=wordlist, algorithm=algorithm, salt=salt, parallel=parallel, complexity_check=complexity)
        if brute_force:
            Cracker.crack_passwords_with_brute_force(min_length, max_length, character_set)
        else:
            Cracker.crack_passwords_with_wordlist()
        Cracker.print_statistics()

def application(attack, entry2, entry3, entry_ai, entry5):
    try:
        target = entry2.get()
        profile = entry3.get() if entry3 else None
        save_loc = entry5.get() if entry5 else None
        ai_choices = entry_ai.get() if entry_ai else None
        if attack == 'geo':
            geo_output: str = geo_ip_recon.geoip(gkey, target)
            output_save(str(geo_output))
        elif attack == 'nmap':
            p1_out = port_scanner.scanner(ip=target, profile=int(profile) if profile else None, akey=akey, bkey=bkey, lkey=lkey, lendpoint=lendpoint, AI=ai_choices)
            output_save(p1_out)
        elif attack == 'dns':
            dns_output: str = dns_enum.dns_resolver(target=target, akey=akey, bkey=bkey, lkey=lkey, lendpoint=lendpoint, AI=ai_choices)
            output_save(dns_output)
        elif attack == 'sub':
            sub_output: str = sub_recon.sub_enumerator(target, list_loc)
            output_save(sub_output)
        elif attack == 'jwt':
            output: str = jwt_analyzer.analyze(token=target, openai_api_token=akey, bard_api_token=bkey, llama_api_token=lkey, llama_endpoint=lendpoint, AI=ai_choices)
            output_save(output)
        elif attack == 'pcap':
            packet_analysis.perform_full_analysis(pcap_path=target, json_path=save_loc)
            output_save('Done')
    except KeyboardInterrupt:
        print('Keyboard Interrupt detected ...')

def main():
    parser = argparse.ArgumentParser(description='Password cracking source PassBreaker')
    parser.add_argument('password_hash', help='Password hash')
    parser.add_argument('wordlist_file', help='Wordlist File')
    parser.add_argument('--algorithm', choices=hashlib.algorithms_guaranteed, required=True, help='Hash algorithm')
    parser.add_argument('-s', '--salt', help='Salt Value')
    parser.add_argument('-p', '--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('-c', '--complexity', action='store_true', help='Check for password complexity')
    parser.add_argument('-b', '--brute-force', action='store_true', help='Perform a brute force attack')
    parser.add_argument('--min-length', type=int, default=1, help='Minimum password length for brute force attack')
    parser.add_argument('--max-length', type=int, default=6, help='Minimum password length for brute force attack')
    parser.add_argument('--character-set', default='abcdefghijklmnopqrstuvwxyz0123456789', help='Character set for brute force attack')
    args = parser.parse_args()
    cracker = PasswordCracker(args.password_hash, args.wordlist_file, args.algorithm, args.salt, args.parallel, args.complexity)
    if args.brute_force:
        cracker.crack_passwords_with_brute_force(args.min_length, args.max_length, args.character_set)
    else:
        cracker.crack_passwords_with_wordlist()
    cracker.print_statistics()

def application() -> None:
    try:
        apikey = entry1.get()
        openai.api_key = apikey
        target = entry2.get()
        attack = entry5.get()
        outputf = str(entry4.get())
        match attack:
            case 'geo':
                val = geoip(apikey, target)
                print(val)
                output_save(val, outputf)
            case 'nmap':
                p = int(entry3.get())
                match p:
                    case 1:
                        val = scanner(target, 1, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 2:
                        val = scanner(target, 2, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 3:
                        val = scanner(target, 3, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 4:
                        val = scanner(target, 4, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 5:
                        val = scanner(target, 5, apikey)
                        print(val)
                        output_save(val, outputf)
            case 'dns':
                val = dns_recon(target, apikey)
                output_save(val, outputf)
            case 'subd':
                val = sub(target)
                output_save(val, outputf)
    except KeyboardInterrupt:
        print('Keyboard Interrupt detected ...')

def application() -> None:
    try:
        apikey = entry1.get()
        openai.api_key = apikey
        target = entry2.get()
        attack = entry5.get()
        outputf = str(entry4.get())
        match attack:
            case 'geo':
                val = geoip(apikey, target)
                print(val)
                output_save(val, outputf)
            case 'nmap':
                p = int(entry3.get())
                match p:
                    case 1:
                        val = scanner(target, 1, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 2:
                        val = scanner(target, 2, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 3:
                        val = scanner(target, 3, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 4:
                        val = scanner(target, 4, apikey)
                        print(val)
                        output_save(val, outputf)
                    case 5:
                        val = scanner(target, 5, apikey)
                        print(val)
                        output_save(val, outputf)
            case 'dns':
                val = dns_recon(target, apikey)
                output_save(val, outputf)
            case 'subd':
                val = sub(target)
                output_save(val, outputf)
    except KeyboardInterrupt:
        print('Keyboard Interrupt detected ...')

