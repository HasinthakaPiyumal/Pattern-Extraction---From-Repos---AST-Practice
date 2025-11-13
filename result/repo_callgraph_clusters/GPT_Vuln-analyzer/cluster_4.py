# Cluster 4

class DNS_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f"""\n        Perform a thorough DNS analysis based on the provided DNS scan information. The resulting output must conform to a JSON format designed for integration into a penetration testing (pentest) report.\n        The objective is to provide accurate and essential information from the perspective of a pentester, ensuring the final output is minimal and concise.\n        DNS Data to be Analyzed\n        Analysis Guidelines:\n        Pentester's Viewpoint: Approach the DNS analysis from a pentester's perspective, focusing on security implications and potential vulnerabilities.\n        Output Format Compliance: Ensure that the final output strictly adheres to the specified JSON format. Each section (DNS Records, Reverse DNS, Zone Transfer Scan) must be appropriately populated.\n        Conciseness: Keep the final output minimal. Include only crucial information relevant to a pentest report.\n        Insights to Include:\n            DNS Records: Provide information on A, AAAA, NS, MX, PTR, SOA, and TXT records.\n            Reverse DNS: Include details about the reverse DNS lookup, showcasing the relationship between IP addresses and corresponding domains.\n            Zone Transfer Scan: Indicate whether zone transfers are allowed and, if so, list the name servers associated.\n\n        The output format:\n        {{\n            "DNS_Records": {{\n                "A": [""],\n                "AAAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }},\n            "Reverse_DNS": {{\n                "IP_Address": "",\n                "Domain": ""\n            }},\n            "Zone_Transfer_Scan": {{\n                "Allowed": false,\n                "Name_Servers": [""]\n            }}\n        }}\n\n        DNS Data to be analyzed: {data}\n        """
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            data = dns_ai_data_regex(str(generated_text))
            print(data)
            return dns_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, data: str, mode: str, lkey, lendpoint):
        user_instruction = '\n            Do a DNS scan analysis on the provided DNS scan information. The DNS output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n            4) So the analysis and provide your view according to the given format\n            5) Remember to provide views as a security engineer or an security analyst.\n            The output format:\n            "A":\n            - List the A records and security views on them\n            "AAA":\n            - List the AAA records and security views on them\n            "NS":\n            - List the NS records and security views on them\n            "MX":\n            - List the MX records and security views on them\n            "PTR":\n            - List the PTR records and security views on them\n            "SOA":\n            - List the SOA records and security views on them\n            "TXT":\n            - List the TXT records and security views on them\n        '
        user_message = f'\n            DNS Data to be analyzed: {data}\n        '
        if mode == 'local':
            loc_prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            returnval = ollama.generate(model='llama2', prompt=loc_prompt)
            bot_response = returnval['response']
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, key: Optional[str]) -> str:
        openai.api_key = key
        prompt = f"""\n        Perform a thorough DNS analysis based on the provided DNS scan information. The resulting output must conform to a JSON format designed for integration into a penetration testing (pentest) report.\n        The objective is to provide accurate and essential information from the perspective of a pentester, ensuring the final output is minimal and concise.\n        DNS Data to be Analyzed:\n        Analysis Guidelines:\n        Pentester's Viewpoint: Approach the DNS analysis from a pentester's perspective, focusing on security implications and potential vulnerabilities.\n        Output Format Compliance: Ensure that the final output strictly adheres to the specified JSON format. Each section (DNS Records, Reverse DNS, Zone Transfer Scan) must be appropriately populated.\n        Conciseness: Keep the final output minimal. Include only crucial information relevant to a pentest report.\n        Insights to Include:\n            DNS Records: Provide information on A, AAAA, NS, MX, PTR, SOA, and TXT records.\n            Reverse DNS: Include details about the reverse DNS lookup, showcasing the relationship between IP addresses and corresponding domains.\n            Zone Transfer Scan: Indicate whether zone transfers are allowed and, if so, list the name servers associated.\n\n        The output format:\n        {{\n            "DNS_Records": {{\n                "A": [""],\n                "AAAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }},\n            "Reverse_DNS": {{\n                "IP_Address": "",\n                "Domain": ""\n            }},\n            "Zone_Transfer_Scan": {{\n                "Allowed": false,\n                "Name_Servers": [""]\n            }}\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        """
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return rsp
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f"""\n        Perform a thorough DNS analysis based on the provided DNS scan information. The resulting output must conform to a JSON format designed for integration into a penetration testing (pentest) report.\n        The objective is to provide accurate and essential information from the perspective of a pentester, ensuring the final output is minimal and concise.\n        DNS Data to be Analyzed\n        Analysis Guidelines:\n        Pentester's Viewpoint: Approach the DNS analysis from a pentester's perspective, focusing on security implications and potential vulnerabilities.\n        Output Format Compliance: Ensure that the final output strictly adheres to the specified JSON format. Each section (DNS Records, Reverse DNS, Zone Transfer Scan) must be appropriately populated.\n        Conciseness: Keep the final output minimal. Include only crucial information relevant to a pentest report.\n        Insights to Include:\n            DNS Records: Provide information on A, AAAA, NS, MX, PTR, SOA, and TXT records.\n            Reverse DNS: Include details about the reverse DNS lookup, showcasing the relationship between IP addresses and corresponding domains.\n            Zone Transfer Scan: Indicate whether zone transfers are allowed and, if so, list the name servers associated.\n\n        The output format:\n        {{\n            "DNS_Records": {{\n                "A": [""],\n                "AAAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }},\n            "Reverse_DNS": {{\n                "IP_Address": "",\n                "Domain": ""\n            }},\n            "Zone_Transfer_Scan": {{\n                "Allowed": false,\n                "Name_Servers": [""]\n            }}\n        }}\n\n        DNS Data to be analyzed: {data}\n        """
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        data = dns_ai_data_regex(str(generated_text))
        print(data)
        return dns_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, key: Optional[str]) -> str:
    openai.api_key = key
    prompt = f"""\n        Perform a thorough DNS analysis based on the provided DNS scan information. The resulting output must conform to a JSON format designed for integration into a penetration testing (pentest) report.\n        The objective is to provide accurate and essential information from the perspective of a pentester, ensuring the final output is minimal and concise.\n        DNS Data to be Analyzed:\n        Analysis Guidelines:\n        Pentester's Viewpoint: Approach the DNS analysis from a pentester's perspective, focusing on security implications and potential vulnerabilities.\n        Output Format Compliance: Ensure that the final output strictly adheres to the specified JSON format. Each section (DNS Records, Reverse DNS, Zone Transfer Scan) must be appropriately populated.\n        Conciseness: Keep the final output minimal. Include only crucial information relevant to a pentest report.\n        Insights to Include:\n            DNS Records: Provide information on A, AAAA, NS, MX, PTR, SOA, and TXT records.\n            Reverse DNS: Include details about the reverse DNS lookup, showcasing the relationship between IP addresses and corresponding domains.\n            Zone Transfer Scan: Indicate whether zone transfers are allowed and, if so, list the name servers associated.\n\n        The output format:\n        {{\n            "DNS_Records": {{\n                "A": [""],\n                "AAAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }},\n            "Reverse_DNS": {{\n                "IP_Address": "",\n                "Domain": ""\n            }},\n            "Zone_Transfer_Scan": {{\n                "Allowed": false,\n                "Name_Servers": [""]\n            }}\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        """
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return rsp
    except KeyboardInterrupt:
        print('Bye')
        quit()

class NMAP_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            return nmap_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def Llama_AI(data: str, mode: str, lkey: str, lendpoint: str) -> Any:
        user_instruction = '\n        Do a NMAP scan analysis on the provided NMAP scan information. The NMAP output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The NMAP scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given.\n        3) The final output must be kept to a minimal.\n        4) If a value not found in the scan just mention an empty string.\n        5) Analyze everything even the smallest of data.\n        6) Completely analyze the data provided and give a confirm answer using the output format.\n        7) mention all the data you found in the output format provided so that regex can be used on it.\n        8) avoid unnecessary explaination.\n        9) the critical score must be calculated based on the CVE if present or by the nature of the services open\n        10) the os information must contain the OS used my the target.\n        11) the open ports must include all the open ports listed in the data[tcp] and varifying if it by checking its states value.  you should not negect even one open port.\n        12) the vulnerable services can be determined via speculation of the service nature or by analyzing the CVE\'s found.\n        The output format:\n            critical score:\n            - Give info on the criticality\n            "os information":\n            - List out the OS information\n            "open ports and services":\n            - List open ports\n            - List open ports services\n            "vulnerable service":\n            - Based on CVEs or nature of the ports opened list the vulnerable services\n            "found cve":\n            - List the CVE\'s found and list the main issues.\n        '
        user_message = f'\n            NMAP Data to be analyzed: {data}\n        '
        if mode == 'local':
            loc_prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            returnval = ollama.generate(model='llama2', prompt=loc_prompt)
            bot_response = returnval['response']
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = llama_runpod_api(prompt, lkey, lendpoint)
        if bot_response:
            return bot_response

    @staticmethod
    def GPT_AI(key: str, data: Any) -> str:
        openai.api_key = key
        try:
            prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
            messages = [{'content': prompt, 'role': 'assistant'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return str(nmap_ai_data_regex(rsp))
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        return nmap_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def GPT_AI(key: str, data: Any) -> str:
    openai.api_key = key
    try:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        messages = [{'content': prompt, 'role': 'assistant'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return str(nmap_ai_data_regex(rsp))
    except KeyboardInterrupt:
        print('Bye')
        quit()

class JWT_AI_MODEL:

    @staticmethod
    def BardAI(key: str, jwt_data: Any) -> str:
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
            print(jwt_analysis_data)
            return jwt_analysis_data
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, jwt_data: str, mode: str, lkey, lendpoint):
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n            Perform a comprehensive analysis on the provided JWT token. The JWT analysis output must be in a asked format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n            Follow these guidelines:\n            1) Analyze the JWT token from a pentester\'s perspective\n            2) Keep the final output minimal while adhering to the given format\n            3) Highlight JWT-specific details and enumerate possible attacks\n\n            The output format:\n            "Header":\n            - List the JWT header details and security views on them\n            "Payload":\n            - List the JWT payload details and security views on them\n            "Signature":\n            - Provide insights on the JWT signature\n            "PossibleAttacks":\n            - List possible JWT exploits and attacks\n        '
        user_message = f'\n            JWT Token Data to be analyzed: {jwt_data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> JWT Token Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        print('test')
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
        openai.api_key = api_key
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return rsp
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, jwt_data: Any) -> str:
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
        print(jwt_analysis_data)
        return jwt_analysis_data
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
    openai.api_key = api_key
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return rsp
    except KeyboardInterrupt:
        print('Bye')
        quit()

def chat_with_api(api_url: str, user_message: str, user_instruction: str, model_name: str, file_name: str=None) -> Any:
    data = {'user_message': user_message, 'model_name': model_name, 'file_name': file_name, 'user_instruction': user_instruction}
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        return response.json()['bot_response']
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return None

class SubEnum:

    @staticmethod
    def display_urls(sd_data: list[str], count: int) -> None:
        console = Console()
        table = Table(title=f'GVA Subdomain report. {count} found', show_header=True, header_style='bold')
        table.add_column('Index', justify='right', style='cyan')
        table.add_column('URL', style='green')
        for index, url in enumerate(sd_data):
            table.add_row(str(index), url)
        console.print(table)

    def sub_enumerator(self, target: str, list_file: str) -> str:
        with open(list_file, 'r') as file:
            s_array = [line.strip() for line in file]
        sd_data = []
        for subd in track(s_array):
            try:
                if dns.resolver.resolve(f'{subd}.{target}', 'A'):
                    sd_data.append(f'{subd}.{target}')
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
            except KeyboardInterrupt:
                print('Ended')
                quit()
        self.display_urls(sd_data, len(sd_data))
        return 'Done'

def sub_enumerator(self, target: str, list_file: str) -> str:
    with open(list_file, 'r') as file:
        s_array = [line.strip() for line in file]
    sd_data = []
    for subd in track(s_array):
        try:
            if dns.resolver.resolve(f'{subd}.{target}', 'A'):
                sd_data.append(f'{subd}.{target}')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except KeyboardInterrupt:
            print('Ended')
            quit()
    self.display_urls(sd_data, len(sd_data))
    return 'Done'

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

def get_column(self, column):
    column_list = []
    for i in self.values:
        column_list.append(i[column])
    return column_list

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

def print_statistics(self):
    print(f'Total Number of Passwords Tried: {self.total_passwords}')
    if self.matched_password:
        print(f'Password Cracked! Password: {self.matched_password}')
    else:
        print('Password Failed.')

def DnsAI(analyze: str, key: Optional[str]) -> str:
    openai.api_key = key
    prompt = f'\n    Do a DNS analysis on the provided DNS scan information\n    The DNS output must return in a JSON format accorging to the provided\n    output format. The data must be accurate in regards towards a pentest report.\n    The data must follow the following rules:\n    1) The DNS scans must be done from a pentester point of view\n    2) The final output must be minimal according to the format given\n    3) The final output must be kept to a minimal\n\n    The output format:\n    {{\n        "A": [""],\n        "AAA": [""],\n        "NS": [""],\n        "MX": [""],\n        "PTR": [""],\n        "SOA": [""],\n        "TXT": [""]\n    }}\n\n    DNS Data to be analyzed: {analyze}\n    '
    try:
        completion = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None)
        response = completion.choices[0].text
        return dns_extract_data(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

def PortAI(key: str, data: Any) -> str:
    openai.api_key = key
    try:
        prompt = f'\n        Do a NMAP scan analysis on the provided NMAP scan information\n        The NMAP output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The NMAP scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given.\n        3) The final output must be kept to a minimal.\n        4) If a value not found in the scan just mention an empty string.\n        5) Analyze everything even the smallest of data.\n\n        The output format:\n        {{\n            "critical score": [""],\n            "os information": [""],\n            "open ports": [""],\n            "open services": [""],\n            "vulnerable service": [""],\n            "found cve": [""]\n        }}\n\n        NMAP Data to be analyzed: {data}\n        '
        completion = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None)
        response = completion.choices[0].text
        return port_extract_data(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

def sub(target: str) -> Any:
    s_array = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'hod', 'butterfly', 'ckp', 'tele2', 'receiver', 'reality', 'panopto', 't7', 'thot', 'wien', 'uat-online', 'Footer']
    ss = []
    out = ''
    for subd in s_array:
        try:
            ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
            if ip_value:
                ss.append(f'{subd}.{target}')
                if f'{subd}.{target}' in ss:
                    print(f'{subd}.{target} | Found')
                    out += f'{subd}.{target}'
                    out += '\n'
                    out += ''
                else:
                    pass
        except dns.resolver.NXDOMAIN:
            pass
        except dns.resolver.NoAnswer:
            pass
        except KeyboardInterrupt:
            print('Ended')
            quit()
    return out

def dns_recon(target: Optional[str], key: str) -> str:
    if key is not None:
        pass
    else:
        raise ValueError('KeyNotFound: Key Not Provided')
    if target is not None:
        pass
    else:
        raise ValueError('InvalidTarget: Target Not Provided')
    analyze = ''
    record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
    for records in track(record_types):
        try:
            answer = dns.resolver.resolve(target, records)
            for server in answer:
                st = server.to_text()
                analyze += '\n'
                analyze += records
                analyze += ' : '
                analyze += st
        except dns.resolver.NoAnswer:
            print('No record Found')
            pass
        except dns.resolver.NXDOMAIN:
            print('NXDOMAIN record NOT Found')
            pass
        except KeyboardInterrupt:
            print('Bye')
            quit()
    try:
        response = DnsAI(key, analyze)
        return str(response)
    except KeyboardInterrupt:
        print('Bye')
        quit()

class sub_enum:

    def display_urls(sd_data: list[str], count: int) -> None:
        console = Console()
        table = Table(title=f'GVA Subdomain report. found out of {count}', show_header=True, header_style='bold')
        table.add_column('Index', justify='right', style='cyan')
        table.add_column('URL', style='green')
        for index, url in enumerate(sd_data):
            table.add_row(str(index), url)
        console.print(table)

    def sub_enumerator(self, target: str, list: str) -> str:
        sd_data = []
        s_array = []
        count: int = 0
        with open(list, 'r') as file:
            for line in file:
                subdomain_key = line.strip()
                s_array.append(subdomain_key)
        for subd in track(s_array):
            try:
                ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
                if ip_value:
                    sd_data.append(f'{subd}.{target}')
                    if f'{subd}.{target}' in sd_data:
                        count = count + 1
                    else:
                        pass
            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except KeyboardInterrupt:
                print('Ended')
                quit()
        self.display_urls(sd_data, count)
        return 'Done'

def sub_enumerator(self, target: str, list: str) -> str:
    sd_data = []
    s_array = []
    count: int = 0
    with open(list, 'r') as file:
        for line in file:
            subdomain_key = line.strip()
            s_array.append(subdomain_key)
    for subd in track(s_array):
        try:
            ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
            if ip_value:
                sd_data.append(f'{subd}.{target}')
                if f'{subd}.{target}' in sd_data:
                    count = count + 1
                else:
                    pass
        except dns.resolver.NXDOMAIN:
            pass
        except dns.resolver.NoAnswer:
            pass
        except KeyboardInterrupt:
            print('Ended')
            quit()
    self.display_urls(sd_data, count)
    return 'Done'

class DNS_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f'\n            Do a DNS analysis on the provided DNS scan information\n            The DNS output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n\n            The output format:\n            {{\n                "A": [""],\n                "AAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }}\n            DNS Data to be analyzed: {data}\n            '
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            data = dns_ai_data_regex(str(generated_text))
            print(data)
            return dns_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, data: str, mode: str, lkey, lendpoint):
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n            Do a DNS scan analysis on the provided DNS scan information. The DNS output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n            4) So the analysis and provide your view according to the given format\n            5) Remember to provide views as a security engineer or an security analyst.\n            The output format:\n            "A":\n            - List the A records and security views on them\n            "AAA":\n            - List the AAA records and security views on them\n            "NS":\n            - List the NS records and security views on them\n            "MX":\n            - List the MX records and security views on them\n            "PTR":\n            - List the PTR records and security views on them\n            "SOA":\n            - List the SOA records and security views on them\n            "TXT":\n            - List the TXT records and security views on them\n        '
        user_message = f'\n            DNS Data to be analyzed: {data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        print('test')
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, key: Optional[str]) -> str:
        openai.api_key = key
        prompt = f'\n        Do a DNS analysis on the provided DNS scan information\n        The DNS output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The DNS scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given\n        3) The final output must be kept to a minimal\n\n        The output format:\n        {{\n            "A": [""],\n            "AAA": [""],\n            "NS": [""],\n            "MX": [""],\n            "PTR": [""],\n            "SOA": [""],\n            "TXT": [""]\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        '
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            return dns_ai_data_regex(str(response))
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f'\n            Do a DNS analysis on the provided DNS scan information\n            The DNS output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n\n            The output format:\n            {{\n                "A": [""],\n                "AAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }}\n            DNS Data to be analyzed: {data}\n            '
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        data = dns_ai_data_regex(str(generated_text))
        print(data)
        return dns_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, key: Optional[str]) -> str:
    openai.api_key = key
    prompt = f'\n        Do a DNS analysis on the provided DNS scan information\n        The DNS output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The DNS scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given\n        3) The final output must be kept to a minimal\n\n        The output format:\n        {{\n            "A": [""],\n            "AAA": [""],\n            "NS": [""],\n            "MX": [""],\n            "PTR": [""],\n            "SOA": [""],\n            "TXT": [""]\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        '
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        return dns_ai_data_regex(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

class NMAP_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            return nmap_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def Llama_AI(data: str, mode: str, lkey: str, lendpoint: str) -> Any:
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n        Do a NMAP scan analysis on the provided NMAP scan information. The NMAP output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The NMAP scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given.\n        3) The final output must be kept to a minimal.\n        4) If a value not found in the scan just mention an empty string.\n        5) Analyze everything even the smallest of data.\n        6) Completely analyze the data provided and give a confirm answer using the output format.\n        7) mention all the data you found in the output format provided so that regex can be used on it.\n        8) avoid unnecessary explaination.\n        9) the critical score must be calculated based on the CVE if present or by the nature of the services open\n        10) the os information must contain the OS used my the target.\n        11) the open ports must include all the open ports listed in the data[tcp] and varifying if it by checking its states value.  you should not negect even one open port.\n        12) the vulnerable services can be determined via speculation of the service nature or by analyzing the CVE\'s found.\n        The output format:\n            critical score:\n            - Give info on the criticality\n            "os information":\n            - List out the OS information\n            "open ports and services":\n            - List open ports\n            - List open ports services\n            "vulnerable service":\n            - Based on CVEs or nature of the ports opened list the vulnerable services\n            "found cve":\n            - List the CVE\'s found and list the main issues.\n        '
        user_message = f'\n            NMAP Data to be analyzed: {data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = llama_runpod_api(prompt, lkey, lendpoint)
        if bot_response:
            return bot_response

    @staticmethod
    def GPT_AI(key: str, data: Any) -> str:
        openai.api_key = key
        try:
            prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
            messages = [{'content': prompt, 'role': 'assistant'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return str(nmap_ai_data_regex(rsp))
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        return nmap_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def GPT_AI(key: str, data: Any) -> str:
    openai.api_key = key
    try:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        messages = [{'content': prompt, 'role': 'assistant'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return str(nmap_ai_data_regex(rsp))
    except KeyboardInterrupt:
        print('Bye')
        quit()

class JWT_AI_MODEL:

    @staticmethod
    def BardAI(key: str, jwt_data: Any) -> str:
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
            print(jwt_analysis_data)
            return jwt_analysis_data
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, jwt_data: str, mode: str, lkey, lendpoint):
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n            Perform a comprehensive analysis on the provided JWT token. The JWT analysis output must be in a asked format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n            Follow these guidelines:\n            1) Analyze the JWT token from a pentester\'s perspective\n            2) Keep the final output minimal while adhering to the given format\n            3) Highlight JWT-specific details and enumerate possible attacks\n\n            The output format:\n            "Header":\n            - List the JWT header details and security views on them\n            "Payload":\n            - List the JWT payload details and security views on them\n            "Signature":\n            - Provide insights on the JWT signature\n            "PossibleAttacks":\n            - List possible JWT exploits and attacks\n        '
        user_message = f'\n            JWT Token Data to be analyzed: {jwt_data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> JWT Token Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        print('test')
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
        openai.api_key = api_key
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return rsp
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, jwt_data: Any) -> str:
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
        print(jwt_analysis_data)
        return jwt_analysis_data
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
    openai.api_key = api_key
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return rsp
    except KeyboardInterrupt:
        print('Bye')
        quit()

def chat_with_api(api_url: str, user_message: str, user_instruction: str, model_name: str, file_name: str=None) -> Any:
    data = {'user_message': user_message, 'model_name': model_name, 'file_name': file_name, 'user_instruction': user_instruction}
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        return response.json()['bot_response']
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return None

def DnsAI(analyze: str, key: Optional[str]) -> str:
    openai.api_key = key
    prompt = f'\n    Do a DNS analysis on the provided DNS scan information\n    The DNS output must return in a JSON format accorging to the provided\n    output format. The data must be accurate in regards towards a pentest report.\n    The data must follow the following rules:\n    1) The DNS scans must be done from a pentester point of view\n    2) The final output must be minimal according to the format given\n    3) The final output must be kept to a minimal\n\n    The output format:\n    {{\n        "A": [""],\n        "AAA": [""],\n        "NS": [""],\n        "MX": [""],\n        "PTR": [""],\n        "SOA": [""],\n        "TXT": [""]\n    }}\n\n    DNS Data to be analyzed: {analyze}\n    '
    try:
        completion = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None)
        response = completion.choices[0].text
        return dns_extract_data(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

def PortAI(key: str, data: Any) -> str:
    openai.api_key = key
    try:
        prompt = f'\n        Do a NMAP scan analysis on the provided NMAP scan information\n        The NMAP output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The NMAP scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given.\n        3) The final output must be kept to a minimal.\n        4) If a value not found in the scan just mention an empty string.\n        5) Analyze everything even the smallest of data.\n\n        The output format:\n        {{\n            "critical score": [""],\n            "os information": [""],\n            "open ports": [""],\n            "open services": [""],\n            "vulnerable service": [""],\n            "found cve": [""]\n        }}\n\n        NMAP Data to be analyzed: {data}\n        '
        completion = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None)
        response = completion.choices[0].text
        return port_extract_data(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

def sub(target: str) -> Any:
    s_array = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'hod', 'butterfly', 'ckp', 'tele2', 'receiver', 'reality', 'panopto', 't7', 'thot', 'wien', 'uat-online', 'Footer']
    ss = []
    out = ''
    for subd in s_array:
        try:
            ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
            if ip_value:
                ss.append(f'{subd}.{target}')
                if f'{subd}.{target}' in ss:
                    print(f'{subd}.{target} | Found')
                    out += f'{subd}.{target}'
                    out += '\n'
                    out += ''
                else:
                    pass
        except dns.resolver.NXDOMAIN:
            pass
        except dns.resolver.NoAnswer:
            pass
        except KeyboardInterrupt:
            print('Ended')
            quit()
    return out

def dns_recon(target: Optional[str], key: str) -> str:
    if key is not None:
        pass
    else:
        raise ValueError('KeyNotFound: Key Not Provided')
    if target is not None:
        pass
    else:
        raise ValueError('InvalidTarget: Target Not Provided')
    analyze = ''
    record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
    for records in track(record_types):
        try:
            answer = dns.resolver.resolve(target, records)
            for server in answer:
                st = server.to_text()
                analyze += '\n'
                analyze += records
                analyze += ' : '
                analyze += st
        except dns.resolver.NoAnswer:
            print('No record Found')
            pass
        except dns.resolver.NXDOMAIN:
            print('NXDOMAIN record NOT Found')
            pass
        except KeyboardInterrupt:
            print('Bye')
            quit()
    try:
        response = DnsAI(key, analyze)
        return str(response)
    except KeyboardInterrupt:
        print('Bye')
        quit()

class sub_enum:

    def display_urls(sd_data: list[str], count: int) -> None:
        console = Console()
        table = Table(title=f'GVA Subdomain report. found out of {count}', show_header=True, header_style='bold')
        table.add_column('Index', justify='right', style='cyan')
        table.add_column('URL', style='green')
        for index, url in enumerate(sd_data):
            table.add_row(str(index), url)
        console.print(table)

    def sub_enumerator(self, target: str, list: str) -> str:
        sd_data = []
        s_array = []
        count: int = 0
        with open(list, 'r') as file:
            for line in file:
                subdomain_key = line.strip()
                s_array.append(subdomain_key)
        for subd in track(s_array):
            try:
                ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
                if ip_value:
                    sd_data.append(f'{subd}.{target}')
                    if f'{subd}.{target}' in sd_data:
                        count = count + 1
                    else:
                        pass
            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except KeyboardInterrupt:
                print('Ended')
                quit()
        self.display_urls(sd_data, count)
        return 'Done'

def sub_enumerator(self, target: str, list: str) -> str:
    sd_data = []
    s_array = []
    count: int = 0
    with open(list, 'r') as file:
        for line in file:
            subdomain_key = line.strip()
            s_array.append(subdomain_key)
    for subd in track(s_array):
        try:
            ip_value = dns.resolver.resolve(f'{subd}.{target}', 'A')
            if ip_value:
                sd_data.append(f'{subd}.{target}')
                if f'{subd}.{target}' in sd_data:
                    count = count + 1
                else:
                    pass
        except dns.resolver.NXDOMAIN:
            pass
        except dns.resolver.NoAnswer:
            pass
        except KeyboardInterrupt:
            print('Ended')
            quit()
    self.display_urls(sd_data, count)
    return 'Done'

class DNS_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f'\n            Do a DNS analysis on the provided DNS scan information\n            The DNS output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n\n            The output format:\n            {{\n                "A": [""],\n                "AAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }}\n            DNS Data to be analyzed: {data}\n            '
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            data = dns_ai_data_regex(str(generated_text))
            print(data)
            return dns_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, data: str, mode: str, lkey, lendpoint):
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n            Do a DNS scan analysis on the provided DNS scan information. The DNS output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n            4) So the analysis and provide your view according to the given format\n            5) Remember to provide views as a security engineer or an security analyst.\n            The output format:\n            "A":\n            - List the A records and security views on them\n            "AAA":\n            - List the AAA records and security views on them\n            "NS":\n            - List the NS records and security views on them\n            "MX":\n            - List the MX records and security views on them\n            "PTR":\n            - List the PTR records and security views on them\n            "SOA":\n            - List the SOA records and security views on them\n            "TXT":\n            - List the TXT records and security views on them\n        '
        user_message = f'\n            DNS Data to be analyzed: {data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        print('test')
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, key: Optional[str]) -> str:
        openai.api_key = key
        prompt = f'\n        Do a DNS analysis on the provided DNS scan information\n        The DNS output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The DNS scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given\n        3) The final output must be kept to a minimal\n\n        The output format:\n        {{\n            "A": [""],\n            "AAA": [""],\n            "NS": [""],\n            "MX": [""],\n            "PTR": [""],\n            "SOA": [""],\n            "TXT": [""]\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        '
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            return dns_ai_data_regex(str(response))
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f'\n            Do a DNS analysis on the provided DNS scan information\n            The DNS output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The DNS scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given\n            3) The final output must be kept to a minimal\n\n            The output format:\n            {{\n                "A": [""],\n                "AAA": [""],\n                "NS": [""],\n                "MX": [""],\n                "PTR": [""],\n                "SOA": [""],\n                "TXT": [""]\n            }}\n            DNS Data to be analyzed: {data}\n            '
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        data = dns_ai_data_regex(str(generated_text))
        print(data)
        return dns_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, key: Optional[str]) -> str:
    openai.api_key = key
    prompt = f'\n        Do a DNS analysis on the provided DNS scan information\n        The DNS output must return in a JSON format accorging to the provided\n        output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The DNS scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given\n        3) The final output must be kept to a minimal\n\n        The output format:\n        {{\n            "A": [""],\n            "AAA": [""],\n            "NS": [""],\n            "MX": [""],\n            "PTR": [""],\n            "SOA": [""],\n            "TXT": [""]\n        }}\n\n        DNS Data to be analyzed: {analyze}\n        '
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        return dns_ai_data_regex(str(response))
    except KeyboardInterrupt:
        print('Bye')
        quit()

class NMAP_AI_MODEL:

    @staticmethod
    def BardAI(key: str, data: Any) -> str:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            return nmap_ai_data_regex(str(generated_text))
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def Llama_AI(data: str, mode: str, lkey: str, lendpoint: str) -> Any:
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n        Do a NMAP scan analysis on the provided NMAP scan information. The NMAP output must return in a asked format accorging to the provided output format. The data must be accurate in regards towards a pentest report.\n        The data must follow the following rules:\n        1) The NMAP scans must be done from a pentester point of view\n        2) The final output must be minimal according to the format given.\n        3) The final output must be kept to a minimal.\n        4) If a value not found in the scan just mention an empty string.\n        5) Analyze everything even the smallest of data.\n        6) Completely analyze the data provided and give a confirm answer using the output format.\n        7) mention all the data you found in the output format provided so that regex can be used on it.\n        8) avoid unnecessary explaination.\n        9) the critical score must be calculated based on the CVE if present or by the nature of the services open\n        10) the os information must contain the OS used my the target.\n        11) the open ports must include all the open ports listed in the data[tcp] and varifying if it by checking its states value.  you should not negect even one open port.\n        12) the vulnerable services can be determined via speculation of the service nature or by analyzing the CVE\'s found.\n        The output format:\n            critical score:\n            - Give info on the criticality\n            "os information":\n            - List out the OS information\n            "open ports and services":\n            - List open ports\n            - List open ports services\n            "vulnerable service":\n            - Based on CVEs or nature of the ports opened list the vulnerable services\n            "found cve":\n            - List the CVE\'s found and list the main issues.\n        '
        user_message = f'\n            NMAP Data to be analyzed: {data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> NMAP Data to be analyzed: {user_message} [/INST]'
            bot_response = llama_runpod_api(prompt, lkey, lendpoint)
        if bot_response:
            return bot_response

    @staticmethod
    def GPT_AI(key: str, data: Any) -> str:
        openai.api_key = key
        try:
            prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
            messages = [{'content': prompt, 'role': 'assistant'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return str(nmap_ai_data_regex(rsp))
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, data: Any) -> str:
    prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        return nmap_ai_data_regex(str(generated_text))
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def GPT_AI(key: str, data: Any) -> str:
    openai.api_key = key
    try:
        prompt = f'\n            Do a NMAP scan analysis on the provided NMAP scan information\n            The NMAP output must return in a JSON format accorging to the provided\n            output format. The data must be accurate in regards towards a pentest report.\n            The data must follow the following rules:\n            1) The NMAP scans must be done from a pentester point of view\n            2) The final output must be minimal according to the format given.\n            3) The final output must be kept to a minimal.\n            4) If a value not found in the scan just mention an empty string.\n            5) Analyze everything even the smallest of data.\n            6) Completely analyze the data provided and give a confirm answer using the output format.\n\n            The output format:\n            {{\n                "critical score": [""],\n                "os information": [""],\n                "open ports": [""],\n                "open services": [""],\n                "vulnerable service": [""],\n                "found cve": [""]\n            }}\n\n            NMAP Data to be analyzed: {data}\n            '
        messages = [{'content': prompt, 'role': 'assistant'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=2500, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return str(nmap_ai_data_regex(rsp))
    except KeyboardInterrupt:
        print('Bye')
        quit()

class JWT_AI_MODEL:

    @staticmethod
    def BardAI(key: str, jwt_data: Any) -> str:
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
        url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
        headers = {'Content-Type': 'application/json'}
        data = {'prompt': {'text': prompt}}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            generated_text = response.json()
            jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
            print(jwt_analysis_data)
            return jwt_analysis_data
        else:
            print('Error: Unable to generate text. Status Code:', response.status_code)
            return 'None'

    @staticmethod
    def llama_AI(self, jwt_data: str, mode: str, lkey, lendpoint):
        api_url = 'http://localhost:5000/api/chatbot'
        user_instruction = '\n            Perform a comprehensive analysis on the provided JWT token. The JWT analysis output must be in a asked format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n            Follow these guidelines:\n            1) Analyze the JWT token from a pentester\'s perspective\n            2) Keep the final output minimal while adhering to the given format\n            3) Highlight JWT-specific details and enumerate possible attacks\n\n            The output format:\n            "Header":\n            - List the JWT header details and security views on them\n            "Payload":\n            - List the JWT payload details and security views on them\n            "Signature":\n            - Provide insights on the JWT signature\n            "PossibleAttacks":\n            - List possible JWT exploits and attacks\n        '
        user_message = f'\n            JWT Token Data to be analyzed: {jwt_data}\n        '
        model_name = 'TheBloke/Llama-2-7B-Chat-GGML'
        file_name = 'llama-2-7b-chat.ggmlv3.q4_K_M.bin'
        if mode == 'local':
            bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        elif mode == 'runpod':
            prompt = f'[INST] <<SYS>> {user_instruction}<</SYS>> JWT Token Data to be analyzed: {user_message} [/INST]'
            bot_response = self.llama_runpod_api(prompt, lkey, lendpoint)
        bot_response = self.chat_with_api(api_url, user_message, user_instruction, model_name, file_name)
        print('test')
        if bot_response:
            return bot_response

    @staticmethod
    def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
        openai.api_key = api_key
        prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
        try:
            messages = [{'content': prompt, 'role': 'user'}]
            response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
            response = response['choices'][0]['message']['content']
            rsp = str(response)
            return rsp
        except KeyboardInterrupt:
            print('Bye')
            quit()

@staticmethod
def BardAI(key: str, jwt_data: Any) -> str:
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {jwt_data}\n        """
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=' + key
    headers = {'Content-Type': 'application/json'}
    data = {'prompt': {'text': prompt}}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        generated_text = response.json()
        jwt_analysis_data = jwt_ai_data_regex(str(generated_text))
        print(jwt_analysis_data)
        return jwt_analysis_data
    else:
        print('Error: Unable to generate text. Status Code:', response.status_code)
        return 'None'

@staticmethod
def gpt_ai(analyze: str, api_key: Optional[str]) -> str:
    openai.api_key = api_key
    prompt = f"""\n        Perform a comprehensive analysis on the provided JWT token. The analysis output must be in a JSON format according to the provided output structure. Ensure accuracy for inclusion in a penetration testing report.\n        Follow these guidelines:\n        1) Analyze the JWT token from a pentester's perspective\n        2) Keep the final output minimal while adhering to the given format\n        3) Highlight JWT-specific details and enumerate possible attacks and vulnerabilities\n        5) For the output "Algorithm Used" value use the Algorithm value from the JWT data.\n        6) For the output "Header" value use the Header value from the JWT data.\n        7) For the "Payload" Use the decoded payloads as a reference and then analyze any attack endpoints.\n        8) For "Signature" mention the signatures discovered.\n        9) List a few endpoints you feel are vulnerable for "VulnerableEndpoints"\n\n        The output format:\n        {{\n            "Algorithm Used": "",\n            "Header": "",\n            "Payload": "",\n            "Signature": "",\n            "PossibleAttacks": "",\n            "VulnerableEndpoints": ""\n        }}\n\n        JWT Token Data to be analyzed: {analyze}\n        """
    try:
        messages = [{'content': prompt, 'role': 'user'}]
        response = openai.ChatCompletion.create(model=model_engine, messages=messages, max_tokens=1024, n=1, stop=None)
        response = response['choices'][0]['message']['content']
        rsp = str(response)
        return rsp
    except KeyboardInterrupt:
        print('Bye')
        quit()

def chat_with_api(api_url: str, user_message: str, user_instruction: str, model_name: str, file_name: str=None) -> Any:
    data = {'user_message': user_message, 'model_name': model_name, 'file_name': file_name, 'user_instruction': user_instruction}
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        return response.json()['bot_response']
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return None

