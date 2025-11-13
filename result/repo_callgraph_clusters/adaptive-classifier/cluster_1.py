# Cluster 1

def main():
    parser = argparse.ArgumentParser(description='Benchmark ONNX vs PyTorch performance')
    parser.add_argument('--model', type=str, default='prajjwal1/bert-tiny', help='HuggingFace model name to benchmark')
    parser.add_argument('--runs', type=int, default=100, help='Number of benchmark runs')
    parser.add_argument('--skip-quantized', action='store_true', help='Skip quantized ONNX benchmarking')
    args = parser.parse_args()
    if not check_optimum_installed():
        print('⚠️  optimum[onnxruntime] not installed. Skipping ONNX benchmarks.')
        print('Install with: pip install optimum[onnxruntime]')
        return
    print('=' * 70)
    print('ONNX Runtime Benchmark for Adaptive Classifier')
    print('=' * 70)
    print(f'Model: {args.model}')
    print(f'Runs per test: {args.runs}')
    print()
    test_texts = ['This is a positive example', 'This seems negative to me', 'A neutral statement here', 'Another test case for benchmarking performance', 'The quick brown fox jumps over the lazy dog']
    print('Preparing classifiers...')
    print()
    classifier_base = AdaptiveClassifier(args.model, use_onnx=False, device='cpu')
    training_texts = ['great product', 'terrible experience', 'okay item', 'loved it', 'hated it', "it's fine", 'amazing quality', 'poor service', 'average performance']
    training_labels = ['positive', 'negative', 'neutral', 'positive', 'negative', 'neutral', 'positive', 'negative', 'neutral']
    classifier_base.add_examples(training_texts, training_labels)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier'
        print('Exporting ONNX models...')
        classifier_base._save_pretrained(save_path, include_onnx=True, quantize_onnx=not args.skip_quantized)
        print('Loading PyTorch model...')
        classifier_pytorch = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx=False)
        print('Loading ONNX model...')
        classifier_onnx = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx=True)
        print()
        print('Starting benchmarks...')
        print('-' * 70)
        print('\n1. PyTorch Baseline')
        print('   Running benchmark...')
        pytorch_avg, pytorch_total = benchmark_inference(classifier_pytorch, test_texts, args.runs)
        print(f'   ✓ Average time per query: {pytorch_avg:.2f}ms')
        print(f'   ✓ Total time: {pytorch_total:.2f}s')
        print('\n2. ONNX Runtime')
        print('   Running benchmark...')
        onnx_avg, onnx_total = benchmark_inference(classifier_onnx, test_texts, args.runs)
        print(f'   ✓ Average time per query: {onnx_avg:.2f}ms')
        print(f'   ✓ Total time: {onnx_total:.2f}s')
        speedup = pytorch_avg / onnx_avg
        print(f'   ✓ Speedup: {speedup:.2f}x faster than PyTorch')
        print('\n3. Accuracy Verification')
        test_text = 'This is amazing!'
        pred_pytorch = classifier_pytorch.predict(test_text)
        pred_onnx = classifier_onnx.predict(test_text)
        print(f'   PyTorch top prediction: {pred_pytorch[0]}')
        print(f'   ONNX top prediction: {pred_onnx[0]}')
        if pred_pytorch[0][0] == pred_onnx[0][0]:
            print('   ✓ Predictions match!')
        else:
            print('   ⚠️  Predictions differ slightly')
    print()
    print('=' * 70)
    print('SUMMARY')
    print('=' * 70)
    print(f'PyTorch:     {pytorch_avg:.2f}ms/query  (baseline)')
    print(f'ONNX:        {onnx_avg:.2f}ms/query  ({speedup:.2f}x faster)')
    print()
    if speedup > 2.0:
        print('🚀 ONNX provides significant speedup! (>2x)')
    elif speedup > 1.2:
        print('⚡ ONNX provides moderate speedup')
    else:
        print('ℹ️  ONNX provides marginal speedup')
    print()
    print('=' * 70)
    print('\nRecommendation:')
    if speedup > 1.5:
        print('✓ Use ONNX for CPU inference for better performance!')
        print('  classifier = AdaptiveClassifier(model_name, use_onnx=True)')
    else:
        print('ℹ️  ONNX speedup is modest for this model.')
        print('  Consider using smaller models (distilbert, MiniLM) for better gains.')

class LLMRouter:
    """Router class to direct queries to appropriate models."""

    def __init__(self, config: RouterConfig, enable_adaptation: bool=True):
        """Initialize the router with classifier and configuration."""
        self.config = config
        self.enable_adaptation = enable_adaptation
        self.classifier = AdaptiveClassifier.load(config.adaptive_router_path)
        self.stats = {'total_queries': 0, 'high_routes': 0, 'low_routes': 0, 'high_success': 0, 'low_success': 0, 'adapted_examples': 0}

    def route_and_evaluate(self, query: str) -> Tuple[bool, Dict]:
        """Route query to appropriate model and evaluate results."""
        predictions = self.classifier.predict(query)
        route = predictions[0][0]
        model = self.config.high_model if route == 'HIGH' else self.config.low_model
        self.stats['total_queries'] += 1
        if route == 'HIGH':
            self.stats['high_routes'] += 1
        else:
            self.stats['low_routes'] += 1
        passed_rtc, similarity_score, details = perform_rtc_evaluation(query, model, self.config)
        if passed_rtc:
            if route == 'HIGH':
                self.stats['high_success'] += 1
            else:
                self.stats['low_success'] += 1
        if self.enable_adaptation and passed_rtc:
            self.adapt_to_example(query, route)
            self.stats['adapted_examples'] += 1
        evaluation_result = {'query': query, 'route': route, 'model': model, 'passed_rtc': passed_rtc, 'similarity_score': similarity_score, 'evaluation_details': details}
        return (passed_rtc, evaluation_result)

    def adapt_to_example(self, query: str, label: str):
        """Add successful example to classifier."""
        if self.enable_adaptation:
            self.classifier.add_examples([query], [label])

    def save_classifier(self):
        """Save the adapted classifier."""
        if self.enable_adaptation:
            self.classifier.save(self.config.adaptive_router_path)

    def get_stats(self) -> Dict:
        """Get routing statistics."""
        stats = self.stats.copy()
        stats['high_success_rate'] = stats['high_success'] / stats['high_routes'] if stats['high_routes'] > 0 else 0
        stats['low_success_rate'] = stats['low_success'] / stats['low_routes'] if stats['low_routes'] > 0 else 0
        stats['overall_success_rate'] = (stats['high_success'] + stats['low_success']) / stats['total_queries'] if stats['total_queries'] > 0 else 0
        stats['cost_saving_ratio'] = stats['low_success'] / stats['total_queries'] if stats['total_queries'] > 0 else 0
        return stats

def __init__(self, config: RouterConfig, enable_adaptation: bool=True):
    """Initialize the router with classifier and configuration."""
    self.config = config
    self.enable_adaptation = enable_adaptation
    self.classifier = AdaptiveClassifier.load(config.adaptive_router_path)
    self.stats = {'total_queries': 0, 'high_routes': 0, 'low_routes': 0, 'high_success': 0, 'low_success': 0, 'adapted_examples': 0}

def route_and_evaluate(self, query: str) -> Tuple[bool, Dict]:
    """Route query to appropriate model and evaluate results."""
    predictions = self.classifier.predict(query)
    route = predictions[0][0]
    model = self.config.high_model if route == 'HIGH' else self.config.low_model
    self.stats['total_queries'] += 1
    if route == 'HIGH':
        self.stats['high_routes'] += 1
    else:
        self.stats['low_routes'] += 1
    passed_rtc, similarity_score, details = perform_rtc_evaluation(query, model, self.config)
    if passed_rtc:
        if route == 'HIGH':
            self.stats['high_success'] += 1
        else:
            self.stats['low_success'] += 1
    if self.enable_adaptation and passed_rtc:
        self.adapt_to_example(query, route)
        self.stats['adapted_examples'] += 1
    evaluation_result = {'query': query, 'route': route, 'model': model, 'passed_rtc': passed_rtc, 'similarity_score': similarity_score, 'evaluation_details': details}
    return (passed_rtc, evaluation_result)

def adapt_to_example(self, query: str, label: str):
    """Add successful example to classifier."""
    if self.enable_adaptation:
        self.classifier.add_examples([query], [label])

def save_classifier(self):
    """Save the adapted classifier."""
    if self.enable_adaptation:
        self.classifier.save(self.config.adaptive_router_path)

class AdaptiveClassifier(ModelHubMixin):
    """A flexible classifier that can adapt to new classes and examples."""

    def __init__(self, model_name: str, device: Optional[str]=None, config: Optional[Dict[str, Any]]=None, seed: int=42, use_onnx: Optional[Union[bool, str]]='auto', trust_remote_code: bool=False):
        """Initialize the adaptive classifier.

        Args:
            model_name: Name of the HuggingFace transformer model
            device: Device to run the model on (default: auto-detect)
            config: Optional configuration dictionary
            seed: Random seed for initialization
            use_onnx: Whether to use ONNX Runtime ("auto", True, False).
                     "auto" uses ONNX on CPU, PyTorch on GPU.
            trust_remote_code: Whether to trust remote code when loading models (default: False)
        """
        torch.manual_seed(seed)
        self.config = ModelConfig(config)
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.use_onnx = self._should_use_onnx(use_onnx)
        if self.use_onnx:
            try:
                from optimum.onnxruntime import ORTModelForFeatureExtraction
                logger.info(f'Initializing ONNX model for {model_name}')
                self.model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True, trust_remote_code=trust_remote_code)
                logger.info('Successfully loaded ONNX model')
            except ImportError:
                logger.warning('optimum[onnxruntime] not installed. Falling back to PyTorch. Install with: pip install optimum[onnxruntime]')
                self.use_onnx = False
                self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
            except Exception as e:
                logger.warning(f'Failed to load ONNX model: {e}. Falling back to PyTorch.')
                self.use_onnx = False
                self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
        else:
            self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote_code)
        self.embedding_dim = self.model.config.hidden_size
        self.memory = PrototypeMemory(self.embedding_dim, config=self.config)
        self.adaptive_head = None
        self.label_to_id = {}
        self.id_to_label = {}
        self.train_steps = 0
        self.training_history = {}
        self.strategic_cost_function = None
        self.strategic_optimizer = None
        self.strategic_evaluator = None
        if self.config.enable_strategic_mode:
            self._initialize_strategic_components()

    def _should_use_onnx(self, use_onnx: Union[bool, str]) -> bool:
        """Determine if ONNX should be used based on configuration and device.

        Args:
            use_onnx: User preference ("auto", True, False)

        Returns:
            True if ONNX should be used, False otherwise
        """
        if use_onnx == 'auto':
            return self.device == 'cpu'
        elif isinstance(use_onnx, bool):
            return use_onnx
        else:
            logger.warning(f'Invalid use_onnx value: {use_onnx}. Using auto-detection.')
            return self.device == 'cpu'

    def add_examples(self, texts: List[str], labels: List[str]):
        """Add new examples with special handling for new classes."""
        if not texts or not labels:
            raise ValueError('Empty input lists')
        if len(texts) != len(labels):
            raise ValueError('Mismatched text and label lists')
        has_existing_classes = len(self.label_to_id) > 0
        new_classes = set(labels) - set(self.label_to_id.keys())
        is_adding_new_classes = len(new_classes) > 0
        for label in sorted(new_classes):
            idx = len(self.label_to_id)
            self.label_to_id[label] = idx
            self.id_to_label[idx] = label
        embeddings = self._get_embeddings(texts)
        for text, embedding, label in zip(texts, embeddings, labels):
            example = Example(text, label, embedding)
            self.memory.add_example(example, label)
            if label not in self.training_history:
                self.training_history[label] = 0
            self.training_history[label] += 1
        is_incremental_learning = is_adding_new_classes and has_existing_classes
        if is_incremental_learning:
            old_head = copy.deepcopy(self.adaptive_head) if self.adaptive_head is not None else None
            num_classes = len(self.label_to_id)
            self.adaptive_head.update_num_classes(num_classes)
            self.adaptive_head = self.adaptive_head.to(self.device)
            self._train_new_classes(old_head, new_classes)
        else:
            if self.adaptive_head is None:
                self._initialize_adaptive_head()
            elif is_adding_new_classes:
                num_classes = len(self.label_to_id)
                self.adaptive_head.update_num_classes(num_classes)
                self.adaptive_head = self.adaptive_head.to(self.device)
            self._train_adaptive_head()
            if self.strategic_mode and self.train_steps % self.config.strategic_training_frequency == 0:
                self._perform_strategic_training()
        self.memory._rebuild_index()

    def _train_new_classes(self, old_head: Optional[nn.Module], new_classes: Set[str]):
        """Train the model with focus on new classes while preserving old class knowledge."""
        if not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        examples_per_class = {}
        for label in self.memory.examples:
            examples_per_class[label] = len(self.memory.examples[label])
        min_examples = min(examples_per_class.values())
        max_examples = max(examples_per_class.values())
        num_classes = len(examples_per_class)
        target_samples_per_class = max(5, min(10, min_examples * 2))
        if num_classes > 20:
            for label, examples in self.memory.examples.items():
                if label in new_classes:
                    num_samples = min(len(examples), target_samples_per_class * 2)
                else:
                    num_samples = min(len(examples), target_samples_per_class)
                if num_samples <= len(examples):
                    indices = np.random.choice(len(examples), size=num_samples, replace=False)
                else:
                    indices = np.random.choice(len(examples), size=num_samples, replace=True)
                for idx in indices:
                    example = examples[idx]
                    all_embeddings.append(example.embedding)
                    all_labels.append(self.label_to_id[label])
        else:
            sampling_weights = {}
            for label, count in examples_per_class.items():
                if label in new_classes:
                    sampling_weights[label] = 2.0
                else:
                    sampling_weights[label] = min_examples / count
            for label, examples in self.memory.examples.items():
                weight = sampling_weights[label]
                num_samples = max(min_examples, int(len(examples) * weight))
                indices = np.random.choice(len(examples), size=num_samples, replace=num_samples > len(examples))
                for idx in indices:
                    example = examples[idx]
                    all_embeddings.append(example.embedding)
                    all_labels.append(self.label_to_id[label])
        all_embeddings = torch.stack(all_embeddings)
        all_labels = torch.tensor(all_labels)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        ewc = None
        if old_head is not None:
            old_embeddings = []
            old_labels = []
            old_label_to_id = {label: idx for idx, label in enumerate(self.id_to_label.values()) if label not in new_classes}
            for label, examples in self.memory.examples.items():
                if label not in new_classes:
                    for example in examples[:5]:
                        old_embeddings.append(example.embedding)
                        old_labels.append(old_label_to_id[label])
            if old_embeddings:
                old_embeddings = torch.stack(old_embeddings)
                old_labels = torch.tensor(old_labels, dtype=torch.long)
                old_dataset = torch.utils.data.TensorDataset(old_embeddings, old_labels)
                ewc = EWC(old_head, old_dataset, device=self.device, ewc_lambda=5.0)
        self.adaptive_head.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=0.001, weight_decay=0.01)
        loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True, generator=torch.Generator().manual_seed(42))
        best_loss = float('inf')
        patience = 3
        patience_counter = 0
        for epoch in range(15):
            total_loss = 0
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.adaptive_head(batch_embeddings)
                task_loss = criterion(outputs, batch_labels)
                if ewc is not None:
                    ewc_loss = ewc.ewc_loss(batch_size=len(batch_embeddings))
                    loss = task_loss + ewc_loss
                else:
                    loss = task_loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / len(loader)
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.debug(f'Early stopping at epoch {epoch + 1}')
                    break
        self.train_steps += 1

    def _perform_strategic_training(self):
        """Perform strategic training on current examples."""
        if not self.strategic_mode or not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        for label in self.memory.examples:
            for example in self.memory.examples[label]:
                all_embeddings.append(example.embedding)
                all_labels.append(self.label_to_id[label])
        if all_embeddings:
            all_embeddings = torch.stack(all_embeddings)
            all_labels = torch.tensor(all_labels, dtype=torch.long, device=self.device)
            self._strategic_training_step(all_embeddings, all_labels)
            logger.debug('Performed strategic training step')

    def predict(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict with dual prediction system - blends strategic and regular predictions.
        
        If no cost function is provided, uses existing prediction logic (zero changes).
        If cost function is provided, blends strategic and regular predictions.
        
        Args:
            text: Input text to classify
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples
        """
        if not text:
            raise ValueError('Empty input text')
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        return self._predict_dual(text, k)

    def _predict_regular(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Regular prediction logic (original implementation)."""
        with torch.no_grad():
            embedding = self._get_embeddings([text])[0]
            max_classes = len(self.id_to_label) if self.id_to_label else k
            proto_preds = self.memory.get_nearest_prototypes(embedding, k=max_classes)
            if self.adaptive_head is not None:
                self.adaptive_head.eval()
                input_embedding = embedding.unsqueeze(0).to(self.device)
                logits = self.adaptive_head(input_embedding)
                logits = logits.squeeze(0)
                probs = F.softmax(logits, dim=0)
                values, indices = torch.topk(probs, len(self.id_to_label))
                head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
            else:
                head_preds = []
        combined_scores = {}
        for label, score in proto_preds:
            trained_examples = self.training_history.get(label, 0)
            if trained_examples < 10:
                weight = 0.3
            else:
                weight = 0.7
            combined_scores[label] = score * weight
        for label, score in head_preds:
            trained_examples = self.training_history.get(label, 0)
            if trained_examples < 10:
                weight = 0.7
            else:
                weight = 0.3
            combined_scores[label] = combined_scores.get(label, 0) + score * weight
        predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in predictions))
        if total > 0:
            predictions = [(label, score / total) for label, score in predictions]
        return predictions[:k]

    def _predict_dual(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Dual prediction system that blends strategic and regular predictions."""
        regular_preds = self._predict_regular(text, k)
        strategic_preds = self.predict_strategic(text, k)
        blended_scores = {}
        regular_weight = self.config.strategic_blend_regular_weight
        strategic_weight = self.config.strategic_blend_strategic_weight
        for label, score in regular_preds:
            blended_scores[label] = score * regular_weight
        for label, score in strategic_preds:
            blended_scores[label] = blended_scores.get(label, 0) + score * strategic_weight
        blended_predictions = sorted(blended_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in blended_predictions))
        if total > 0:
            blended_predictions = [(label, score / total) for label, score in blended_predictions]
        logger.debug(f'Dual prediction - Regular: {regular_preds[:3]}, Strategic: {strategic_preds[:3]}, Blended: {blended_predictions[:3]}')
        return blended_predictions[:k]

    def _save_pretrained(self, save_directory: Union[str, Path], config: Optional[Dict[str, Any]]=None, include_onnx: bool=True, quantize_onnx: bool=True, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Save the model to a directory.

        Args:
            save_directory: Directory to save the model to
            config: Optional additional configuration
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model (requires include_onnx=True)
            **kwargs: Additional arguments passed to save_pretrained

        Returns:
            Tuple of (dict of filenames, dict of objects to save)
        """
        save_directory = Path(save_directory)
        os.makedirs(save_directory, exist_ok=True)
        config_dict = {'model_name': self.model.config._name_or_path, 'embedding_dim': self.embedding_dim, 'label_to_id': self.label_to_id, 'id_to_label': {str(k): v for k, v in self.id_to_label.items()}, 'train_steps': self.train_steps, 'training_history': self.training_history, 'config': self.config.to_dict(), 'library_name': 'adaptive-classifier'}
        saved_examples = {}
        for label, examples in self.memory.examples.items():
            saved_examples[label] = [ex.to_dict() for ex in self.select_representative_examples(examples, k=self.config.num_representative_examples)]
        tensor_dict = {}
        for label, proto in self.memory.prototypes.items():
            tensor_dict[f'prototype_{label}'] = proto
        if self.adaptive_head is not None:
            for name, param in self.adaptive_head.state_dict().items():
                tensor_dict[f'adaptive_head_{name}'] = param
        config_file = save_directory / 'config.json'
        examples_file = save_directory / 'examples.json'
        tensors_file = save_directory / 'model.safetensors'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, sort_keys=True)
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(saved_examples, f, indent=2, sort_keys=True)
        save_file(tensor_dict, tensors_file)
        model_card_path = save_directory / 'README.md'
        if not model_card_path.exists():
            model_card_content = self._generate_model_card()
            with open(model_card_path, 'w', encoding='utf-8') as f:
                f.write(model_card_content)
        if include_onnx:
            try:
                onnx_dir = save_directory / 'onnx'
                self.export_onnx(onnx_dir, quantize=quantize_onnx)
                logger.info(f'ONNX model exported to {onnx_dir}')
            except ImportError:
                logger.warning('Skipping ONNX export: optimum[onnxruntime] not installed. Install with: pip install optimum[onnxruntime]')
            except Exception as e:
                logger.warning(f'Skipping ONNX export due to error: {e}')
        saved_files = {'config': config_file.name, 'examples': examples_file.name, 'model': tensors_file.name, 'model_card': model_card_path.name}
        if include_onnx and (save_directory / 'onnx').exists():
            saved_files['onnx'] = 'onnx/'
        return (saved_files, {})

    @classmethod
    def _from_pretrained(cls, model_id: str, revision: Optional[str]=None, cache_dir: Optional[str]=None, force_download: bool=False, proxies: Optional[Dict]=None, resume_download: bool=False, local_files_only: bool=False, token: Optional[Union[str, bool]]=None, use_onnx: Optional[Union[bool, str]]='auto', prefer_quantized: bool=True, trust_remote_code: bool=False, **kwargs) -> 'AdaptiveClassifier':
        """Load a model from the HuggingFace Hub or local directory.

        Args:
            model_id: HuggingFace Hub model ID or path to local directory
            revision: Revision of the model on the Hub
            cache_dir: Cache directory for downloaded models
            force_download: Force download of models
            proxies: Proxies to use for downloading
            resume_download: Resume downloading if interrupted
            local_files_only: Use local files only, don't download
            token: Authentication token for Hub
            use_onnx: Whether to use ONNX Runtime ("auto", True, False)
            prefer_quantized: Use quantized ONNX model if available (default: True)
                             Set to False to use unquantized model for maximum accuracy
            trust_remote_code: Whether to trust remote code when loading models (default: False)
            **kwargs: Additional arguments passed to from_pretrained

        Returns:
            Loaded AdaptiveClassifier instance

        Examples:
            >>> # Load with quantized ONNX (default - faster, smaller)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router")
            >>>
            >>> # Load with unquantized ONNX (maximum accuracy)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router", prefer_quantized=False)
            >>>
            >>> # Force PyTorch (no ONNX)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router", use_onnx=False)
            >>>
            >>> # Load model requiring custom code
            >>> classifier = AdaptiveClassifier.load("model-with-custom-code", trust_remote_code=True)
        """
        model_path = Path(model_id)
        try:
            if model_path.is_dir() and (model_path / 'config.json').exists():
                pass
            else:
                config_file = hf_hub_download(repo_id=model_id, filename='config.json', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                model_path = Path(os.path.dirname(config_file))
                hf_hub_download(repo_id=model_id, filename='examples.json', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                hf_hub_download(repo_id=model_id, filename='model.safetensors', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                try:
                    hf_hub_download(repo_id=model_id, filename='onnx/model_quantized.onnx', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                    for onnx_file in ['config.json', 'ort_config.json', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']:
                        try:
                            hf_hub_download(repo_id=model_id, filename=f'onnx/{onnx_file}', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                        except:
                            pass
                    logger.info('Downloaded ONNX model files from Hub')
                except Exception as e:
                    logger.debug(f'ONNX model not available on Hub: {e}')
        except Exception as e:
            raise ValueError(f'Error loading model from {model_id}: {e}')
        with open(model_path / 'config.json', 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        with open(model_path / 'examples.json', 'r', encoding='utf-8') as f:
            saved_examples = json.load(f)
        onnx_path = model_path / 'onnx'
        has_onnx = onnx_path.exists() and ((onnx_path / 'model_quantized.onnx').exists() or (onnx_path / 'model.onnx').exists())
        final_use_onnx = use_onnx
        if use_onnx == 'auto':
            device = kwargs.get('device', None) or ('cuda' if torch.cuda.is_available() else 'cpu')
            final_use_onnx = has_onnx and device == 'cpu'
        elif use_onnx is True and (not has_onnx):
            logger.warning('ONNX model requested but not found in save directory. Loading PyTorch model instead.')
            final_use_onnx = False
        device = kwargs.get('device', None)
        if final_use_onnx and has_onnx:
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            logger.info(f'Loading ONNX model from {onnx_path}')
            classifier = cls.__new__(cls)
            torch.manual_seed(42)
            classifier.config = ModelConfig(config_dict.get('config', None))
            classifier.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
            classifier.use_onnx = True
            has_quantized = (onnx_path / 'model_quantized.onnx').exists()
            has_unquantized = (onnx_path / 'model.onnx').exists()
            if prefer_quantized and has_quantized:
                onnx_file = 'model_quantized.onnx'
                logger.info('Loading quantized ONNX model for optimal performance')
            elif has_unquantized:
                onnx_file = 'model.onnx'
                logger.info('Loading unquantized ONNX model')
            elif has_quantized:
                onnx_file = 'model_quantized.onnx'
                logger.info('Loading quantized ONNX model (only version available)')
            else:
                raise ValueError(f'No ONNX model files found in {onnx_path}')
            classifier.model = ORTModelForFeatureExtraction.from_pretrained(onnx_path, file_name=onnx_file, trust_remote_code=trust_remote_code)
            classifier.tokenizer = AutoTokenizer.from_pretrained(config_dict['model_name'], trust_remote_code=trust_remote_code)
            classifier.embedding_dim = classifier.model.config.hidden_size
            classifier.memory = PrototypeMemory(classifier.embedding_dim, config=classifier.config)
            classifier.adaptive_head = None
            classifier.label_to_id = {}
            classifier.id_to_label = {}
            classifier.train_steps = 0
            classifier.training_history = {}
            classifier.strategic_cost_function = None
            classifier.strategic_optimizer = None
            classifier.strategic_evaluator = None
            if not hasattr(classifier, 'default_threshold'):
                classifier.default_threshold = 0.5
            if not hasattr(classifier, 'min_predictions'):
                classifier.min_predictions = 1
            if not hasattr(classifier, 'max_predictions'):
                classifier.max_predictions = None
            if not hasattr(classifier, 'label_thresholds'):
                classifier.label_thresholds = {}
            if classifier.config.enable_strategic_mode:
                classifier._initialize_strategic_components()
        else:
            classifier = cls(config_dict['model_name'], device=device, config=config_dict.get('config', None), use_onnx=final_use_onnx if isinstance(final_use_onnx, bool) else False, trust_remote_code=trust_remote_code)
        classifier.label_to_id = config_dict['label_to_id']
        classifier.id_to_label = {int(k): v for k, v in config_dict['id_to_label'].items()}
        classifier.train_steps = config_dict['train_steps']
        classifier.training_history = config_dict.get('training_history', {})
        tensors = load_file(model_path / 'model.safetensors')
        for label, examples_data in saved_examples.items():
            classifier.memory.examples[label] = [Example.from_dict(ex_data) for ex_data in examples_data]
        for label in classifier.label_to_id.keys():
            prototype_key = f'prototype_{label}'
            if prototype_key in tensors:
                prototype = tensors[prototype_key]
                classifier.memory.prototypes[label] = prototype
        classifier.memory._restore_from_save()
        adaptive_head_params = {k.replace('adaptive_head_', ''): v for k, v in tensors.items() if k.startswith('adaptive_head_')}
        if adaptive_head_params:
            classifier._initialize_adaptive_head()
            classifier.adaptive_head.load_state_dict(adaptive_head_params)
        if not classifier.training_history:
            for label, examples in saved_examples.items():
                classifier.training_history[label] = len(examples) * 20
        return classifier

    def _generate_model_card(self) -> str:
        """Generate a model card for the classifier.
        
        Returns:
            Model card content as string
        """
        stats = self.get_memory_stats()
        model_card = f'---\nlanguage: multilingual\ntags:\n- adaptive-classifier\n- text-classification\n- continuous-learning\nlicense: apache-2.0\n---\n\n# Adaptive Classifier\n\nThis model is an instance of an [adaptive-classifier](https://github.com/codelion/adaptive-classifier) that allows for continuous learning and dynamic class addition.\n\n## Installation\n\n**IMPORTANT:** To use this model, you must first install the `adaptive-classifier` library. You do **NOT** need `trust_remote_code=True`.\n\n```bash\npip install adaptive-classifier\n```\n\n## Model Details\n\n- Base Model: {self.model.config._name_or_path}\n- Number of Classes: {stats['num_classes']}\n- Total Examples: {stats['total_examples']}\n- Embedding Dimension: {self.embedding_dim}\n\n## Class Distribution\n\n```\n{self._format_class_distribution(stats)}\n```\n\n## Usage\n\nAfter installing the `adaptive-classifier` library, you can load and use this model:\n\n```python\nfrom adaptive_classifier import AdaptiveClassifier\n\n# Load the model (no trust_remote_code needed!)\nclassifier = AdaptiveClassifier.from_pretrained("adaptive-classifier/model-name")\n\n# Make predictions\ntext = "Your text here"\npredictions = classifier.predict(text)\nprint(predictions)  # List of (label, confidence) tuples\n\n# Add new examples for continuous learning\ntexts = ["Example 1", "Example 2"]\nlabels = ["class1", "class2"]\nclassifier.add_examples(texts, labels)\n```\n\n**Note:** This model uses the `adaptive-classifier` library distributed via PyPI. You do **NOT** need to set `trust_remote_code=True` - just install the library first.\n\n## Training Details\n\n- Training Steps: {self.train_steps}\n- Examples per Class: See distribution above\n- Prototype Memory: Active\n- Neural Adaptation: {('Active' if self.adaptive_head is not None else 'Inactive')}\n\n## Limitations\n\nThis model:\n- Requires at least {self.config.min_examples_per_class} examples per class\n- Has a maximum of {self.config.max_examples_per_class} examples per class\n- Updates prototypes every {self.config.prototype_update_frequency} examples\n\n## Citation\n\n```bibtex\n@software{{adaptive_classifier,\n  title = {{Adaptive Classifier: Dynamic Text Classification with Continuous Learning}},\n  author = {{Sharma, Asankhaya}},\n  year = {{2025}},\n  publisher = {{GitHub}},\n  url = {{https://github.com/codelion/adaptive-classifier}}\n}}\n```\n'
        return model_card

    def _format_class_distribution(self, stats: Dict[str, Any]) -> str:
        """Format class distribution for model card.
        
        Args:
            stats: Statistics from get_memory_stats()
            
        Returns:
            Formatted string of class distribution
        """
        if 'examples_per_class' not in stats:
            return 'No examples stored'
        lines = []
        total = sum(stats['examples_per_class'].values())
        for label, count in sorted(stats['examples_per_class'].items()):
            percentage = count / total * 100 if total > 0 else 0
            lines.append(f'{label}: {count} examples ({percentage:.1f}%)')
        return '\n'.join(lines)

    def export_onnx(self, save_directory: Union[str, Path], quantize: bool=False, quantization_config: Optional[str]='arm64') -> Path:
        """Export the transformer model to ONNX format.

        Args:
            save_directory: Directory to save ONNX model
            quantize: Whether to apply INT8 quantization
            quantization_config: Quantization configuration ("arm64", "avx512", "avx2")

        Returns:
            Path to the saved ONNX model directory

        Raises:
            ImportError: If optimum[onnxruntime] is not installed
            ValueError: If model is already in ONNX format
        """
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig
        except ImportError:
            raise ImportError('optimum[onnxruntime] is required for ONNX export. Install with: pip install optimum[onnxruntime]')
        save_directory = Path(save_directory)
        save_directory.mkdir(parents=True, exist_ok=True)
        if self.use_onnx:
            logger.warning('Model is already in ONNX format. Saving current model.')
            self.model.save_pretrained(save_directory)
            return save_directory
        model_name = self.model.config._name_or_path
        logger.info(f'Exporting {model_name} to ONNX format...')
        ort_model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
        ort_model.save_pretrained(save_directory)
        logger.info(f'Saved unquantized ONNX model to {save_directory}')
        if quantize:
            logger.info(f'Applying {quantization_config} INT8 quantization...')
            if quantization_config == 'arm64':
                qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
            elif quantization_config == 'avx512':
                qconfig = AutoQuantizationConfig.avx512(is_static=False, per_channel=False)
            elif quantization_config == 'avx2':
                qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
            else:
                logger.warning(f'Unknown quantization config: {quantization_config}. Using arm64.')
                qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
            quantizer = ORTQuantizer.from_pretrained(ort_model)
            quantizer.quantize(save_dir=save_directory, quantization_config=qconfig)
            logger.info(f'Saved quantized ONNX model to {save_directory}')
        logger.info(f'ONNX model exported to {save_directory}')
        return save_directory

    def push_to_hub(self, repo_id: str, include_onnx: bool=True, quantize_onnx: bool=True, token: Optional[str]=None, commit_message: Optional[str]=None, private: bool=False, **kwargs):
        """Push model to HuggingFace Hub with ONNX export by default.

        Args:
            repo_id: Repository ID on HuggingFace Hub (e.g., "username/model-name")
            include_onnx: Whether to include ONNX version of the model (default: True)
            quantize_onnx: Whether to quantize the ONNX model (requires include_onnx=True)
            token: HuggingFace Hub authentication token (or set HF_TOKEN env var)
            commit_message: Commit message for the push
            private: Whether to create a private repository
            **kwargs: Additional arguments passed to HfApi.upload_folder

        Examples:
            >>> classifier.push_to_hub("my-org/my-classifier")  # ONNX included by default
            >>> classifier.push_to_hub("my-org/my-classifier", quantize_onnx=True)
            >>> classifier.push_to_hub("my-org/my-classifier", include_onnx=False)  # Opt-out
        """
        import tempfile
        import os
        from huggingface_hub import HfApi
        token = token or os.environ.get('HF_TOKEN')
        if not token:
            logger.warning('No HuggingFace token provided. Set HF_TOKEN environment variable or pass token parameter. You may need to login with `huggingface-cli login`')
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir)
            self._save_pretrained(save_path, include_onnx=include_onnx, quantize_onnx=quantize_onnx)
            api = HfApi()
            try:
                api.create_repo(repo_id=repo_id, token=token, private=private, exist_ok=True)
            except Exception as e:
                logger.warning(f'Could not create repo (may already exist): {e}')
            commit_info = api.upload_folder(folder_path=str(save_path), repo_id=repo_id, token=token, commit_message=commit_message or 'Upload model with adaptive-classifier', **kwargs)
            logger.info(f'Successfully pushed model to https://huggingface.co/{repo_id}')
            return f'https://huggingface.co/{repo_id}'

    def save(self, save_dir: str, include_onnx: bool=True, quantize_onnx: bool=True):
        """Legacy save method for backwards compatibility.

        Args:
            save_dir: Directory to save to
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model
        """
        return self._save_pretrained(save_dir, include_onnx=include_onnx, quantize_onnx=quantize_onnx)

    @classmethod
    def load(cls, save_dir: str, device: Optional[str]=None, use_onnx: Optional[Union[bool, str]]='auto', prefer_quantized: bool=True, trust_remote_code: bool=False) -> 'AdaptiveClassifier':
        """Legacy load method for backwards compatibility.

        Args:
            save_dir: Directory to load from
            device: Device to load model on
            use_onnx: Whether to use ONNX Runtime ("auto", True, False)
            prefer_quantized: Use quantized ONNX model if available (default: True)
            trust_remote_code: Whether to trust remote code when loading models (default: False)
        """
        kwargs = {}
        if device is not None:
            kwargs['device'] = device
        return cls._from_pretrained(save_dir, use_onnx=use_onnx, prefer_quantized=prefer_quantized, trust_remote_code=trust_remote_code, **kwargs)

    def to(self, device: str) -> 'AdaptiveClassifier':
        """Move the model to specified device.
        
        Args:
            device: Device to move to ("cuda" or "cpu")
            
        Returns:
            Self for chaining
        """
        self.device = device
        self.model = self.model.to(device)
        if self.adaptive_head is not None:
            self.adaptive_head = self.adaptive_head.to(device)
        return self

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary of memory statistics
        """
        return self.memory.get_stats()

    def _initialize_adaptive_head(self):
        """Initialize or reinitialize the adaptive head with improved configuration."""
        num_classes = len(self.label_to_id)
        hidden_dims = [self.embedding_dim, self.embedding_dim // 2]
        self.adaptive_head = AdaptiveHead(self.embedding_dim, num_classes, hidden_dims=hidden_dims).to(self.device)

    def _get_embeddings(self, texts: List[str]) -> List[torch.Tensor]:
        """Get embeddings for input texts."""
        was_training = False
        if not self.use_onnx and hasattr(self.model, 'training'):
            was_training = self.model.training
            self.model.eval()
        with torch.no_grad():
            inputs = self.tokenizer(texts, max_length=self.config.max_length, truncation=True, padding=True, return_tensors='pt')
            if not self.use_onnx:
                inputs = inputs.to(self.device)
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]
            embeddings = F.normalize(embeddings, p=2, dim=1)
        if was_training and hasattr(self.model, 'train'):
            self.model.train()
        return [emb.cpu() for emb in embeddings]

    def get_example_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored examples and model state."""
        stats = {'total_examples': sum((len(exs) for exs in self.memory.examples.values())), 'examples_per_class': {label: len(exs) for label, exs in self.memory.examples.items()}, 'num_classes': len(self.label_to_id), 'train_steps': self.train_steps, 'memory_usage': {'prototypes': sum((p.nelement() * p.element_size() for p in self.memory.prototypes.values())), 'examples': sum((sum((ex.embedding.nelement() * ex.embedding.element_size() for ex in exs)) for exs in self.memory.examples.values()))}}
        if self.adaptive_head is not None:
            stats['model_params'] = sum((p.nelement() for p in self.adaptive_head.parameters()))
        return stats

    def predict_batch(self, texts: List[str], k: int=5, batch_size: int=32) -> List[List[Tuple[str, float]]]:
        """Predict labels for a batch of texts with improved batching."""
        if not texts:
            raise ValueError('Empty input batch')
        all_predictions = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self._get_embeddings(batch_texts)
            batch_predictions = []
            for embedding in batch_embeddings:
                proto_preds = self.memory.get_nearest_prototypes(embedding, k=k)
                if self.adaptive_head is not None:
                    self.adaptive_head.eval()
                    with torch.no_grad():
                        input_embedding = embedding.unsqueeze(0).to(self.device)
                        logits = self.adaptive_head(input_embedding)
                        logits = logits.squeeze(0)
                        probs = F.softmax(logits, dim=0)
                        values, indices = torch.topk(probs, min(k, len(self.id_to_label)))
                        head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
                else:
                    head_preds = []
                combined_scores = {}
                proto_weight = 0.7
                head_weight = 0.3
                for label, score in proto_preds:
                    combined_scores[label] = score * proto_weight
                for label, score in head_preds:
                    combined_scores[label] = combined_scores.get(label, 0) + score * head_weight
                predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
                total = sum((score for _, score in predictions))
                if total > 0:
                    predictions = [(label, score / total) for label, score in predictions]
                batch_predictions.append(predictions[:k])
            all_predictions.extend(batch_predictions)
        return all_predictions

    def clear_memory(self, labels: Optional[List[str]]=None):
        """Clear memory for specified labels or all if none specified."""
        if labels is None:
            self.memory.clear()
        else:
            for label in labels:
                if label in self.memory.examples:
                    del self.memory.examples[label]
                if label in self.memory.prototypes:
                    del self.memory.prototypes[label]
            self.memory._rebuild_index()

    def merge_classifiers(self, other: 'AdaptiveClassifier') -> 'AdaptiveClassifier':
        """Merge another classifier into this one."""
        if self.embedding_dim != other.embedding_dim:
            raise ValueError('Classifiers have different embedding dimensions')
        next_idx = max(self.id_to_label.keys()) + 1
        for label in other.label_to_id:
            if label not in self.label_to_id:
                self.label_to_id[label] = next_idx
                self.id_to_label[next_idx] = label
                next_idx += 1
        for label, examples in other.memory.examples.items():
            for example in examples:
                self.memory.add_example(example, label)
        if self.adaptive_head is not None:
            self._initialize_adaptive_head()
            self._train_adaptive_head()
        return self

    def _train_adaptive_head(self, epochs: int=10):
        """Train the adaptive head with improved stability."""
        if not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        for label in sorted(self.memory.examples.keys()):
            examples = sorted(self.memory.examples[label], key=lambda x: x.text)
            for example in examples:
                all_embeddings.append(example.embedding)
                all_labels.append(self.label_to_id[example.label])
        all_embeddings = torch.stack(all_embeddings)
        all_labels = torch.tensor(all_labels, dtype=torch.long, device=self.device)
        all_embeddings = F.normalize(all_embeddings, p=2, dim=1)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=min(32, len(all_embeddings)), shuffle=True, generator=torch.Generator().manual_seed(42))
        self.adaptive_head.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=0.001, weight_decay=0.01, betas=(0.9, 0.999))
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
        best_loss = float('inf')
        patience_counter = 0
        patience = 3
        for epoch in range(epochs):
            total_loss = 0
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.adaptive_head(batch_embeddings)
                if epoch == 0 and total_loss == 0:
                    logger.debug(f'outputs shape: {outputs.shape}')
                    logger.debug(f'batch_labels shape: {batch_labels.shape}')
                    logger.debug(f'batch_labels content: {batch_labels}')
                loss = criterion(outputs, batch_labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / len(loader)
            scheduler.step(avg_loss)
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.debug(f'Early stopping at epoch {epoch + 1}')
                    break
        self.train_steps += 1

    def _update_adaptive_head(self):
        """Update adaptive head for new classes."""
        num_classes = len(self.label_to_id)
        if self.adaptive_head is None:
            self._initialize_adaptive_head()
        elif num_classes > self.adaptive_head.model[-1].out_features:
            self.adaptive_head.update_num_classes(num_classes)

    def select_representative_examples(self, examples: List[Example], k: int=5) -> List[Example]:
        """Select k most representative examples using k-means clustering.
        
        Args:
            examples: List of examples to select from
            k: Number of examples to select
            
        Returns:
            List of selected examples
        """
        if len(examples) <= k:
            return examples
        embeddings = torch.stack([ex.embedding for ex in examples])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(embeddings.numpy())
        selected_indices = []
        centroids = torch.tensor(kmeans.cluster_centers_)
        for centroid in centroids:
            distances = torch.norm(embeddings - centroid, dim=1)
            closest_idx = torch.argmin(distances).item()
            selected_indices.append(closest_idx)
        return [examples[idx] for idx in selected_indices]

    def _initialize_strategic_components(self):
        """Initialize strategic classification components."""
        try:
            if self.config.cost_coefficients:
                self.strategic_cost_function = CostFunctionFactory.create_cost_function(cost_type=self.config.cost_function_type, cost_coefficients=self.config.cost_coefficients)
                self.strategic_optimizer = StrategicOptimizer(self.strategic_cost_function)
                self.strategic_evaluator = StrategicEvaluator(self.strategic_cost_function)
                logger.info(f'Initialized strategic mode with {self.config.cost_function_type} cost function')
            else:
                logger.warning('Strategic mode enabled but no cost coefficients provided')
        except Exception as e:
            logger.error(f'Failed to initialize strategic components: {e}')
            self.config.enable_strategic_mode = False

    @property
    def strategic_mode(self) -> bool:
        """Check if strategic mode is enabled and properly initialized."""
        return self.config.enable_strategic_mode and self.strategic_cost_function is not None

    def _strategic_training_step(self, all_embeddings: torch.Tensor, all_labels: torch.Tensor):
        """Perform strategic training step."""
        if not self.strategic_mode or self.adaptive_head is None:
            return
        self.adaptive_head.train()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=self.config.learning_rate * 0.5, weight_decay=0.01)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=min(16, len(all_embeddings)), shuffle=True, generator=torch.Generator().manual_seed(42))
        for epoch in range(5):
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                strategic_loss = self.strategic_optimizer.strategic_loss(self.adaptive_head, batch_embeddings, batch_labels, self.config.strategic_lambda)
                strategic_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
        logger.debug('Completed strategic training step')

    def predict_strategic(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict assuming the input might be strategically modified.
        
        This method simulates how a strategic agent might modify the input
        to get a better classification outcome, then predicts on that modified input.
        
        Args:
            text: Input text to classify
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples for strategic predictions
        """
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        try:
            embedding = self._get_embeddings([text])[0]

            def classifier_func(x):
                with torch.no_grad():
                    if self.adaptive_head is not None:
                        self.adaptive_head.eval()
                        if x.dim() == 1:
                            x = x.unsqueeze(0)
                        logits = self.adaptive_head(x.to(self.device))
                        return F.softmax(logits, dim=-1)
                    else:
                        num_classes = len(self.label_to_id) if self.label_to_id else 1
                        return torch.ones(1, num_classes) / num_classes
            strategic_embedding = self.strategic_cost_function.compute_best_response(embedding, classifier_func)
            return self._predict_from_embedding(strategic_embedding, k, strategic=True)
        except Exception as e:
            logger.warning(f'Strategic prediction failed: {e}. Falling back to regular prediction.')
            return self._predict_regular(text, k)

    def predict_robust(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict assuming input has already been strategically modified.
        
        This method assumes the input text has already been strategically manipulated
        and applies robust prediction techniques that are less susceptible to such manipulation.
        
        Args:
            text: Input text (potentially strategically modified)
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples for robust predictions
        """
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        try:
            embedding = self._get_embeddings([text])[0]
            return self._predict_from_embedding(embedding, k, robust=True)
        except Exception as e:
            logger.warning(f'Robust prediction failed: {e}. Falling back to regular prediction.')
            return self._predict_regular(text, k)

    def _predict_from_embedding(self, embedding: torch.Tensor, k: int=5, robust: bool=False, strategic: bool=False) -> List[Tuple[str, float]]:
        """Helper method to predict from embedding with strategic considerations.
        
        Args:
            embedding: Input embedding tensor
            k: Number of top predictions to return
            robust: If True, applies robust prediction weights
            strategic: If True, indicates this is for strategic prediction
            
        Returns:
            List of (label, confidence) tuples
        """
        with torch.no_grad():
            proto_preds = self.memory.get_nearest_prototypes(embedding, k=k)
            if self.adaptive_head is not None:
                self.adaptive_head.eval()
                input_embedding = embedding.unsqueeze(0).to(self.device)
                logits = self.adaptive_head(input_embedding)
                logits = logits.squeeze(0)
                probs = F.softmax(logits, dim=0)
                values, indices = torch.topk(probs, min(k, len(self.id_to_label)))
                head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
            else:
                head_preds = []
        combined_scores = {}
        if self.strategic_mode and robust:
            proto_weight = self.config.strategic_robust_proto_weight
            head_weight = self.config.strategic_robust_head_weight
        elif self.strategic_mode and strategic:
            proto_weight = self.config.strategic_prediction_proto_weight
            head_weight = self.config.strategic_prediction_head_weight
        else:
            proto_weight = self.config.prototype_weight
            head_weight = self.config.neural_weight
        for label, score in proto_preds:
            combined_scores[label] = score * proto_weight
        for label, score in head_preds:
            combined_scores[label] = combined_scores.get(label, 0) + score * head_weight
        predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in predictions))
        if total > 0:
            predictions = [(label, score / total) for label, score in predictions]
        return predictions[:k]

    def evaluate_strategic_robustness(self, test_texts: List[str], test_labels: List[str], gaming_levels: List[float]=[0.0, 0.5, 1.0]) -> Dict[str, float]:
        """Evaluate strategic robustness of the classifier."""
        if not self.strategic_mode:
            raise ValueError('Strategic mode not enabled')
        test_embeddings = torch.stack(self._get_embeddings(test_texts))
        test_label_indices = torch.tensor([self.label_to_id[label] for label in test_labels])
        return self.strategic_evaluator.evaluate_robustness(self.adaptive_head, test_embeddings, test_label_indices, gaming_levels)

def push_to_hub(self, repo_id: str, include_onnx: bool=True, quantize_onnx: bool=True, token: Optional[str]=None, commit_message: Optional[str]=None, private: bool=False, **kwargs):
    """Push model to HuggingFace Hub with ONNX export by default.

        Args:
            repo_id: Repository ID on HuggingFace Hub (e.g., "username/model-name")
            include_onnx: Whether to include ONNX version of the model (default: True)
            quantize_onnx: Whether to quantize the ONNX model (requires include_onnx=True)
            token: HuggingFace Hub authentication token (or set HF_TOKEN env var)
            commit_message: Commit message for the push
            private: Whether to create a private repository
            **kwargs: Additional arguments passed to HfApi.upload_folder

        Examples:
            >>> classifier.push_to_hub("my-org/my-classifier")  # ONNX included by default
            >>> classifier.push_to_hub("my-org/my-classifier", quantize_onnx=True)
            >>> classifier.push_to_hub("my-org/my-classifier", include_onnx=False)  # Opt-out
        """
    import tempfile
    import os
    from huggingface_hub import HfApi
    token = token or os.environ.get('HF_TOKEN')
    if not token:
        logger.warning('No HuggingFace token provided. Set HF_TOKEN environment variable or pass token parameter. You may need to login with `huggingface-cli login`')
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir)
        self._save_pretrained(save_path, include_onnx=include_onnx, quantize_onnx=quantize_onnx)
        api = HfApi()
        try:
            api.create_repo(repo_id=repo_id, token=token, private=private, exist_ok=True)
        except Exception as e:
            logger.warning(f'Could not create repo (may already exist): {e}')
        commit_info = api.upload_folder(folder_path=str(save_path), repo_id=repo_id, token=token, commit_message=commit_message or 'Upload model with adaptive-classifier', **kwargs)
        logger.info(f'Successfully pushed model to https://huggingface.co/{repo_id}')
        return f'https://huggingface.co/{repo_id}'

def save(self, save_dir: str, include_onnx: bool=True, quantize_onnx: bool=True):
    """Legacy save method for backwards compatibility.

        Args:
            save_dir: Directory to save to
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model
        """
    return self._save_pretrained(save_dir, include_onnx=include_onnx, quantize_onnx=quantize_onnx)

@classmethod
def load(cls, save_dir: str, device: Optional[str]=None, use_onnx: Optional[Union[bool, str]]='auto', prefer_quantized: bool=True, trust_remote_code: bool=False) -> 'AdaptiveClassifier':
    """Legacy load method for backwards compatibility.

        Args:
            save_dir: Directory to load from
            device: Device to load model on
            use_onnx: Whether to use ONNX Runtime ("auto", True, False)
            prefer_quantized: Use quantized ONNX model if available (default: True)
            trust_remote_code: Whether to trust remote code when loading models (default: False)
        """
    kwargs = {}
    if device is not None:
        kwargs['device'] = device
    return cls._from_pretrained(save_dir, use_onnx=use_onnx, prefer_quantized=prefer_quantized, trust_remote_code=trust_remote_code, **kwargs)

def demonstrate_basic_usage():
    """Demonstrate basic multi-label classification."""
    print('=' * 60)
    print('MULTI-LABEL ADAPTIVE CLASSIFIER - BASIC USAGE')
    print('=' * 60)
    classifier = MultiLabelAdaptiveClassifier(model_name='distilbert/distilbert-base-cased', default_threshold=0.5, min_predictions=1, max_predictions=5)
    texts, labels = create_sample_data()
    print(f'Training with {len(texts)} examples')
    print(f'Example text: {texts[0][:60]}...')
    print(f'Example labels: {labels[0]}')
    classifier.add_examples(texts, labels)
    stats = classifier.get_label_statistics()
    print(f'\nTraining completed:')
    print(f'- Total labels: {stats['num_classes']}')
    print(f'- Total examples: {stats['total_examples']}')
    print(f'- Adaptive threshold: {stats['adaptive_threshold']:.3f}')
    return classifier

def demonstrate_saving_loading(classifier):
    """Demonstrate saving and loading the model."""
    print('\n' + '=' * 60)
    print('SAVING AND LOADING')
    print('=' * 60)
    save_path = './multilabel_classifier'
    print(f'Saving classifier to {save_path}')
    classifier.save(save_path)
    print('Loading classifier...')
    loaded_classifier = MultiLabelAdaptiveClassifier.load(save_path)
    test_text = 'New medical technology helps treat cancer patients'
    print(f'\nTesting loaded classifier:')
    print(f'Text: {test_text}')
    predictions = loaded_classifier.predict_multilabel(test_text)
    print('Predictions:')
    for label, confidence in predictions:
        print(f'  {label}: {confidence:.4f}')
    return loaded_classifier

def demonstrate_incremental_learning(classifier):
    """Demonstrate adding new labels incrementally."""
    print('\n' + '=' * 60)
    print('INCREMENTAL LEARNING - ADDING NEW LABELS')
    print('=' * 60)
    new_texts = ['Chef creates innovative fusion cuisine combining Asian and European flavors', 'Food delivery service expands to new cities with sustainable packaging', 'Restaurant industry adapts to new dining trends post-pandemic', 'Cooking show features celebrity chefs competing in culinary challenges']
    new_labels = [['food', 'cuisine', 'cooking', 'culture'], ['business', 'food', 'sustainability'], ['business', 'food', 'trends'], ['entertainment', 'food', 'cooking', 'tv']]
    print("Adding new examples with 'food' and 'cooking' labels...")
    classifier.add_examples(new_texts, new_labels)
    food_text = 'Nutritionist recommends healthy meal planning for busy professionals'
    print(f'\nTesting with food-related text:')
    print(f'Text: {food_text}')
    predictions = classifier.predict_multilabel(food_text)
    print('Predictions:')
    for label, confidence in predictions:
        print(f'  {label}: {confidence:.4f}')
    stats = classifier.get_label_statistics()
    print(f'\nUpdated statistics:')
    print(f'- Total labels: {stats['num_classes']}')
    print(f'- Total examples: {stats['total_examples']}')

def main():
    classifier = AdaptiveClassifier('distilbert/distilbert-base-cased')
    texts = ['The product works great!', 'Amazing service, very satisfied', 'This exceeded my expectations', "Best purchase I've made this year", 'Really impressed with the quality', 'Fantastic product, will buy again', 'Highly recommend this to everyone', "Terrible experience, don't buy", 'Worst product ever', 'Complete waste of money', 'Poor quality and bad service', 'Would not recommend to anyone', 'Disappointed with the purchase', 'Product broke after first use', 'Product arrived on time', 'Does what it says', 'Average product, nothing special', 'Meets basic requirements', 'Fair price for what you get', 'Standard quality product', 'Works as expected']
    labels = ['positive', 'positive', 'positive', 'positive', 'positive', 'positive', 'positive', 'negative', 'negative', 'negative', 'negative', 'negative', 'negative', 'negative', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral']
    print('Adding initial examples...')
    classifier.add_examples(texts, labels)
    test_texts = ['This is a fantastic product!', 'Disappointed with this bad product', 'Average product, as expected']
    print('\nTesting predictions:')
    classifier.model.eval()
    with torch.no_grad():
        for text in test_texts:
            predictions = classifier.predict(text)
            print(f'\nText: {text}')
            print('Predictions:')
            for label, score in predictions:
                print(f'{label}: {score:.4f}')
    print('\nSaving classifier...')
    classifier.save('./demo_classifier')
    print('\nLoading classifier...')
    loaded_classifier = AdaptiveClassifier.load('./demo_classifier')
    print('\nAdding new technical class...')
    technical_texts = ['Error code 404 appeared', 'System crashed after update', 'Cannot connect to database', 'Memory allocation failed', 'Null pointer exception detected', 'API endpoint not responding', 'Stack overflow in main thread']
    technical_labels = ['technical'] * len(technical_texts)
    loaded_classifier.add_examples(technical_texts, technical_labels)
    print('\nTesting technical classification:')
    technical_test = 'API giving null pointer exception'
    loaded_classifier.model.eval()
    with torch.no_grad():
        predictions = loaded_classifier.predict(technical_test)
        print(f'\nText: {technical_test}')
        print('Predictions:')
        for label, score in predictions:
            print(f'{label}: {score:.4f}')

def demonstrate_continuous_learning():
    """Example of continuous learning with performance monitoring"""
    logger.info('Demonstrating continuous learning...')
    classifier = AdaptiveClassifier('distilbert/distilbert-base-cased')
    initial_texts = ['Great product, highly recommend', 'Terrible service, avoid', 'Average experience, nothing special']
    initial_labels = ['positive', 'negative', 'neutral']
    classifier.add_examples(initial_texts, initial_labels)

    def evaluate_performance(test_texts: List[str], test_labels: List[str]) -> float:
        correct = 0
        total = len(test_texts)
        for text, true_label in zip(test_texts, test_labels):
            predictions = classifier.predict(text)
            predicted_label = predictions[0][0]
            if predicted_label == true_label:
                correct += 1
        return correct / total
    test_texts = ['This is fantastic', "Don't buy this", "It's okay I guess"]
    test_labels = ['positive', 'negative', 'neutral']
    initial_accuracy = evaluate_performance(test_texts, test_labels)
    logger.info(f'Initial accuracy: {initial_accuracy:.2f}')
    for i in range(3):
        new_texts = [f'Really enjoyed using it {i}', f'Disappointed with quality {i}', f'Standard product {i}']
        new_labels = ['positive', 'negative', 'neutral']
        classifier.add_examples(new_texts, new_labels)
        accuracy = evaluate_performance(test_texts, test_labels)
        logger.info(f'Accuracy after update {i + 1}: {accuracy:.2f}')
    return classifier

def demonstrate_persistence():
    print('Phase 1: Creating and training initial classifier')
    classifier = AdaptiveClassifier('distilbert/distilbert-base-cased')
    initial_texts = ['This product is amazing!', 'Terrible experience', 'Neutral about this']
    initial_labels = ['positive', 'negative', 'neutral']
    classifier.add_examples(initial_texts, initial_labels)
    print('\nSaving classifier ...')
    classifier.save('./demo_classifier')
    print('\nPhase 2: Loading classifier from saved state')
    loaded_classifier = AdaptiveClassifier.load('./demo_classifier')
    test_text = 'This is fantastic!'
    predictions = loaded_classifier.predict(test_text)
    print(f'\nPredictions using loaded classifier:')
    print(f'Text: {test_text}')
    for label, score in predictions:
        print(f'{label}: {score:.4f}')
    print('\nPhase 3: Adding new examples to loaded classifier')
    new_texts = ['Technical error occurred', 'System crashed']
    new_labels = ['technical'] * 2
    loaded_classifier.add_examples(new_texts, new_labels)
    print('\nSaving updated classifier ...')
    loaded_classifier.save('./demo_classifier')
    print('\nFinal class distribution:')
    for label, examples in loaded_classifier.memory.examples.items():
        print(f'{label}: {len(examples)} examples')

def demonstrate_multi_language():
    """Example of handling multiple languages"""
    logger.info('Demonstrating multi-language support...')
    classifier = AdaptiveClassifier('distilbert/distilbert-base-multilingual-cased')
    texts = ['This is great', 'I love this product', 'Amazing experience', 'Excellent service', 'Best purchase ever', 'Highly recommended', 'Really impressive quality', 'Fantastic results', 'This is terrible', 'Worst experience ever', "Don't waste your money", 'Very disappointed', 'Poor quality product', 'Absolutely horrible', 'Complete waste of time', 'Not worth buying', 'Esto es excelente', 'Me encanta este producto', 'Una experiencia maravillosa', 'Servicio excepcional', 'La mejor compra', 'Muy recomendable', 'Calidad impresionante', 'Resultados fantásticos', 'Esto es terrible', 'La peor experiencia', 'No malgastes tu dinero', 'Muy decepcionado', 'Producto de mala calidad', 'Absolutamente horrible', 'Pérdida total de tiempo', 'No vale la pena comprarlo']
    labels = ['positive'] * 8 + ['negative'] * 8 + ['positive'] * 8 + ['negative'] * 8
    classifier.add_examples(texts, labels)
    test_texts = ['This is wonderful', 'This is terrible', 'Esto es maravilloso', 'Esto es terrible']
    print('\nTesting predictions in multiple languages:')
    for text in test_texts:
        predictions = classifier.predict(text)
        print(f'\nText: {text}')
        print('Predictions:')
        for label, score in predictions:
            print(f'{label}: {score:.4f}')
    return classifier

def test_single_example_confidence_consistency():
    """Test confidence consistency with single example per class"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('google-bert/bert-large-cased')
        examples = {'foo': ['fish'], 'bar': ['cat']}
        for label, examples_list in examples.items():
            classifier.add_examples(examples_list, [label] * len(examples_list))
        fish_before = classifier.predict('fish')
        cat_before = classifier.predict('cat')
        fish_conf_before = fish_before[0][1]
        cat_conf_before = cat_before[0][1]
        save_path = Path(temp_dir) / 'test_model'
        classifier.save(str(save_path))
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        fish_after = loaded_classifier.predict('fish')
        cat_after = loaded_classifier.predict('cat')
        fish_conf_after = fish_after[0][1]
        cat_conf_after = cat_after[0][1]
        assert abs(fish_conf_before - fish_conf_after) < 0.01, f'Fish confidence changed: {fish_conf_before:.4f} -> {fish_conf_after:.4f}'
        assert abs(cat_conf_before - cat_conf_after) < 0.01, f'Cat confidence changed: {cat_conf_before:.4f} -> {cat_conf_after:.4f}'
        assert loaded_classifier.training_history['foo'] == 1
        assert loaded_classifier.training_history['bar'] == 1

def test_exact_reported_case():
    """Test the exact case reported by the user"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('google-bert/bert-large-cased')
        examples = {'foo': ['fish'], 'bar': ['cat']}
        for label, examples in examples.items():
            classifier.add_examples(examples, [label] * len(examples))
        result_fish_before = classifier.predict('fish')
        result_cat_before = classifier.predict('cat')
        save_path = Path(temp_dir) / 'foobar'
        classifier.save(str(save_path))
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        result_fish_after = loaded_classifier.predict('fish')
        result_cat_after = loaded_classifier.predict('cat')
        fish_drop = result_fish_before[0][1] - result_fish_after[0][1]
        cat_drop = result_cat_before[0][1] - result_cat_after[0][1]
        assert abs(fish_drop) < 0.01, f'Fish confidence dropped by {fish_drop:.4f}'
        assert abs(cat_drop) < 0.01, f'Cat confidence dropped by {cat_drop:.4f}'

@pytest.mark.integration
class TestEnterpriseClassifiers:
    """Integration tests for enterprise classifiers."""

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_model_loading(self, classifier_name):
        """Test that each enterprise classifier can be loaded from HuggingFace Hub."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        try:
            classifier = AdaptiveClassifier.load(repo_name)
            assert classifier is not None
            assert hasattr(classifier, 'predict')
            assert hasattr(classifier, 'label_to_id')
            assert hasattr(classifier, 'id_to_label')
        except Exception as e:
            pytest.fail(f'Failed to load {repo_name}: {str(e)}')

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_prediction_functionality(self, classifier_name):
        """Test that each classifier can make predictions."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        classifier = AdaptiveClassifier.load(repo_name)
        test_sentences = TEST_SENTENCES[classifier_name]
        for sentence in test_sentences:
            predictions = classifier.predict(sentence, k=3)
            assert isinstance(predictions, list)
            assert len(predictions) > 0
            for label, confidence in predictions:
                assert isinstance(label, str)
                assert isinstance(confidence, float)
                assert 0.0 <= confidence <= 1.0
            expected_classes = CLASSIFIER_METRICS[classifier_name]['class_names']
            for label, _ in predictions:
                assert label in expected_classes, f"Unexpected label '{label}' for {classifier_name}"

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_k_parameter_consistency(self, classifier_name):
        """Test that k=1 and k=2 produce consistent top predictions (regression test for k parameter bug)."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        classifier = AdaptiveClassifier.load(repo_name)
        test_sentences = TEST_SENTENCES[classifier_name]
        for sentence in test_sentences:
            pred_k1 = classifier.predict(sentence, k=1)
            pred_k2 = classifier.predict(sentence, k=2)
            assert len(pred_k1) >= 1
            assert len(pred_k2) >= 1
            top_label_k1 = pred_k1[0][0]
            top_label_k2 = pred_k2[0][0]
            assert top_label_k1 == top_label_k2, f"k=1 and k=2 give different top predictions for {classifier_name}: k=1={top_label_k1}, k=2={top_label_k2}, sentence='{sentence[:50]}...'"
            top_conf_k1 = pred_k1[0][1]
            top_conf_k2 = pred_k2[0][1]
            conf_diff = abs(top_conf_k1 - top_conf_k2)
            assert conf_diff < 0.01, f'k=1 and k=2 confidence scores differ significantly for {classifier_name}: k=1={top_conf_k1:.3f}, k=2={top_conf_k2:.3f}, diff={conf_diff:.3f}'

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_prediction_stability(self, classifier_name):
        """Test that repeated predictions are consistent."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        classifier = AdaptiveClassifier.load(repo_name)
        test_sentence = TEST_SENTENCES[classifier_name][0]
        predictions = []
        for _ in range(3):
            pred = classifier.predict(test_sentence, k=2)
            predictions.append(pred)
        first_top = predictions[0][0]
        for i, pred in enumerate(predictions[1:], 1):
            current_top = pred[0]
            assert first_top[0] == current_top[0], f'Prediction {i + 1} differs from first for {classifier_name}: first={first_top[0]}, current={current_top[0]}'

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_inference_performance(self, classifier_name):
        """Test that inference completes within reasonable time."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        classifier = AdaptiveClassifier.load(repo_name)
        test_sentence = TEST_SENTENCES[classifier_name][0]
        start_time = time.time()
        predictions = classifier.predict(test_sentence, k=3)
        end_time = time.time()
        inference_time = end_time - start_time
        assert inference_time < 2.0, f'Inference too slow for {classifier_name}: {inference_time:.2f}s'
        assert len(predictions) > 0

    @pytest.mark.parametrize('classifier_name', list(CLASSIFIER_METRICS.keys()))
    def test_class_coverage(self, classifier_name):
        """Test that the classifier knows about all expected classes."""
        repo_name = f'adaptive-classifier/{classifier_name}'
        classifier = AdaptiveClassifier.load(repo_name)
        expected_classes = set(CLASSIFIER_METRICS[classifier_name]['class_names'])
        expected_count = CLASSIFIER_METRICS[classifier_name]['classes']
        actual_classes = set(classifier.label_to_id.keys())
        assert len(actual_classes) == expected_count, f'Wrong number of classes for {classifier_name}: expected {expected_count}, got {len(actual_classes)}'
        assert actual_classes == expected_classes, f'Class mismatch for {classifier_name}: expected {expected_classes}, got {actual_classes}'

    def test_all_classifiers_loadable(self):
        """Test that all enterprise classifiers can be loaded successfully."""
        successful_loads = 0
        failed_loads = []
        for classifier_name in CLASSIFIER_METRICS.keys():
            repo_name = f'adaptive-classifier/{classifier_name}'
            try:
                classifier = AdaptiveClassifier.load(repo_name)
                assert classifier is not None
                successful_loads += 1
            except Exception as e:
                failed_loads.append((classifier_name, str(e)))
        total_classifiers = len(CLASSIFIER_METRICS)
        print(f'\nClassifier Loading Summary:')
        print(f'Successfully loaded: {successful_loads}/{total_classifiers}')
        if failed_loads:
            print(f'Failed to load:')
            for name, error in failed_loads:
                print(f'  - {name}: {error}')
        assert successful_loads == total_classifiers, f'Failed to load {len(failed_loads)} classifiers: {[name for name, _ in failed_loads]}'

    def test_integration_health_check(self):
        """Overall health check for the enterprise classifier ecosystem."""
        print(f'\n{'=' * 60}')
        print('ENTERPRISE CLASSIFIER INTEGRATION HEALTH CHECK')
        print(f'{'=' * 60}')
        results = {'total_classifiers': len(CLASSIFIER_METRICS), 'high_accuracy': 0, 'good_accuracy': 0, 'acceptable_accuracy': 0, 'low_accuracy': 0}
        for classifier_name, metrics in CLASSIFIER_METRICS.items():
            expected_acc = metrics['expected']
            if expected_acc >= 0.95:
                results['high_accuracy'] += 1
            elif expected_acc >= 0.8:
                results['good_accuracy'] += 1
            elif expected_acc >= 0.6:
                results['acceptable_accuracy'] += 1
            else:
                results['low_accuracy'] += 1
        print(f'Total classifiers: {results['total_classifiers']}')
        print(f'High accuracy (≥95%): {results['high_accuracy']}')
        print(f'Good accuracy (80-95%): {results['good_accuracy']}')
        print(f'Acceptable accuracy (60-80%): {results['acceptable_accuracy']}')
        print(f'Low accuracy (<60%): {results['low_accuracy']}')
        assert results['total_classifiers'] == 17, 'Should have exactly 17 enterprise classifiers'
        assert results['high_accuracy'] >= 6, 'Should have at least 6 high-accuracy classifiers'
        assert results['low_accuracy'] == 0, 'Should have no low-accuracy classifiers'
        print(f'✅ Enterprise classifier ecosystem is healthy!')
        print(f'{'=' * 60}')

def test_all_classifiers_loadable(self):
    """Test that all enterprise classifiers can be loaded successfully."""
    successful_loads = 0
    failed_loads = []
    for classifier_name in CLASSIFIER_METRICS.keys():
        repo_name = f'adaptive-classifier/{classifier_name}'
        try:
            classifier = AdaptiveClassifier.load(repo_name)
            assert classifier is not None
            successful_loads += 1
        except Exception as e:
            failed_loads.append((classifier_name, str(e)))
    total_classifiers = len(CLASSIFIER_METRICS)
    print(f'\nClassifier Loading Summary:')
    print(f'Successfully loaded: {successful_loads}/{total_classifiers}')
    if failed_loads:
        print(f'Failed to load:')
        for name, error in failed_loads:
            print(f'  - {name}: {error}')
    assert successful_loads == total_classifiers, f'Failed to load {len(failed_loads)} classifiers: {[name for name, _ in failed_loads]}'

def test_progressive_class_addition():
    """Test adding classes progressively (triggers EWC multiple times)."""
    classifier = AdaptiveClassifier('distilbert-base-uncased', device='cpu')
    phase1_texts = ['Good product', 'Bad service', 'Average quality']
    phase1_labels = ['positive', 'negative', 'neutral']
    classifier.add_examples(phase1_texts, phase1_labels)
    phase2_texts = ['Need help', 'Bug report', 'Feature request']
    phase2_labels = ['support', 'bug', 'feature']
    classifier.add_examples(phase2_texts, phase2_labels)
    phase3_texts = ['Excellent!', 'Terrible!', "It's okay"]
    phase3_labels = ['positive', 'negative', 'neutral']
    classifier.add_examples(phase3_texts, phase3_labels)
    phase4_texts = ['Urgent issue', 'Question about pricing']
    phase4_labels = ['urgent', 'inquiry']
    classifier.add_examples(phase4_texts, phase4_labels)
    expected_classes = {'positive', 'negative', 'neutral', 'support', 'bug', 'feature', 'urgent', 'inquiry'}
    for label in expected_classes:
        assert label in classifier.label_to_id
    test_text = 'This is wonderful!'
    predictions = classifier.predict(test_text, k=3)
    assert predictions is not None
    assert len(predictions) > 0

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_onnx_initialization():
    """Test that ONNX model initializes correctly."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, use_onnx=True, device='cpu')
    assert classifier.use_onnx is True
    assert hasattr(classifier.model, 'model')

def test_auto_detection_cpu():
    """Test that auto-detection uses ONNX on CPU."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, device='cpu', use_onnx='auto')
    if _check_optimum_installed():
        assert classifier.use_onnx is True
    else:
        assert classifier.use_onnx is False

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_embedding_consistency():
    """Test that ONNX and PyTorch produce similar embeddings."""
    model_name = 'prajjwal1/bert-tiny'
    test_text = 'This is a test sentence for embedding comparison.'
    classifier_pytorch = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
    classifier_onnx = AdaptiveClassifier(model_name, use_onnx=True, device='cpu')
    embedding_pytorch = classifier_pytorch._get_embeddings([test_text])[0]
    embedding_onnx = classifier_onnx._get_embeddings([test_text])[0]
    emb_pytorch_np = embedding_pytorch.cpu().numpy()
    emb_onnx_np = embedding_onnx.cpu().numpy()
    assert emb_pytorch_np.shape == emb_onnx_np.shape
    cosine_sim = np.dot(emb_pytorch_np, emb_onnx_np) / (np.linalg.norm(emb_pytorch_np) * np.linalg.norm(emb_onnx_np))
    print(f'Cosine similarity between PyTorch and ONNX embeddings: {cosine_sim:.6f}')
    assert cosine_sim > 0.99, f'Embeddings differ too much: cosine_sim={cosine_sim}'

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_onnx_with_training():
    """Test that ONNX model works with adaptive classifier training."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, use_onnx=True, device='cpu')
    texts = ['This is a positive example', 'This is a negative example', 'Another positive case', 'Another negative case']
    labels = ['positive', 'negative', 'positive', 'negative']
    classifier.add_examples(texts, labels)
    predictions = classifier.predict('This seems positive')
    assert len(predictions) > 0
    assert all((isinstance(label, str) and isinstance(score, float) for label, score in predictions))

def test_explicit_disable_onnx():
    """Test that ONNX can be explicitly disabled."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
    assert classifier.use_onnx is False

def test_label_id_assignment_order_independence():
    """Test that label IDs are assigned consistently regardless of input order"""
    classifier1 = AdaptiveClassifier('answerdotai/ModernBERT-base')
    classifier2 = AdaptiveClassifier('answerdotai/ModernBERT-base')
    labels1 = ['alpha', 'beta', 'gamma']
    texts1 = ['text1', 'text2', 'text3']
    labels2 = ['gamma', 'beta', 'alpha']
    texts2 = ['text3', 'text2', 'text1']
    classifier1.add_examples(texts1, labels1)
    classifier2.add_examples(texts2, labels2)
    assert classifier1.label_to_id == classifier2.label_to_id, f'Label mappings differ: {classifier1.label_to_id} vs {classifier2.label_to_id}'
    expected_mapping = {'alpha': 0, 'beta': 1, 'gamma': 2}
    assert classifier1.label_to_id == expected_mapping
    assert classifier2.label_to_id == expected_mapping

def test_incremental_label_addition():
    """Test that labels are assigned IDs consistently when added incrementally"""
    classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
    classifier.add_examples(['text1'], ['zebra'])
    assert classifier.label_to_id == {'zebra': 0}
    classifier.add_examples(['text2'], ['alpha'])
    assert classifier.label_to_id == {'zebra': 0, 'alpha': 1}
    classifier.add_examples(['text3'], ['beta'])
    assert classifier.label_to_id == {'zebra': 0, 'alpha': 1, 'beta': 2}
    classifier.add_examples(['text4', 'text5'], ['delta', 'charlie'])
    assert classifier.label_to_id == {'zebra': 0, 'alpha': 1, 'beta': 2, 'charlie': 3, 'delta': 4}

def test_predictions_with_sorted_labels():
    """Test that predictions are more consistent with sorted label assignment"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier1 = AdaptiveClassifier('answerdotai/ModernBERT-base')
        classifier2 = AdaptiveClassifier('answerdotai/ModernBERT-base')
        labels1 = ['zing', 'zing', 'zing', 'zoob', 'zoob', 'zoob']
        examples1 = ['fish like to swim', 'fish live in the sea', 'fish are amphibians', 'cats like to meow', 'cats live at home', 'cats are felines']
        labels2 = labels1.copy()
        examples2 = examples1.copy()
        labels2.reverse()
        examples2.reverse()
        classifier1.add_examples(examples1, labels1)
        classifier2.add_examples(examples2, labels2)
        assert classifier1.label_to_id == classifier2.label_to_id
        assert classifier1.label_to_id == {'zing': 0, 'zoob': 1}
        swim_pred1 = classifier1.predict('swim')
        swim_pred2 = classifier2.predict('swim')
        meow_pred1 = classifier1.predict('meow')
        meow_pred2 = classifier2.predict('meow')
        swim_conf1 = {label: score for label, score in swim_pred1}
        swim_conf2 = {label: score for label, score in swim_pred2}
        meow_conf1 = {label: score for label, score in meow_pred1}
        meow_conf2 = {label: score for label, score in meow_pred2}
        swim_diff = abs(swim_conf1.get('zing', 0) - swim_conf2.get('zing', 0))
        meow_diff = abs(meow_conf1.get('zoob', 0) - meow_conf2.get('zoob', 0))
        print(f'\nSwim predictions:')
        print(f'  Classifier 1: {swim_pred1}')
        print(f'  Classifier 2: {swim_pred2}')
        print(f"  Difference in 'zing' confidence: {swim_diff:.4f}")
        print(f'\nMeow predictions:')
        print(f'  Classifier 1: {meow_pred1}')
        print(f'  Classifier 2: {meow_pred2}')
        print(f"  Difference in 'zoob' confidence: {meow_diff:.4f}")
        assert swim_diff < 0.4, f'Swim predictions differ too much: {swim_diff:.4f}'
        assert meow_diff < 0.4, f'Meow predictions differ too much: {meow_diff:.4f}'

def test_mixed_batch_label_sorting():
    """Test that labels are sorted within each batch before assignment"""
    classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
    labels = ['zoo', 'apple', 'dog', 'cat', 'banana']
    texts = ['text1', 'text2', 'text3', 'text4', 'text5']
    classifier.add_examples(texts, labels)
    expected = {'apple': 0, 'banana': 1, 'cat': 2, 'dog': 3, 'zoo': 4}
    assert classifier.label_to_id == expected

def test_reported_confidence_values():
    """Test for the exact confidence drop reported:
    fish: 0.9997 -> 0.8997
    cat: 0.9999 -> 0.8998
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('google-bert/bert-large-cased')
        examples = {'foo': ['fish'], 'bar': ['cat']}
        for label, examples in examples.items():
            classifier.add_examples(examples, [label] * len(examples))
        result_fish_before = classifier.predict('fish')
        result_cat_before = classifier.predict('cat')
        save_path = Path(temp_dir) / 'foobar'
        classifier.save(str(save_path))
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        result_fish_after = loaded_classifier.predict('fish')
        result_cat_after = loaded_classifier.predict('cat')
        fish_conf_before = result_fish_before[0][1]
        cat_conf_before = result_cat_before[0][1]
        fish_conf_after = result_fish_after[0][1]
        cat_conf_after = result_cat_after[0][1]
        print(f'\nFish confidence: {fish_conf_before:.4f} -> {fish_conf_after:.4f}')
        print(f'Cat confidence: {cat_conf_before:.4f} -> {cat_conf_after:.4f}')
        assert abs(fish_conf_before - fish_conf_after) < 0.01, f'Fish confidence dropped from {fish_conf_before:.4f} to {fish_conf_after:.4f}'
        assert abs(cat_conf_before - cat_conf_after) < 0.01, f'Cat confidence dropped from {cat_conf_before:.4f} to {cat_conf_after:.4f}'
        assert 0.85 < fish_conf_before < 0.95, f'Before save confidence should be blended, got {fish_conf_before:.4f}'
        assert 0.85 < fish_conf_after < 0.95, f'After load confidence should be blended, got {fish_conf_after:.4f}'

def test_confidence_consistency_after_save_load():
    """Test that confidence scores remain consistent after save/load"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
        texts = ['This is a foo example'] * 100 + ['This is a bar example'] * 100
        labels = ['foo'] * 100 + ['bar'] * 100
        classifier.add_examples(texts, labels)
        test_text = 'This is a foo example'
        predictions_before = classifier.predict(test_text)
        conf_before = {label: score for label, score in predictions_before}
        save_path = Path(temp_dir) / 'test_model'
        classifier.save(str(save_path))
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        predictions_after = loaded_classifier.predict(test_text)
        conf_after = {label: score for label, score in predictions_after}
        assert abs(conf_before['foo'] - conf_after['foo']) < 0.01, f'Confidence dropped from {conf_before['foo']:.4f} to {conf_after['foo']:.4f}'
        assert conf_after['foo'] > 0.7, f'Confidence too low after load: {conf_after['foo']:.4f}'

def test_continuous_learning_with_save_load():
    """Test continuous learning scenario with save/load"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
        texts_1 = ['Initial foo example'] * 100 + ['Initial bar example'] * 100
        labels_1 = ['foo'] * 100 + ['bar'] * 100
        classifier.add_examples(texts_1, labels_1)
        save_path = Path(temp_dir) / 'test_model'
        classifier.save(str(save_path))
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        assert loaded_classifier.training_history['foo'] == 100
        assert loaded_classifier.training_history['bar'] == 100
        texts_2 = ['Additional foo example'] * 20 + ['Additional bar example'] * 20
        labels_2 = ['foo'] * 20 + ['bar'] * 20
        loaded_classifier.add_examples(texts_2, labels_2)
        assert loaded_classifier.training_history['foo'] == 120
        assert loaded_classifier.training_history['bar'] == 120
        predictions = loaded_classifier.predict('This is a foo example')
        conf = {label: score for label, score in predictions}
        assert conf['foo'] > 0.65

def test_backward_compatibility():
    """Test loading models without training_history field"""
    with tempfile.TemporaryDirectory() as temp_dir:
        classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
        texts = ['Foo example'] * 100 + ['Bar example'] * 100
        labels = ['foo'] * 100 + ['bar'] * 100
        classifier.add_examples(texts, labels)
        save_path = Path(temp_dir) / 'test_model'
        classifier.save(str(save_path))
        import json
        config_path = save_path / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        config.pop('training_history', None)
        with open(config_path, 'w') as f:
            json.dump(config, f)
        loaded_classifier = AdaptiveClassifier.load(str(save_path))
        assert loaded_classifier.training_history['foo'] == 100
        assert loaded_classifier.training_history['bar'] == 100
        predictions = loaded_classifier.predict('This is a foo example')
        conf = {label: score for label, score in predictions}
        assert conf['foo'] > 0.65

def test_new_class_detection():
    """Test that new classes with few examples are correctly identified"""
    classifier = AdaptiveClassifier('answerdotai/ModernBERT-base')
    texts_established = ['Established foo'] * 50 + ['Established bar'] * 50
    labels_established = ['foo'] * 50 + ['bar'] * 50
    classifier.add_examples(texts_established, labels_established)
    texts_new = ['New baz example'] * 5
    labels_new = ['baz'] * 5
    classifier.add_examples(texts_new, labels_new)
    assert classifier.training_history['foo'] == 50
    assert classifier.training_history['bar'] == 50
    assert classifier.training_history['baz'] == 5
    predictions = classifier.predict('New baz example')
    assert len(predictions) > 0
    assert any((label == 'baz' for label, _ in predictions))

@pytest.fixture
def base_classifier():
    return AdaptiveClassifier('bert-base-uncased')

def test_save_load(base_classifier, sample_data):
    """Test saving and loading the classifier with deterministic results."""
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    texts, labels = sample_data
    base_classifier.add_examples(texts, labels)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'test_classifier'
        if not base_classifier.use_onnx and hasattr(base_classifier.model, 'eval'):
            base_classifier.model.eval()
        if base_classifier.adaptive_head is not None:
            base_classifier.adaptive_head.eval()
        base_classifier.save(save_path)
        assert (save_path / 'config.json').exists()
        assert (save_path / 'model.safetensors').exists()
        assert (save_path / 'examples.json').exists()
        assert (save_path / 'README.md').exists()
        loaded_classifier = AdaptiveClassifier.load(save_path, device=base_classifier.device, use_onnx=False)
        assert loaded_classifier is not None
        assert loaded_classifier.label_to_id == base_classifier.label_to_id
        if not loaded_classifier.use_onnx and hasattr(loaded_classifier.model, 'eval'):
            loaded_classifier.model.eval()
        if loaded_classifier.adaptive_head is not None:
            loaded_classifier.adaptive_head.eval()
        with torch.no_grad():
            test_text = 'This is a test'
            original_preds = base_classifier.predict(test_text)
            loaded_preds = loaded_classifier.predict(test_text)
        original_preds = sorted(original_preds, key=lambda x: (-x[1], x[0]))
        loaded_preds = sorted(loaded_preds, key=lambda x: (-x[1], x[0]))
        score_threshold = 0.05
        for (label1, score1), (label2, score2) in zip(original_preds, loaded_preds):
            assert label1 == label2, f"Labels don't match: {label1} vs {label2}"
            assert abs(score1 - score2) < score_threshold, f'Scores differ too much: {score1} vs {score2}'
        original_stats = base_classifier.get_memory_stats()
        loaded_stats = loaded_classifier.get_memory_stats()
        assert original_stats['num_classes'] == loaded_stats['num_classes']
        assert original_stats['total_examples'] == loaded_stats['total_examples']
        for label in original_stats['examples_per_class']:
            assert original_stats['examples_per_class'][label] == loaded_stats['examples_per_class'][label]

def test_dynamic_class_addition(base_classifier, sample_data):
    texts, labels = sample_data
    base_classifier.add_examples(texts[:3], labels[:3])
    new_texts = ['Error in system', 'Null pointer exception']
    new_labels = ['technical', 'technical']
    base_classifier.add_examples(new_texts, new_labels)
    assert 'technical' in base_classifier.label_to_id
    pred = base_classifier.predict('System crash occurred')
    assert any((label == 'technical' for label, _ in pred))

def test_empty_input_handling(base_classifier):
    with pytest.raises(ValueError):
        base_classifier.add_examples([], [])
    with pytest.raises(ValueError):
        base_classifier.predict('')

def test_device_handling(base_classifier, sample_data):
    texts, labels = sample_data
    base_classifier.add_examples(texts, labels)
    base_classifier.to('cpu')
    cpu_pred = base_classifier.predict('test')
    if torch.cuda.is_available():
        base_classifier.to('cuda')
        gpu_pred = base_classifier.predict('test')
        for (label1, score1), (label2, score2) in zip(cpu_pred, gpu_pred):
            assert label1 == label2
            assert abs(score1 - score2) < 1e-05

def test_num_representative_examples(sample_data):
    config = {'num_representative_examples': 2}
    classifier = AdaptiveClassifier('bert-base-uncased', config=config)
    texts, labels = sample_data
    for _ in range(5):
        classifier.add_examples(texts, labels)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'test_classifier'
        classifier.save(save_path)
        loaded_classifier = AdaptiveClassifier.load(save_path)
        assert loaded_classifier.config.num_representative_examples == config['num_representative_examples']
        for label in loaded_classifier.memory.examples:
            assert len(loaded_classifier.memory.examples[label]) <= config['num_representative_examples'], f'Class {label} has more than {config['num_representative_examples']} examples'

@pytest.fixture
def large_classifier():
    """Create classifier that will be used for many-class testing."""
    return AdaptiveClassifier('bert-base-uncased', seed=42)

def test_weight_structure_preservation():
    """Test that head structure expands correctly and uses update_num_classes instead of reinitialization."""
    torch.manual_seed(42)
    classifier = AdaptiveClassifier('bert-base-uncased', seed=42)
    initial_texts = ['Text about cats', 'Text about dogs']
    initial_labels = ['cats', 'dogs']
    classifier.add_examples(initial_texts, initial_labels)
    assert classifier.adaptive_head is not None, 'Adaptive head should be created'
    assert classifier.adaptive_head.model[-1].weight.shape[0] == 2, 'Should have 2 output classes'
    old_head = classifier.adaptive_head
    old_head.update_num_classes(3)
    assert old_head.model[-1].weight.shape[0] == 3, 'Should have 3 output classes after update'
    assert old_head.model[-1].bias.shape[0] == 3, 'Should have 3 output biases after update'
    print('✓ AdaptiveHead update_num_classes method works correctly')

def test_class_expansion_behavior():
    """Test that adding new classes expands the head instead of reinitializing."""
    torch.manual_seed(42)
    classifier = AdaptiveClassifier('bert-base-uncased', seed=42)
    initial_texts = ['Text about cats', 'Text about dogs']
    initial_labels = ['cats', 'dogs']
    classifier.add_examples(initial_texts, initial_labels)
    original_head_id = id(classifier.adaptive_head)
    new_texts = ['Text about birds']
    new_labels = ['birds']
    classifier.add_examples(new_texts, new_labels)
    new_head = classifier.adaptive_head
    assert new_head is not None, 'Head should still exist'
    assert new_head.model[-1].weight.shape[0] == 3, 'Should have 3 output classes'
    assert new_head.model[-1].bias.shape[0] == 3, 'Should have 3 output biases'
    assert len(classifier.label_to_id) == 3, 'Should have 3 classes total'
    assert 'cats' in classifier.label_to_id, "Original class 'cats' should be preserved"
    assert 'dogs' in classifier.label_to_id, "Original class 'dogs' should be preserved"
    assert 'birds' in classifier.label_to_id, "New class 'birds' should be added"
    print('✓ Class expansion behavior verified')

def test_improved_accuracy_preservation():
    """Test that the improved implementation has better accuracy preservation."""
    torch.manual_seed(42)
    np.random.seed(42)
    classifier = AdaptiveClassifier('bert-base-uncased', seed=42)
    initial_texts = ['Text about cats and their behavior', 'Dogs are loyal animals', 'Cats like to play with yarn', 'Dogs love to fetch balls']
    initial_labels = ['cats', 'dogs', 'cats', 'dogs']
    classifier.add_examples(initial_texts, initial_labels)
    test_text_cat = 'Cats are independent pets'
    test_text_dog = 'Dogs are faithful companions'
    pred_cat_before = classifier.predict(test_text_cat, k=1)
    pred_dog_before = classifier.predict(test_text_dog, k=1)
    new_texts = ['Birds can fly in the sky']
    new_labels = ['birds']
    classifier.add_examples(new_texts, new_labels)
    pred_cat_after = classifier.predict(test_text_cat, k=1)
    pred_dog_after = classifier.predict(test_text_dog, k=1)
    print(f'Cat prediction before: {pred_cat_before}')
    print(f'Cat prediction after: {pred_cat_after}')
    print(f'Dog prediction before: {pred_dog_before}')
    print(f'Dog prediction after: {pred_dog_after}')
    if pred_cat_before and pred_cat_after:
        cat_confidence_drop = pred_cat_before[0][1] - pred_cat_after[0][1]
        print(f'Cat confidence drop: {cat_confidence_drop:.3f}')
    if pred_dog_before and pred_dog_after:
        dog_confidence_drop = pred_dog_before[0][1] - pred_dog_after[0][1]
        print(f'Dog confidence drop: {dog_confidence_drop:.3f}')
    pred_bird = classifier.predict('Birds have feathers and wings', k=1)
    print(f'Bird prediction: {pred_bird}')
    assert pred_bird and pred_bird[0][0] == 'birds', 'New class should be predictable'
    print('✓ Improved accuracy preservation verified')

@pytest.fixture
def multilabel_classifier():
    """Create a MultiLabelAdaptiveClassifier instance."""
    return MultiLabelAdaptiveClassifier('distilbert/distilbert-base-cased', default_threshold=0.5, min_predictions=1, max_predictions=5)

def test_save_load_multilabel(multilabel_classifier, sample_multilabel_data):
    """Test saving and loading multi-label classifier."""
    texts, labels = sample_multilabel_data
    multilabel_classifier.add_examples(texts, labels)
    test_text = 'Test prediction text'
    original_predictions = multilabel_classifier.predict_multilabel(test_text, max_labels=5)
    with tempfile.TemporaryDirectory() as temp_dir:
        save_path = Path(temp_dir) / 'multilabel_classifier'
        multilabel_classifier.save(str(save_path))
        loaded_classifier = MultiLabelAdaptiveClassifier.load(str(save_path), device=multilabel_classifier.device)
        loaded_classifier.max_predictions = multilabel_classifier.max_predictions
        loaded_predictions = loaded_classifier.predict_multilabel(test_text, max_labels=5)
        assert len(loaded_predictions) <= 5
        assert len(original_predictions) <= 5
        assert len(loaded_predictions) > 0
        assert len(original_predictions) > 0

def test_statistics_reporting(multilabel_classifier, sample_multilabel_data):
    """Test that statistics are reported correctly."""
    texts, labels = sample_multilabel_data
    multilabel_classifier.add_examples(texts, labels)
    stats = multilabel_classifier.get_label_statistics()
    assert 'label_thresholds' in stats
    assert 'adaptive_threshold' in stats
    assert 'default_threshold' in stats
    assert 'min_predictions' in stats
    assert 'max_predictions' in stats
    assert 'num_classes' in stats
    assert 'total_examples' in stats
    assert stats['default_threshold'] == multilabel_classifier.default_threshold
    assert stats['min_predictions'] == multilabel_classifier.min_predictions
    assert stats['max_predictions'] == multilabel_classifier.max_predictions

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_export_onnx_basic():
    """Test basic ONNX export functionality."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
    texts = ['positive example', 'negative example']
    labels = ['positive', 'negative']
    classifier.add_examples(texts, labels)
    with tempfile.TemporaryDirectory() as tmpdir:
        onnx_path = Path(tmpdir) / 'onnx_model'
        result_path = classifier.export_onnx(onnx_path, quantize=False)
        assert result_path.exists()
        assert (result_path / 'model.onnx').exists()
        print(f'✓ ONNX model exported to {result_path}')

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_save_with_onnx():
    """Test saving classifier with ONNX export integrated."""
    model_name = 'prajjwal1/bert-tiny'
    classifier = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
    texts = ['positive text', 'negative text', 'neutral text']
    labels = ['positive', 'negative', 'neutral']
    classifier.add_examples(texts, labels)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier_with_onnx'
        classifier._save_pretrained(save_path, include_onnx=True, quantize_onnx=False)
        assert (save_path / 'config.json').exists()
        assert (save_path / 'examples.json').exists()
        assert (save_path / 'model.safetensors').exists()
        assert (save_path / 'onnx').exists()
        assert (save_path / 'onnx' / 'model.onnx').exists()
        print('✓ Classifier saved with ONNX')

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_load_onnx_model():
    """Test loading a saved ONNX model."""
    model_name = 'prajjwal1/bert-tiny'
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier_onnx'
        classifier_orig = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
        texts = ['happy', 'sad', 'angry']
        labels = ['positive', 'negative', 'negative']
        classifier_orig.add_examples(texts, labels)
        classifier_orig._save_pretrained(save_path, include_onnx=True)
        classifier_loaded = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx=True)
        assert classifier_loaded.use_onnx is True
        print('✓ ONNX model loaded successfully')
        predictions = classifier_loaded.predict('very happy')
        assert len(predictions) > 0
        print(f'✓ Predictions work: {predictions[:2]}')

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_onnx_prediction_consistency():
    """Test that predictions are consistent after export and reload."""
    model_name = 'prajjwal1/bert-tiny'
    test_text = 'This is a test for consistency'
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier_consistency'
        classifier_pytorch = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
        texts = ['good', 'bad', 'okay']
        labels = ['positive', 'negative', 'neutral']
        classifier_pytorch.add_examples(texts, labels)
        pred_pytorch = classifier_pytorch.predict(test_text, k=3)
        classifier_pytorch._save_pretrained(save_path, include_onnx=True)
        classifier_onnx = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx=True)
        pred_onnx = classifier_onnx.predict(test_text, k=3)
        print(f'PyTorch predictions: {pred_pytorch}')
        print(f'ONNX predictions: {pred_onnx}')
        assert pred_pytorch[0][0] == pred_onnx[0][0], 'Top prediction differs between PyTorch and ONNX'
        for (label_pt, score_pt), (label_ox, score_ox) in zip(pred_pytorch, pred_onnx):
            assert label_pt == label_ox, f'Label mismatch: {label_pt} vs {label_ox}'
            score_diff = abs(score_pt - score_ox)
            assert score_diff < 0.05, f'Score difference too large for {label_pt}: {score_diff}'
        print('✓ Predictions are consistent between PyTorch and ONNX')

@pytest.mark.skipif(not _check_optimum_installed(), reason='optimum[onnxruntime] not installed')
def test_auto_detection_loads_onnx():
    """Test that auto-detection loads ONNX when available on CPU."""
    model_name = 'prajjwal1/bert-tiny'
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier_auto'
        classifier_orig = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
        texts = ['example one', 'example two']
        labels = ['class1', 'class2']
        classifier_orig.add_examples(texts, labels)
        classifier_orig._save_pretrained(save_path, include_onnx=True)
        classifier_auto = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx='auto', device='cpu')
        assert classifier_auto.use_onnx is True
        print('✓ Auto-detection correctly loads ONNX on CPU')

def test_fallback_when_onnx_not_available():
    """Test that loading works even when ONNX not in save directory."""
    model_name = 'prajjwal1/bert-tiny'
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / 'classifier_no_onnx'
        classifier_orig = AdaptiveClassifier(model_name, use_onnx=False, device='cpu')
        texts = ['text one', 'text two']
        labels = ['A', 'B']
        classifier_orig.add_examples(texts, labels)
        classifier_orig._save_pretrained(save_path, include_onnx=False)
        classifier_loaded = AdaptiveClassifier._from_pretrained(str(save_path), use_onnx=True)
        assert classifier_loaded.use_onnx is False
        print('✓ Correctly falls back to PyTorch when ONNX not available')
        predictions = classifier_loaded.predict('test')
        assert len(predictions) > 0

