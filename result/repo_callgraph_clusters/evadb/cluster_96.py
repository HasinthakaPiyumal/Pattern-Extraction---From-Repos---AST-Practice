# Cluster 96

class AbstractHFFunction(AbstractFunction, GPUCompatible):
    """
    An abstract class for all HuggingFace models.

    This is implemented using the pipeline API from HuggingFace. pipeline is an
    easy way to use a huggingface model for inference. In EvaDB, we require users
    to mention the task they want to perform for simplicity. A HuggingFace task
    is different from a model(pytorch). There are a large number of models on HuggingFace
    hub that can be used for a particular task. The user can specify the model or a default
    model will be used.

    Refer to https://huggingface.co/transformers/main_classes/pipelines.html for more details
    on pipelines.
    """

    @property
    def name(self) -> str:
        return 'GenericHuggingfaceModel'

    def __init__(self, function_obj: FunctionCatalogEntry, device: int=-1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pipeline_args = self.default_pipeline_args
        for entry in function_obj.metadata:
            if entry.value.isnumeric():
                pipeline_args[entry.key] = int(entry.value)
            else:
                pipeline_args[entry.key] = entry.value
        self.pipeline_args = pipeline_args
        try_to_import_transformers()
        from transformers import pipeline
        self.hf_function_obj = pipeline(**pipeline_args, device=device)

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)

    @property
    def default_pipeline_args(self) -> dict:
        """
        Arguments that will be passed to the pipeline by default.
        User provided arguments override the default arguments
        """
        return {}

    def input_formatter(self, inputs: Any):
        """
        Function that formats input from EvaDB format to HuggingFace format for that particular HF model
        """
        return inputs

    def output_formatter(self, outputs: Any):
        """
        Function that formats output from HuggingFace format to EvaDB format (pandas dataframe)
        The output can be in various formats, depending on the model. For example:
            {'text' : 'transcript from video'}
            [[{'score': 0.25, 'label': 'bridge'}, {'score': 0.50, 'label': 'car'}]]
        """
        if isinstance(outputs, dict):
            return pd.DataFrame(outputs, index=[0])
        result_list = []
        if outputs != [[]]:
            for row_output in outputs:
                if isinstance(row_output, list):
                    row_output = {k: [dic[k] for dic in row_output] for k in row_output[0]}
                result_list.append(row_output)
        result_df = pd.DataFrame(result_list)
        return result_df

    def forward(self, inputs, *args, **kwargs) -> pd.DataFrame:
        hf_input = self.input_formatter(inputs)
        hf_output = self.hf_function_obj(hf_input, *args, **kwargs)
        evadb_output = self.output_formatter(hf_output)
        return evadb_output

    def to_device(self, device: str) -> GPUCompatible:
        try_to_import_transformers()
        from transformers import pipeline
        self.hf_function_obj = pipeline(**self.pipeline_args, device=device)
        return self

def forward(self, inputs, *args, **kwargs) -> pd.DataFrame:
    hf_input = self.input_formatter(inputs)
    hf_output = self.hf_function_obj(hf_input, *args, **kwargs)
    evadb_output = self.output_formatter(hf_output)
    return evadb_output

