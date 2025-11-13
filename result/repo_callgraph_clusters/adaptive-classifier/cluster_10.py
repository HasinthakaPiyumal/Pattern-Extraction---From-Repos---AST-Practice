# Cluster 10

class LinearCostFunction(SeparableCostFunction):
    """Linear cost function c(x,y) = <alpha, y-x>_+."""

    def __init__(self, alpha: Union[Dict[str, float], torch.Tensor], feature_names: Optional[List[str]]=None):
        """Initialize linear cost function.
        
        Args:
            alpha: Cost coefficients for each feature
            feature_names: Optional list of feature names for dict-based coefficients
        """
        if isinstance(alpha, dict):
            if feature_names is None:
                raise ValueError('feature_names required when using dict coefficients')
            alpha_tensor = torch.tensor([alpha.get(name, 0.0) for name in feature_names])
        else:
            alpha_tensor = alpha if isinstance(alpha, torch.Tensor) else torch.tensor(alpha)
        super().__init__(alpha_tensor, alpha_tensor, feature_names)
        self.alpha = alpha_tensor

    def compute_cost(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute linear cost c(x,y) = <alpha, y-x>_+."""
        diff = y - x
        cost = torch.dot(self.alpha, diff)
        return torch.relu(cost)

def __init__(self, alpha: Union[Dict[str, float], torch.Tensor], feature_names: Optional[List[str]]=None):
    """Initialize linear cost function.
        
        Args:
            alpha: Cost coefficients for each feature
            feature_names: Optional list of feature names for dict-based coefficients
        """
    if isinstance(alpha, dict):
        if feature_names is None:
            raise ValueError('feature_names required when using dict coefficients')
        alpha_tensor = torch.tensor([alpha.get(name, 0.0) for name in feature_names])
    else:
        alpha_tensor = alpha if isinstance(alpha, torch.Tensor) else torch.tensor(alpha)
    super().__init__(alpha_tensor, alpha_tensor, feature_names)
    self.alpha = alpha_tensor

class MultiLabelAdaptiveHead(nn.Module):
    """Multi-label version of adaptive head using sigmoid activation."""

    def __init__(self, input_dim: int, num_classes: int, hidden_dims: List[int]=None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [input_dim // 2]
        layers = []
        prev_dim = input_dim
        for dim in hidden_dims:
            layers.extend([nn.Linear(prev_dim, dim), nn.ReLU(), nn.Dropout(0.1)])
            prev_dim = dim
        layers.append(nn.Linear(prev_dim, num_classes))
        self.model = nn.Sequential(*layers)
        self.num_classes = num_classes

    def forward(self, x):
        logits = self.model(x)
        return torch.sigmoid(logits)

    def update_num_classes(self, new_num_classes: int):
        """Update the number of output classes while preserving existing weights."""
        if new_num_classes <= self.num_classes:
            return
        final_layer = self.model[-1]
        new_final_layer = nn.Linear(final_layer.in_features, new_num_classes)
        with torch.no_grad():
            new_final_layer.weight[:self.num_classes] = final_layer.weight
            new_final_layer.bias[:self.num_classes] = final_layer.bias
            nn.init.xavier_uniform_(new_final_layer.weight[self.num_classes:])
            nn.init.zeros_(new_final_layer.bias[self.num_classes:])
        self.model[-1] = new_final_layer
        self.num_classes = new_num_classes

def __init__(self, input_dim: int, num_classes: int, hidden_dims: List[int]=None):
    super().__init__()
    if hidden_dims is None:
        hidden_dims = [input_dim // 2]
    layers = []
    prev_dim = input_dim
    for dim in hidden_dims:
        layers.extend([nn.Linear(prev_dim, dim), nn.ReLU(), nn.Dropout(0.1)])
        prev_dim = dim
    layers.append(nn.Linear(prev_dim, num_classes))
    self.model = nn.Sequential(*layers)
    self.num_classes = num_classes

def update_num_classes(self, new_num_classes: int):
    """Update the number of output classes while preserving existing weights."""
    if new_num_classes <= self.num_classes:
        return
    final_layer = self.model[-1]
    new_final_layer = nn.Linear(final_layer.in_features, new_num_classes)
    with torch.no_grad():
        new_final_layer.weight[:self.num_classes] = final_layer.weight
        new_final_layer.bias[:self.num_classes] = final_layer.bias
        nn.init.xavier_uniform_(new_final_layer.weight[self.num_classes:])
        nn.init.zeros_(new_final_layer.bias[self.num_classes:])
    self.model[-1] = new_final_layer
    self.num_classes = new_num_classes

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

def __init__(self, model_name: str, device: Optional[str]=None, config: Optional[Dict[str, Any]]=None, seed: int=42, default_threshold: float=0.5, min_predictions: int=1, max_predictions: Optional[int]=None):
    super().__init__(model_name, device, config, seed)
    self.default_threshold = default_threshold
    self.min_predictions = min_predictions
    self.max_predictions = max_predictions
    self.label_thresholds = {}
    self.adaptive_head = None

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

class AdaptiveHead(nn.Module):
    """Neural network head with stable initialization and deterministic behavior."""

    def __init__(self, input_dim: int, num_classes: int, hidden_dims: Optional[list]=None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [input_dim]
        layers = []
        prev_dim = input_dim
        for dim in hidden_dims:
            linear = nn.Linear(prev_dim, dim)
            torch.manual_seed(42)
            nn.init.kaiming_uniform_(linear.weight, mode='fan_in', nonlinearity='relu')
            nn.init.zeros_(linear.bias)
            layers.extend([linear, nn.ReLU(), nn.Dropout(0.1)])
            prev_dim = dim
        output_layer = nn.Linear(prev_dim, num_classes)
        torch.manual_seed(42)
        nn.init.xavier_uniform_(output_layer.weight)
        nn.init.zeros_(output_layer.bias)
        layers.append(output_layer)
        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass ensuring consistent output shape."""
        if x.dim() == 1:
            x = x.unsqueeze(0)
        output = self.model(x)
        return output

    def update_num_classes(self, num_classes: int):
        """Update output layer with stable weight initialization."""
        current_weight = self.model[-1].weight
        current_bias = self.model[-1].bias
        if num_classes > current_weight.size(0):
            new_layer = nn.Linear(current_weight.size(1), num_classes)
            torch.manual_seed(42)
            nn.init.xavier_uniform_(new_layer.weight)
            nn.init.zeros_(new_layer.bias)
            with torch.no_grad():
                new_layer.weight[:current_weight.size(0)] = current_weight
                new_layer.bias[:current_weight.size(0)] = current_bias
            self.model[-1] = new_layer

def __init__(self, input_dim: int, num_classes: int, hidden_dims: Optional[list]=None):
    super().__init__()
    if hidden_dims is None:
        hidden_dims = [input_dim]
    layers = []
    prev_dim = input_dim
    for dim in hidden_dims:
        linear = nn.Linear(prev_dim, dim)
        torch.manual_seed(42)
        nn.init.kaiming_uniform_(linear.weight, mode='fan_in', nonlinearity='relu')
        nn.init.zeros_(linear.bias)
        layers.extend([linear, nn.ReLU(), nn.Dropout(0.1)])
        prev_dim = dim
    output_layer = nn.Linear(prev_dim, num_classes)
    torch.manual_seed(42)
    nn.init.xavier_uniform_(output_layer.weight)
    nn.init.zeros_(output_layer.bias)
    layers.append(output_layer)
    self.model = nn.Sequential(*layers)

def update_num_classes(self, num_classes: int):
    """Update output layer with stable weight initialization."""
    current_weight = self.model[-1].weight
    current_bias = self.model[-1].bias
    if num_classes > current_weight.size(0):
        new_layer = nn.Linear(current_weight.size(1), num_classes)
        torch.manual_seed(42)
        nn.init.xavier_uniform_(new_layer.weight)
        nn.init.zeros_(new_layer.bias)
        with torch.no_grad():
            new_layer.weight[:current_weight.size(0)] = current_weight
            new_layer.bias[:current_weight.size(0)] = current_bias
        self.model[-1] = new_layer

class SimpleModel(nn.Module):

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 3)

    def forward(self, x):
        return self.fc(x)

def __init__(self):
    super().__init__()
    self.fc = nn.Linear(10, 3)

class TinyModel(nn.Module):

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(5, 2)

    def forward(self, x):
        return self.fc(x)

def __init__(self):
    super().__init__()
    self.fc = nn.Linear(5, 2)

