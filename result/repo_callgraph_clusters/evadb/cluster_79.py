# Cluster 79

def gen_hf_io_catalog_entries(function_name: str, metadata: List[FunctionMetadataCatalogEntry]):
    """
    Generates IO Catalog Entries for a HuggingFace Function.
    The attributes of the huggingface model can be extracted from metadata.
    """
    pipeline_args = {arg.key: arg.value for arg in metadata}
    function_input, function_output = infer_output_name_and_type(**pipeline_args)
    annotated_inputs = io_entry_for_inputs(function_name, function_input)
    annotated_outputs = io_entry_for_outputs(function_output)
    return annotated_inputs + annotated_outputs

