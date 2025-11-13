# Cluster 37

def get_analyzer_engine() -> AnalyzerEngine:
    """Get or create singleton AnalyzerEngine instance."""
    global _analyzer_engine
    if _analyzer_engine is None:
        _analyzer_engine = AnalyzerEngine()
        _analyzer_engine.analyze(text='warm up', language='en')
    return _analyzer_engine

def run(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    model_name = 'en_core_web_lg'
    download_model(model_name)
    analyzer = get_analyzer_engine()
    analyzer_results = analyzer.analyze(text=initial_query, language='en')
    anonymizer_engine = get_anonymizer_engine()
    entity_mapping = dict()
    anonymized_result = anonymizer_engine.anonymize(initial_query, analyzer_results, {'DEFAULT': OperatorConfig('entity_counter', {'entity_mapping': entity_mapping})})
    response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': anonymized_result.text}])
    final_response = response.choices[0].message.content.strip()
    final_response = replace_entities(entity_mapping, final_response)
    return (final_response, response.usage.completion_tokens)

def test_singleton_instances_are_reused():
    """
    Direct test that singleton instances are the same object across calls.
    """
    print('\nTesting singleton instance reuse...')
    try:
        import optillm.plugins.privacy_plugin as privacy_plugin
        importlib.reload(privacy_plugin)
        analyzer1 = privacy_plugin.get_analyzer_engine()
        anonymizer1 = privacy_plugin.get_anonymizer_engine()
        analyzer2 = privacy_plugin.get_analyzer_engine()
        anonymizer2 = privacy_plugin.get_anonymizer_engine()
        assert analyzer1 is analyzer2, 'AnalyzerEngine instances are not the same object!'
        assert anonymizer1 is anonymizer2, 'AnonymizerEngine instances are not the same object!'
        print('✅ Singleton instance test PASSED - Same objects are reused!')
        return True
    except ImportError as e:
        print(f'⚠️  Skipping singleton test - dependencies not installed: {e}')
        return True
    except Exception as e:
        print(f'❌ Singleton test failed: {e}')
        raise

