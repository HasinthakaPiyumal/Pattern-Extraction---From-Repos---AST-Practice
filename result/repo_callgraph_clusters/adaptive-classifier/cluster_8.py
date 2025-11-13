# Cluster 8

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

class MultiLabelAdaptiveClassifier(AdaptiveClassifier):
    """
    Multi-label extension of AdaptiveClassifier that can predict multiple labels per input.

    Handles the "No labels met the threshold criteria" issue by implementing:
    1. Adaptive thresholds based on number of labels
    2. Minimum predictions per sample
    3. Label-specific threshold adjustments
    """

    def __init__(self, model_name: str, device: Optional[str]=None, config: Optional[Dict[str, Any]]=None, seed: int=42, default_threshold: float=0.5, min_predictions: int=1, max_predictions: Optional[int]=None):
        super().__init__(model_name, device, config, seed)
        self.default_threshold = default_threshold
        self.min_predictions = min_predictions
        self.max_predictions = max_predictions
        self.label_thresholds = {}
        self.adaptive_head = None

    def _initialize_adaptive_head(self):
        """Initialize multi-label adaptive head."""
        num_classes = len(self.label_to_id)
        hidden_dims = [self.embedding_dim, self.embedding_dim // 2]
        self.adaptive_head = MultiLabelAdaptiveHead(self.embedding_dim, num_classes, hidden_dims=hidden_dims).to(self.device)

    def _get_adaptive_threshold(self, num_labels: int) -> float:
        """
        Calculate adaptive threshold based on number of labels.

        With more labels, individual prediction scores tend to be lower,
        so we need a lower threshold to avoid "No labels met the threshold criteria".
        """
        if num_labels <= 2:
            return self.default_threshold
        elif num_labels <= 5:
            return self.default_threshold * 0.8
        elif num_labels <= 10:
            return self.default_threshold * 0.6
        elif num_labels <= 20:
            return self.default_threshold * 0.4
        else:
            return self.default_threshold * 0.2

    def predict_multilabel(self, text: str, threshold: Optional[float]=None, max_labels: Optional[int]=None) -> List[Tuple[str, float]]:
        """
        Predict multiple labels for input text.

        Args:
            text: Input text to classify
            threshold: Confidence threshold for predictions (adaptive if None)
            max_labels: Maximum number of labels to return

        Returns:
            List of (label, confidence) tuples for labels above threshold
        """
        if not text:
            raise ValueError('Empty input text')
        num_labels = len(self.label_to_id)
        if num_labels == 0:
            return []
        if threshold is None:
            threshold = self._get_adaptive_threshold(num_labels)
        max_labels = max_labels or self.max_predictions
        with torch.no_grad():
            embedding = self._get_embeddings([text])[0]
            if self.adaptive_head is not None:
                self.adaptive_head.eval()
                input_embedding = embedding.unsqueeze(0).to(self.device)
                probabilities = self.adaptive_head(input_embedding).squeeze(0)
                predictions = []
                for i, prob in enumerate(probabilities):
                    if i < len(self.id_to_label):
                        label = self.id_to_label[i]
                        label_threshold = self.label_thresholds.get(label, threshold)
                        if prob.item() >= label_threshold:
                            predictions.append((label, prob.item()))
                predictions.sort(key=lambda x: x[1], reverse=True)
                if max_labels and len(predictions) > max_labels:
                    predictions = predictions[:max_labels]
            else:
                proto_predictions = self.memory.get_nearest_prototypes(embedding, k=min(num_labels, max_labels) if max_labels else num_labels)
                predictions = [(label, score) for label, score in proto_predictions if score >= threshold]
        if len(predictions) < self.min_predictions and self.adaptive_head is not None:
            with torch.no_grad():
                input_embedding = embedding.unsqueeze(0).to(self.device)
                probabilities = self.adaptive_head(input_embedding).squeeze(0)
                values, indices = torch.topk(probabilities, min(self.min_predictions, len(self.id_to_label)))
                additional_predictions = []
                for val, idx in zip(values, indices):
                    if idx.item() < len(self.id_to_label):
                        label = self.id_to_label[idx.item()]
                        score = val.item()
                        if not any((pred[0] == label for pred in predictions)):
                            additional_predictions.append((label, score))
                predictions.extend(additional_predictions[:self.min_predictions - len(predictions)])
                predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions

    def predict(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """
        Override base predict to use multi-label prediction.
        Falls back to single-label prediction if needed.
        """
        multilabel_preds = self.predict_multilabel(text, max_labels=k)
        if multilabel_preds:
            return multilabel_preds[:k]
        else:
            return super().predict(text, k)

    def add_examples(self, texts: List[str], labels: List[List[str]]):
        """
        Add multi-label training examples.

        Args:
            texts: List of input texts
            labels: List of label lists (each text can have multiple labels)
        """
        if not texts or not labels:
            raise ValueError('Empty input lists')
        if len(texts) != len(labels):
            raise ValueError('Mismatched text and label lists')
        flattened_texts = []
        flattened_labels = []
        for text, text_labels in zip(texts, labels):
            if not text_labels:
                continue
            for label in text_labels:
                flattened_texts.append(text)
                flattened_labels.append(label)
        if flattened_texts:
            super().add_examples(flattened_texts, flattened_labels)
        self._update_label_thresholds()

    def _update_label_thresholds(self):
        """Update per-label thresholds based on training data distribution."""
        if not self.memory.examples:
            return
        label_counts = defaultdict(int)
        total_examples = 0
        for label, examples in self.memory.examples.items():
            label_counts[label] = len(examples)
            total_examples += len(examples)
        for label, count in label_counts.items():
            frequency = count / total_examples
            if frequency < 0.05:
                self.label_thresholds[label] = self.default_threshold * 0.3
            elif frequency < 0.1:
                self.label_thresholds[label] = self.default_threshold * 0.5
            elif frequency > 0.3:
                self.label_thresholds[label] = self.default_threshold * 1.2
            else:
                self.label_thresholds[label] = self.default_threshold
        logger.debug(f'Updated label thresholds: {self.label_thresholds}')

    def _train_adaptive_head(self, epochs: int=10):
        """Train multi-label adaptive head with BCE loss."""
        if not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        num_classes = len(self.label_to_id)
        text_to_labels = defaultdict(set)
        for label, examples in self.memory.examples.items():
            for example in examples:
                text_to_labels[example.text].add(label)
        for text, labels in text_to_labels.items():
            embedding = None
            for label in labels:
                for example in self.memory.examples[label]:
                    if example.text == text:
                        embedding = example.embedding
                        break
                if embedding is not None:
                    break
            if embedding is not None:
                all_embeddings.append(embedding)
                label_vector = torch.zeros(num_classes)
                for label in labels:
                    if label in self.label_to_id:
                        label_vector[self.label_to_id[label]] = 1.0
                all_labels.append(label_vector)
        if not all_embeddings:
            return
        all_embeddings = torch.stack(all_embeddings)
        all_labels = torch.stack(all_labels)
        all_embeddings = F.normalize(all_embeddings, p=2, dim=1)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=min(32, len(all_embeddings)), shuffle=True, generator=torch.Generator().manual_seed(42))
        self.adaptive_head.train()
        criterion = nn.BCELoss()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=0.001, weight_decay=0.01)
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
                loss = criterion(outputs, batch_labels)
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

    def get_label_statistics(self) -> Dict[str, Any]:
        """Get statistics about label distribution and thresholds."""
        stats = super().get_example_statistics()
        stats['label_thresholds'] = dict(self.label_thresholds)
        stats['adaptive_threshold'] = self._get_adaptive_threshold(len(self.label_to_id))
        stats['default_threshold'] = self.default_threshold
        stats['min_predictions'] = self.min_predictions
        stats['max_predictions'] = self.max_predictions
        return stats

def _update_label_thresholds(self):
    """Update per-label thresholds based on training data distribution."""
    if not self.memory.examples:
        return
    label_counts = defaultdict(int)
    total_examples = 0
    for label, examples in self.memory.examples.items():
        label_counts[label] = len(examples)
        total_examples += len(examples)
    for label, count in label_counts.items():
        frequency = count / total_examples
        if frequency < 0.05:
            self.label_thresholds[label] = self.default_threshold * 0.3
        elif frequency < 0.1:
            self.label_thresholds[label] = self.default_threshold * 0.5
        elif frequency > 0.3:
            self.label_thresholds[label] = self.default_threshold * 1.2
        else:
            self.label_thresholds[label] = self.default_threshold
    logger.debug(f'Updated label thresholds: {self.label_thresholds}')

@dataclass
class Example:
    """Represents a single training example."""
    text: str
    label: str
    embedding: Optional[torch.Tensor] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert example to dictionary for saving."""
        return {'text': self.text, 'label': self.label, 'embedding': self.embedding.tolist() if self.embedding is not None else None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Example':
        """Create example from dictionary."""
        embedding = torch.tensor(data['embedding']) if data['embedding'] is not None else None
        return cls(text=data['text'], label=data['label'], embedding=embedding)

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Example':
    """Create example from dictionary."""
    embedding = torch.tensor(data['embedding']) if data['embedding'] is not None else None
    return cls(text=data['text'], label=data['label'], embedding=embedding)

class ModelConfig:
    """Configuration for the adaptive classifier."""

    def __init__(self, config: Optional[Dict[str, Any]]=None):
        """Initialize model configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_length = self.config.get('max_length', 512)
        self.batch_size = self.config.get('batch_size', 32)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.warmup_steps = self.config.get('warmup_steps', 0)
        self.max_examples_per_class = self.config.get('max_examples_per_class', 1000)
        self.prototype_update_frequency = self.config.get('prototype_update_frequency', 100)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.6)
        self.ewc_lambda = self.config.get('ewc_lambda', 100.0)
        self.num_representative_examples = self.config.get('num_representative_examples', 5)
        self.epochs = self.config.get('epochs', 10)
        self.early_stopping_patience = self.config.get('early_stopping_patience', 3)
        self.min_examples_per_class = self.config.get('min_examples_per_class', 3)
        self.prototype_weight = self.config.get('prototype_weight', 0.7)
        self.neural_weight = self.config.get('neural_weight', 0.3)
        self.min_confidence = self.config.get('min_confidence', 0.1)
        self.device_map = self.config.get('device_map', 'auto')
        self.quantization = self.config.get('quantization', None)
        self.gradient_checkpointing = self.config.get('gradient_checkpointing', False)
        self.enable_strategic_mode = self.config.get('enable_strategic_mode', False)
        self.cost_function_type = self.config.get('cost_function_type', 'separable')
        self.strategic_lambda = self.config.get('strategic_lambda', 0.1)
        self.cost_coefficients = self.config.get('cost_coefficients', {})
        self.strategic_training_frequency = self.config.get('strategic_training_frequency', 10)
        self.strategic_blend_regular_weight = self.config.get('strategic_blend_regular_weight', 0.6)
        self.strategic_blend_strategic_weight = self.config.get('strategic_blend_strategic_weight', 0.4)
        self.strategic_robust_proto_weight = self.config.get('strategic_robust_proto_weight', 0.8)
        self.strategic_robust_head_weight = self.config.get('strategic_robust_head_weight', 0.2)
        self.strategic_prediction_proto_weight = self.config.get('strategic_prediction_proto_weight', 0.5)
        self.strategic_prediction_head_weight = self.config.get('strategic_prediction_head_weight', 0.5)

    def update(self, **kwargs):
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f'Unknown configuration parameter: {key}')

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {'max_length': self.max_length, 'batch_size': self.batch_size, 'learning_rate': self.learning_rate, 'warmup_steps': self.warmup_steps, 'max_examples_per_class': self.max_examples_per_class, 'prototype_update_frequency': self.prototype_update_frequency, 'similarity_threshold': self.similarity_threshold, 'ewc_lambda': self.ewc_lambda, 'num_representative_examples': self.num_representative_examples, 'epochs': self.epochs, 'early_stopping_patience': self.early_stopping_patience, 'min_examples_per_class': self.min_examples_per_class, 'prototype_weight': self.prototype_weight, 'neural_weight': self.neural_weight, 'min_confidence': self.min_confidence, 'device_map': self.device_map, 'quantization': self.quantization, 'gradient_checkpointing': self.gradient_checkpointing, 'enable_strategic_mode': self.enable_strategic_mode, 'cost_function_type': self.cost_function_type, 'strategic_lambda': self.strategic_lambda, 'cost_coefficients': self.cost_coefficients, 'strategic_training_frequency': self.strategic_training_frequency, 'strategic_blend_regular_weight': self.strategic_blend_regular_weight, 'strategic_blend_strategic_weight': self.strategic_blend_strategic_weight, 'strategic_robust_proto_weight': self.strategic_robust_proto_weight, 'strategic_robust_head_weight': self.strategic_robust_head_weight, 'strategic_prediction_proto_weight': self.strategic_prediction_proto_weight, 'strategic_prediction_head_weight': self.strategic_prediction_head_weight}

def update(self, **kwargs):
    """Update configuration parameters."""
    for key, value in kwargs.items():
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            logger.warning(f'Unknown configuration parameter: {key}')

class PrototypeMemory:
    """Memory system that maintains prototypes for each class."""

    def __init__(self, embedding_dim: int, config: Optional[ModelConfig]=None):
        """Initialize the prototype memory system.
        
        Args:
            embedding_dim: Dimension of the embeddings
            config: Optional model configuration
        """
        self.embedding_dim = embedding_dim
        self.config = config or ModelConfig()
        self.examples = defaultdict(list)
        self.prototypes = {}
        self.strategic_prototypes = {}
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.label_to_index = {}
        self.index_to_label = {}
        self.updates_since_rebuild = 0

    def add_example(self, example: Example, label: str):
        """Add a new example to memory.
        
        Args:
            example: Example to add
            label: Class label
            
        Raises:
            ValueError: If example embedding dimension doesn't match memory dimension
        """
        if example.embedding is None:
            raise ValueError('Example must have an embedding')
        if example.embedding.size(-1) != self.embedding_dim:
            raise ValueError(f'Example embedding dimension {example.embedding.size(-1)} does not match memory dimension {self.embedding_dim}')
        self.examples[label].append(example)
        if len(self.examples[label]) > self.config.max_examples_per_class:
            self._prune_examples(label)
        self._update_prototype(label)
        if not getattr(self, 'just_rebuilt', False):
            self.updates_since_rebuild += 1
        if self.updates_since_rebuild >= self.config.prototype_update_frequency:
            self._rebuild_index()
            self.just_rebuilt = True
        else:
            self.just_rebuilt = False

    def get_nearest_prototypes(self, query_embedding: torch.Tensor, k: int=5, min_similarity: Optional[float]=None) -> List[Tuple[str, float]]:
        """Find the nearest prototype neighbors for a query.
            
            Args:
                query_embedding: Query embedding tensor
                k: Number of neighbors to return
                min_similarity: Optional minimum similarity threshold
                
            Returns:
                List of (label, similarity) tuples
            """
        if self.updates_since_rebuild >= self.config.prototype_update_frequency:
            self._rebuild_index()
        if self.index.ntotal == 0:
            return []
        query_np = query_embedding.unsqueeze(0).numpy()
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_np, k)
        similarities = np.exp(-distances[0])
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx >= 0:
                label = self.index_to_label[int(idx)]
                score = float(similarity)
                results.append((label, score))
        if results:
            scores = torch.tensor([score for _, score in results])
            normalized_scores = torch.nn.functional.softmax(scores, dim=0)
            results = [(label, float(score)) for (label, _), score in zip(results, normalized_scores)]
        return results

    def _update_prototype(self, label: str):
        """Update the prototype for a given label.
        
        Args:
            label: Class label to update
        """
        examples = self.examples[label]
        if not examples:
            return
        embeddings = torch.stack([ex.embedding for ex in examples])
        prototype = torch.mean(embeddings, dim=0)
        self.prototypes[label] = prototype
        if label in self.label_to_index:
            idx = self.label_to_index[label]
            self.index.remove_ids(torch.tensor([idx]))
            self.index.add(prototype.unsqueeze(0).numpy())

    def _rebuild_index(self):
        """Rebuild the FAISS index from scratch."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.label_to_index.clear()
        self.index_to_label.clear()
        sorted_labels = sorted(self.prototypes.keys())
        for i, label in enumerate(sorted_labels):
            prototype = self.prototypes[label]
            self.index.add(prototype.unsqueeze(0).numpy())
            self.label_to_index[label] = i
            self.index_to_label[i] = label
        self.updates_since_rebuild = 0

    def _restore_from_save(self):
        """Restore index and mappings after loading from save."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.label_to_index.clear()
        self.index_to_label.clear()
        sorted_labels = sorted(self.prototypes.keys())
        for i, label in enumerate(sorted_labels):
            prototype = self.prototypes[label]
            self.index.add(prototype.unsqueeze(0).numpy())
            self.label_to_index[label] = i
            self.index_to_label[i] = label
        self.updates_since_rebuild = 0

    def _prune_examples(self, label: str):
        """Prune examples for a given label to maintain memory bounds."""
        examples = self.examples[label]
        if not examples:
            return
        embeddings = torch.stack([ex.embedding for ex in examples])
        mean_embedding = torch.mean(embeddings, dim=0)
        distances = []
        for ex in examples:
            dist = torch.norm(ex.embedding - mean_embedding).item()
            distances.append(dist)
        sorted_indices = np.argsort(distances)
        keep_indices = sorted_indices[:self.config.max_examples_per_class]
        self.examples[label] = [examples[i] for i in keep_indices]
        assert len(self.examples[label]) <= self.config.max_examples_per_class

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary of memory statistics
        """
        return {'num_classes': len(self.prototypes), 'examples_per_class': {label: len(examples) for label, examples in self.examples.items()}, 'total_examples': sum((len(examples) for examples in self.examples.values())), 'prototype_dimensions': self.embedding_dim, 'updates_since_rebuild': self.updates_since_rebuild}

    def clear(self):
        """Clear all memory."""
        self.examples.clear()
        self.prototypes.clear()
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.label_to_index.clear()
        self.index_to_label.clear()
        self.updates_since_rebuild = 0

    def compute_strategic_prototypes(self, cost_function, classifier_func):
        """Compute strategic prototypes for all classes.
        
        Args:
            cost_function: Strategic cost function
            classifier_func: Current classifier function
        """
        for label, examples in self.examples.items():
            if examples:
                strategic_embeddings = []
                for example in examples:
                    strategic_embedding = cost_function.compute_best_response(example.embedding, classifier_func)
                    strategic_embeddings.append(strategic_embedding)
                if strategic_embeddings:
                    strategic_prototype = torch.stack(strategic_embeddings).mean(dim=0)
                    self.strategic_prototypes[label] = strategic_prototype

    def get_strategic_prototypes(self, query_embedding: torch.Tensor, k: int=5) -> List[Tuple[str, float]]:
        """Get nearest strategic prototypes.
        
        Args:
            query_embedding: Query embedding tensor
            k: Number of neighbors to return
            
        Returns:
            List of (label, similarity) tuples
        """
        if not self.strategic_prototypes:
            return self.get_nearest_prototypes(query_embedding, k)
        similarities = []
        for label, prototype in self.strategic_prototypes.items():
            sim = F.cosine_similarity(query_embedding.unsqueeze(0), prototype.unsqueeze(0)).item()
            similarities.append((label, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

def __init__(self, embedding_dim: int, config: Optional[ModelConfig]=None):
    """Initialize the prototype memory system.
        
        Args:
            embedding_dim: Dimension of the embeddings
            config: Optional model configuration
        """
    self.embedding_dim = embedding_dim
    self.config = config or ModelConfig()
    self.examples = defaultdict(list)
    self.prototypes = {}
    self.strategic_prototypes = {}
    self.index = faiss.IndexFlatL2(embedding_dim)
    self.label_to_index = {}
    self.index_to_label = {}
    self.updates_since_rebuild = 0

def test_initialization(base_classifier):
    assert base_classifier is not None
    assert hasattr(base_classifier, 'model')
    assert hasattr(base_classifier, 'tokenizer')
    assert hasattr(base_classifier, 'memory')

@pytest.fixture
def config():
    return ModelConfig({'max_examples_per_class': 5, 'prototype_update_frequency': 3, 'similarity_threshold': 0.95})

