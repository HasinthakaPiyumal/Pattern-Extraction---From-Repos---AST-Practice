# Cluster 17

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

def LoadModel(self, modelName: str):
    if 'peft' == self.modelType:
        self.LoadModel_PEFT(modelName=modelName)
    else:
        self.LoadModel_Default(modelName=modelName)
    return

