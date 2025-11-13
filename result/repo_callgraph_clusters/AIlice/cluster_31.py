# Cluster 31

class AStorageWeaviate:

    def __init__(self, clusterURL, apiKey, oaiKey):
        self.clusterURL = clusterURL
        self.apiKey = apiKey
        self.oaiKey = oaiKey
        self.client = None
        return

    def __del__(self):
        self.client.close()
        return

    def ModuleInfo(self):
        return {'NAME': 'storage', 'ACTIONS': {}}

    def Open(self, directory: str) -> str:
        try:
            self.client = weaviate.connect_to_wcs(cluster_url=self.clusterURL, auth_credentials=weaviate.auth.AuthApiKey(self.apiKey), headers={'X-OpenAI-Api-Key': self.oaiKey})
        except Exception as e:
            print(f'Open() EXCEPTION. e: {str(e)}')
            return f'Open() EXCEPTION. e: {str(e)}'

    def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
        try:
            print('collection: ', collection, '. store: ', content)
            if not self.client.collections.exists(collection):
                print(f'create a new collection: {collection}')
                self.client.collections.create(name=collection, vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(), generative_config=wvc.config.Configure.Generative.openai())
            self.client.collections.get(collection).data.insert_many([{'text': content}] if type(content) != list else [{'text': t} for t in content])
        except Exception as e:
            print('store() EXCEPTION: ', e)
            return False
        return True

    def Query(self, collection: str, clue: str, num_results: int=1) -> list[tuple[str, float]]:
        try:
            response = self.client.collections.get(collection).query.near_text(query=clue, limit=num_results)
            ret = None
            if 0 < len(response.objects):
                ret = [(r.properties['text'], r.metadata.distance) for r in response.objects]
            print('query: ', collection, '.', clue, ' -> ', ret)
            return ret
        except Exception as e:
            print('query() EXCEPTION: ', e)
            return []

    def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
        return self.Query(collection=collection, clue=query, num_results=num_results)

def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
    try:
        print('collection: ', collection, '. store: ', content)
        if not self.client.collections.exists(collection):
            print(f'create a new collection: {collection}')
            self.client.collections.create(name=collection, vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(), generative_config=wvc.config.Configure.Generative.openai())
        self.client.collections.get(collection).data.insert_many([{'text': content}] if type(content) != list else [{'text': t} for t in content])
    except Exception as e:
        print('store() EXCEPTION: ', e)
        return False
    return True

class AStorageVecDB:

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.data = {'tokenizer': TOKENIZER, 'model': MODEL, 'collections': {}}
        self.dir = None
        return

    def ModuleInfo(self):
        return {'NAME': 'storage', 'ACTIONS': {}}

    def CalcEmbeddings(self, txts: list[str]):
        encodedInput = self.tokenizer(txts, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            modelOutput = self.model(**encodedInput)
        tokenEmbeddings = modelOutput[0]
        inputMaskExpanded = encodedInput['attention_mask'].unsqueeze(-1).expand(tokenEmbeddings.size()).float()
        embeddings = torch.sum(tokenEmbeddings * inputMaskExpanded, 1) / torch.clamp(inputMaskExpanded.sum(1), min=1e-09)
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings

    def Dump(self, dir):
        if None != dir:
            with open(dir + '/vecdb', 'wb') as f:
                pickle.dump(self.data, f)
        return

    def Load(self, dir):
        if os.path.exists(dir + '/vecdb'):
            with open(dir + '/vecdb', 'rb') as f:
                self.data = pickle.load(f)
        return

    def PrepareModel(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.data['tokenizer'])
        self.model = AutoModel.from_pretrained(self.data['model'], trust_remote_code=True)
        self.model.eval()
        return

    def Open(self, directory: str) -> str:
        try:
            if '' == directory.strip():
                self.dir = None
                self.PrepareModel()
                return f'vector database has been switched to a non-persistent version. tokenizer: {self.data['tokenizer']}, model: {self.data['model']}'
            else:
                self.dir = directory
                self.Load(directory)
                self.PrepareModel()
                return f'vector database under {directory} is opened. tokenizer: {self.data['tokenizer']}, model: {self.data['model']}'
        except Exception as e:
            print(f'Open() EXCEPTION. e: {str(e)}')
            raise e

    def Reset(self) -> str:
        self.data['collections'].clear()
        return 'vector database reseted.'

    def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
        try:
            print('collection: ', collection, '. store: ', content)
            if collection not in self.data['collections']:
                self.data['collections'][collection] = dict()
            texts = [content] if type(content) != list else content
            embeddings = self.CalcEmbeddings(texts)
            for txt, emb in zip(texts, embeddings):
                if txt not in self.data['collections'][collection]:
                    self.data['collections'][collection][txt] = emb
            self.Dump(self.dir)
        except Exception as e:
            print('store() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return False
        return True

    def Query(self, collection: str, clue: str='', keywords: list[str]=[], num_results: int=1) -> list[tuple[str, float]]:
        try:
            if collection not in self.data['collections']:
                return []
            results = [txt for txt, _ in self.data['collections'][collection].items()]
            for keyword in keywords:
                results = [txt for txt in results if keyword in txt]
            if clue in ['', None]:
                results = [(r, -1.0) for r in results]
                return results[:num_results] if num_results > 0 else results
            query = self.CalcEmbeddings([clue])[0]
            temp = [(txt, torch.sum((self.data['collections'][collection][txt] - query) ** 2, dim=0).item()) for txt in results]
            ret = sorted(temp, key=lambda x: x[1])[:num_results] if num_results > 0 else temp
            print('query: ', collection, '.', clue, ' -> ', ret)
            return ret
        except Exception as e:
            print('query() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return []

    def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
        return self.Query(collection=collection, clue=query, num_results=num_results)

def CalcEmbeddings(self, txts: list[str]):
    encodedInput = self.tokenizer(txts, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        modelOutput = self.model(**encodedInput)
    tokenEmbeddings = modelOutput[0]
    inputMaskExpanded = encodedInput['attention_mask'].unsqueeze(-1).expand(tokenEmbeddings.size()).float()
    embeddings = torch.sum(tokenEmbeddings * inputMaskExpanded, 1) / torch.clamp(inputMaskExpanded.sum(1), min=1e-09)
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings

class AModelChatGPT:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = self.config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update({'max_tokens': 4096} if 'vision' in self.modelName else {})
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='ChatGPT/InputTokens', amount=prompt[1])
            with openai.OpenAI(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
                for chunk in client.chat.completions.create(model=self.modelName, messages=prompt[0], stream=True, timeout=60, **extras):
                    text += chunk.choices[0].delta.content or ''
                    if endchecker(text):
                        break
                    sentences = [x for x in sentences_split(text[currentPosition:])]
                    if 2 <= len(sentences) and '' != sentences[0].strip():
                        gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(sentences[0]) // 4)
                        proc(txt=sentences[0])
                        currentPosition += len(sentences[0])
        except openai.AuthenticationError as e:
            msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
            print('\n\n', msg)
            print('\n\nException:\n', str(e))
            os._exit(1)
        gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
    currentPosition = 0
    text = ''
    extras = {}
    extras.update({'max_tokens': 4096} if 'vision' in self.modelName else {})
    extras.update(self.modelCfg.get('args', {}))
    extras.update({'temperature': temperature} if None != temperature else {})
    try:
        gasTank.Consume(resourceType='ChatGPT/InputTokens', amount=prompt[1])
        with openai.OpenAI(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
            for chunk in client.chat.completions.create(model=self.modelName, messages=prompt[0], stream=True, timeout=60, **extras):
                text += chunk.choices[0].delta.content or ''
                if endchecker(text):
                    break
                sentences = [x for x in sentences_split(text[currentPosition:])]
                if 2 <= len(sentences) and '' != sentences[0].strip():
                    gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(sentences[0]) // 4)
                    proc(txt=sentences[0])
                    currentPosition += len(sentences[0])
    except openai.AuthenticationError as e:
        msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
        print('\n\n', msg)
        print('\n\nException:\n', str(e))
        os._exit(1)
    gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(text[currentPosition:]) // 4)
    proc(txt=text[currentPosition:])
    return text

class AModelCausalLM:

    def __init__(self, modelType: str, modelName: str, config):
        self.modelType = modelType
        self.config = config
        self.tokenizer = None
        self.model = None
        self.configMap = {'': None, None: None, '4bit': transformers.BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16), '8bit': transformers.BitsAndBytesConfig(load_in_8bit=True)}
        self.LoadModel(modelName)
        if modelType not in config.models or modelName not in config.models[modelType]['modelList']:
            print(f'LLM {modelType}:{modelName} not supported yet.')
            exit(-1)
        modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=modelCfg['systemAsUser'])
        self.contextWindow = modelCfg['contextWindow']
        return

    def LoadModel(self, modelName: str):
        if 'peft' == self.modelType:
            self.LoadModel_PEFT(modelName=modelName)
        else:
            self.LoadModel_Default(modelName=modelName)
        return

    def LoadModel_Default(self, modelName: str):
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(modelName, use_fast=False, legacy=False, force_download=False, resume_download=True)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(modelName, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory, force_download=False, resume_download=True)
        return

    def LoadModel_PEFT(self, modelName: str):
        if not PEFT_INSTALLED:
            print('peft not installed. Please install it with the following command: pip install -e .[finetuning]')
            sys.exit()
        peftConfig = PeftConfig.from_pretrained(modelName)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(peftConfig.base_model_name_or_path, use_fast=False)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(peftConfig.base_model_name_or_path, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory)
        self.model = PeftModel.from_pretrained(self.model, modelName)
        return

    def Generate(self, prompt: str, proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        predictedIDs = torch.tensor([prompt[0]]).cuda()
        generatedIDs = None
        pastKeyValues = None
        currentPosition = 0
        text = ''
        gasTank.Consume(resourceType='HFCausalLM/InputTokens', amount=predictedIDs.shape[1])
        for _ in range(4096):
            with torch.no_grad():
                outputs = self.model(input_ids=predictedIDs, past_key_values=pastKeyValues, use_cache=True)
            logits = outputs.logits
            pastKeyValues = outputs.past_key_values
            if temperature > 1e-09:
                scaledLogits = logits / temperature
                probs = torch.nn.functional.softmax(scaledLogits, dim=-1)
                predictedIDs = torch.multinomial(probs[:, -1, :], 1)
            else:
                predictedIDs = torch.argmax(logits[..., -1, :], dim=-1, keepdim=True)
            gasTank.Consume(resourceType='HFCausalLM/OutputTokens', amount=predictedIDs.shape[1])
            generatedIDs = predictedIDs if None == generatedIDs else torch.cat((generatedIDs, predictedIDs), dim=-1)
            text = self.tokenizer.decode(generatedIDs[0].cpu().numpy(), skip_special_tokens=True)
            if predictedIDs.item() == self.tokenizer.eos_token_id or endchecker(text):
                break
            sentences = [x for x in sentences_split(text[currentPosition:])]
            if 2 <= len(sentences) and '' != sentences[0].strip():
                proc(txt=sentences[0])
                currentPosition += len(sentences[0])
        proc(txt=text[currentPosition:])
        return text

def Generate(self, prompt: str, proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
    predictedIDs = torch.tensor([prompt[0]]).cuda()
    generatedIDs = None
    pastKeyValues = None
    currentPosition = 0
    text = ''
    gasTank.Consume(resourceType='HFCausalLM/InputTokens', amount=predictedIDs.shape[1])
    for _ in range(4096):
        with torch.no_grad():
            outputs = self.model(input_ids=predictedIDs, past_key_values=pastKeyValues, use_cache=True)
        logits = outputs.logits
        pastKeyValues = outputs.past_key_values
        if temperature > 1e-09:
            scaledLogits = logits / temperature
            probs = torch.nn.functional.softmax(scaledLogits, dim=-1)
            predictedIDs = torch.multinomial(probs[:, -1, :], 1)
        else:
            predictedIDs = torch.argmax(logits[..., -1, :], dim=-1, keepdim=True)
        gasTank.Consume(resourceType='HFCausalLM/OutputTokens', amount=predictedIDs.shape[1])
        generatedIDs = predictedIDs if None == generatedIDs else torch.cat((generatedIDs, predictedIDs), dim=-1)
        text = self.tokenizer.decode(generatedIDs[0].cpu().numpy(), skip_special_tokens=True)
        if predictedIDs.item() == self.tokenizer.eos_token_id or endchecker(text):
            break
        sentences = [x for x in sentences_split(text[currentPosition:])]
        if 2 <= len(sentences) and '' != sentences[0].strip():
            proc(txt=sentences[0])
            currentPosition += len(sentences[0])
    proc(txt=text[currentPosition:])
    return text

class AModelAnthropic:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='Anthropic/InputTokens', amount=prompt[1])
            with anthropic.Anthropic(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
                with client.messages.stream(model=self.modelName, max_tokens=4096, system=prompt[0][0]['content'], messages=prompt[0][1:], timeout=60, **extras) as stream:
                    for delta in stream.text_stream:
                        text += delta
                        if endchecker(text):
                            break
                        sentences = [x for x in sentences_split(text[currentPosition:])]
                        if 2 <= len(sentences) and '' != sentences[0].strip():
                            gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(sentences[0]) // 4)
                            proc(txt=sentences[0])
                            currentPosition += len(sentences[0])
        except anthropic.AuthenticationError as e:
            msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
            print('\n\n', msg)
            print('\n\nException:\n', str(e))
            os._exit(1)
        gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
    currentPosition = 0
    text = ''
    extras = {}
    extras.update(self.modelCfg.get('args', {}))
    extras.update({'temperature': temperature} if None != temperature else {})
    try:
        gasTank.Consume(resourceType='Anthropic/InputTokens', amount=prompt[1])
        with anthropic.Anthropic(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
            with client.messages.stream(model=self.modelName, max_tokens=4096, system=prompt[0][0]['content'], messages=prompt[0][1:], timeout=60, **extras) as stream:
                for delta in stream.text_stream:
                    text += delta
                    if endchecker(text):
                        break
                    sentences = [x for x in sentences_split(text[currentPosition:])]
                    if 2 <= len(sentences) and '' != sentences[0].strip():
                        gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(sentences[0]) // 4)
                        proc(txt=sentences[0])
                        currentPosition += len(sentences[0])
    except anthropic.AuthenticationError as e:
        msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
        print('\n\n', msg)
        print('\n\nException:\n', str(e))
        os._exit(1)
    gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(text[currentPosition:]) // 4)
    proc(txt=text[currentPosition:])
    return text

class AModelMistral:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='Mistral/InputTokens', amount=prompt[1])
            with Mistral(api_key=self.config.models[self.modelType]['apikey']) as client:
                for chunk in client.chat.stream(model=self.modelName, messages=prompt[0], timeout_ms=60000, **extras):
                    text += chunk.data.choices[0].delta.content or ''
                    if endchecker(text):
                        break
                    sentences = [x for x in sentences_split(text[currentPosition:])]
                    if 2 <= len(sentences) and '' != sentences[0].strip():
                        gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(sentences[0]) // 4)
                        proc(txt=sentences[0])
                        currentPosition += len(sentences[0])
        except models.sdkerror.SDKError as e:
            if 'Unauthorized' in e.body:
                msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
                print('\n\n', msg)
                print('\n\nException:\n', str(e))
                os._exit(1)
            else:
                raise
        gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
    currentPosition = 0
    text = ''
    extras = {}
    extras.update(self.modelCfg.get('args', {}))
    extras.update({'temperature': temperature} if None != temperature else {})
    try:
        gasTank.Consume(resourceType='Mistral/InputTokens', amount=prompt[1])
        with Mistral(api_key=self.config.models[self.modelType]['apikey']) as client:
            for chunk in client.chat.stream(model=self.modelName, messages=prompt[0], timeout_ms=60000, **extras):
                text += chunk.data.choices[0].delta.content or ''
                if endchecker(text):
                    break
                sentences = [x for x in sentences_split(text[currentPosition:])]
                if 2 <= len(sentences) and '' != sentences[0].strip():
                    gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(sentences[0]) // 4)
                    proc(txt=sentences[0])
                    currentPosition += len(sentences[0])
    except models.sdkerror.SDKError as e:
        if 'Unauthorized' in e.body:
            msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
            print('\n\n', msg)
            print('\n\nException:\n', str(e))
            os._exit(1)
        else:
            raise
    gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(text[currentPosition:]) // 4)
    proc(txt=text[currentPosition:])
    return text

