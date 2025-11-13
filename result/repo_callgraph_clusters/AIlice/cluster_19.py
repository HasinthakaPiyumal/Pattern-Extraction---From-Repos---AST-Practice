# Cluster 19

def build_settings_schema(config):
    return {'type': 'tabs', 'activeTab': 'agent-models', 'tabs': [{'id': 'agent-models', 'title': 'Agent Models', 'content': build_agent_models_schema(config['agentModelConfig'], config['models'])}, {'id': 'model-providers', 'title': 'Model Providers', 'content': build_providers_schema(config['models'])}, {'id': 'inference', 'title': 'Inference', 'content': build_inference_schema(config['temperature'], config['contextWindowRatio'])}]}

