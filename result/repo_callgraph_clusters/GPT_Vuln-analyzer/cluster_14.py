# Cluster 14

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

