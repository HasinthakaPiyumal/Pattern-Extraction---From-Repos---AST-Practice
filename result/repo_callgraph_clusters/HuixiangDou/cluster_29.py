# Cluster 29

class SentenceEmbeddingPipeline(Pipeline):

    def _sanitize_parameters(self, **kwargs):
        preprocess_kwargs = {}
        return (preprocess_kwargs, {}, {})

    def preprocess(self, inputs):
        encoded_inputs = self.tokenizer(inputs, padding=True, truncation=True, return_tensors='pt')
        return encoded_inputs

    def _forward(self, model_inputs):
        outputs = self.model(**model_inputs)
        return {'outputs': outputs, 'attention_mask': model_inputs['attention_mask']}

    def postprocess(self, model_outputs):
        sentence_embeddings = mean_pooling(model_outputs['outputs'], model_outputs['attention_mask'])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings

def postprocess(self, model_outputs):
    sentence_embeddings = mean_pooling(model_outputs['outputs'], model_outputs['attention_mask'])
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    return sentence_embeddings

