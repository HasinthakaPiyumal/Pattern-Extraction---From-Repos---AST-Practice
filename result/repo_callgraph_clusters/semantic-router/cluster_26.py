# Cluster 26

class AutoEncoder:
    type: EncoderType
    name: Optional[str]
    model: DenseEncoder | SparseEncoder

    def __init__(self, type: str, name: Optional[str]):
        self.type = EncoderType(type)
        self.name = name
        if self.type == EncoderType.AZURE:
            self.model = AzureOpenAIEncoder(name=name)
        elif self.type == EncoderType.COHERE:
            self.model = CohereEncoder(name=name)
        elif self.type == EncoderType.OPENAI:
            self.model = OpenAIEncoder(name=name)
        elif self.type == EncoderType.AURELIO:
            self.model = AurelioSparseEncoder(name=name)
        elif self.type == EncoderType.BM25:
            if name is None:
                name = 'bm25'
            self.model = BM25Encoder(name=name)
        elif self.type == EncoderType.TFIDF:
            if name is None:
                name = 'tfidf'
            self.model = TfidfEncoder(name=name)
        elif self.type == EncoderType.FASTEMBED:
            self.model = FastEmbedEncoder(name=name)
        elif self.type == EncoderType.HUGGINGFACE:
            self.model = HuggingFaceEncoder(name=name)
        elif self.type == EncoderType.MISTRAL:
            self.model = MistralEncoder(name=name)
        elif self.type == EncoderType.VOYAGE:
            self.model = VoyageEncoder(name=name)
        elif self.type == EncoderType.JINA:
            self.model = JinaEncoder(name=name)
        elif self.type == EncoderType.NIM:
            self.model = NimEncoder(name=name)
        elif self.type == EncoderType.VIT:
            self.model = VitEncoder(name=name)
        elif self.type == EncoderType.CLIP:
            self.model = CLIPEncoder(name=name)
        elif self.type == EncoderType.GOOGLE:
            self.model = GoogleEncoder(name=name)
        elif self.type == EncoderType.BEDROCK:
            self.model = BedrockEncoder(name=name)
        elif self.type == EncoderType.LITELLM:
            self.model = LiteLLMEncoder(name=name)
        elif self.type == EncoderType.OLLAMA:
            self.model = OllamaEncoder(name=name)
        elif self.type == EncoderType.LOCAL:
            self.model = LocalEncoder(name=name)
        else:
            raise ValueError(f"Encoder type '{type}' not supported")

    def __call__(self, texts: List[str]) -> List[List[float]] | List[SparseEmbedding]:
        return self.model(texts)

def __call__(self, texts: List[str]) -> List[List[float]] | List[SparseEmbedding]:
    return self.model(texts)

