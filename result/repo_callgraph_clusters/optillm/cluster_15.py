# Cluster 15

class OptILMDataset(Dataset):

    def __init__(self, prompts, approaches, ranks, tokens, tokenizer):
        self.prompts = prompts
        self.approaches = approaches
        self.ranks = ranks
        self.tokens = tokens
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        prompt = self.prompts[idx]
        approaches = self.approaches[idx]
        ranks = self.ranks[idx]
        tokens = self.tokens[idx]
        encoding = self.tokenizer.encode_plus(prompt, add_special_tokens=True, max_length=MAX_LENGTH, padding='max_length', truncation=True, return_attention_mask=True, return_tensors='pt')
        return {'input_ids': encoding['input_ids'].flatten(), 'attention_mask': encoding['attention_mask'].flatten(), 'approaches': torch.tensor([APPROACHES.index(approach) for approach in approaches], dtype=torch.long), 'ranks': torch.tensor(ranks, dtype=torch.float), 'tokens': torch.tensor(tokens, dtype=torch.float)}

def __getitem__(self, idx):
    prompt = self.prompts[idx]
    approaches = self.approaches[idx]
    ranks = self.ranks[idx]
    tokens = self.tokens[idx]
    encoding = self.tokenizer.encode_plus(prompt, add_special_tokens=True, max_length=MAX_LENGTH, padding='max_length', truncation=True, return_attention_mask=True, return_tensors='pt')
    return {'input_ids': encoding['input_ids'].flatten(), 'attention_mask': encoding['attention_mask'].flatten(), 'approaches': torch.tensor([APPROACHES.index(approach) for approach in approaches], dtype=torch.long), 'ranks': torch.tensor(ranks, dtype=torch.float), 'tokens': torch.tensor(tokens, dtype=torch.float)}

class OptILMClassifier(nn.Module):

    def __init__(self, base_model, num_labels):
        super().__init__()
        self.base_model = base_model
        self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

    def forward(self, input_ids, attention_mask, effort):
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0]
        effort_encoded = self.effort_encoder(effort.unsqueeze(1))
        combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
        logits = self.classifier(combined_input)
        return logits

def forward(self, input_ids, attention_mask, effort):
    outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
    pooled_output = outputs.last_hidden_state[:, 0]
    effort_encoded = self.effort_encoder(effort.unsqueeze(1))
    combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
    logits = self.classifier(combined_input)
    return logits

def train(model, train_dataloader, val_dataloader, optimizer, scheduler, num_epochs, patience, clip_value):
    best_val_accuracy = 0.0
    epochs_without_improvement = 0
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        total_accuracy = 0
        for batch in tqdm(train_dataloader, desc=f'Epoch {epoch + 1}/{num_epochs}'):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            approaches = batch['approaches'].to(device)
            ranks = batch['ranks'].to(device)
            tokens = batch['tokens'].to(device)
            effort = (tokens - tokens.min()) / (tokens.max() - tokens.min())
            best_approach_indices = ranks.argmin(dim=1)
            logits = model(input_ids, attention_mask, effort[:, 0])
            ce_loss = F.cross_entropy(logits, best_approach_indices)
            effort_loss = F.mse_loss(logits.softmax(dim=1).gather(1, best_approach_indices.unsqueeze(1)).squeeze(), effort[:, 0])
            loss = ce_loss + 0.1 * effort_loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_value)
            optimizer.step()
            optimizer.zero_grad()
            total_loss += loss.item()
            predictions = torch.argmax(logits, dim=-1)
            total_accuracy += calculate_accuracy(predictions, best_approach_indices)
        avg_train_loss = total_loss / len(train_dataloader)
        avg_train_accuracy = total_accuracy / len(train_dataloader)
        avg_val_accuracy = validate(model, val_dataloader)
        print(f'Epoch {epoch + 1}/{num_epochs}, Train Loss: {avg_train_loss:.4f}, Train Accuracy: {avg_train_accuracy:.4f}, Val Accuracy: {avg_val_accuracy:.4f}')
        if isinstance(scheduler, ReduceLROnPlateau):
            scheduler.step(avg_val_accuracy)
        else:
            scheduler.step()
        if avg_val_accuracy > best_val_accuracy:
            best_val_accuracy = avg_val_accuracy
            epochs_without_improvement = 0
            save_model(model, 'best_model.safetensors')
        else:
            epochs_without_improvement += 1
        if epochs_without_improvement >= patience:
            print(f'Early stopping triggered after {epoch + 1} epochs')
            break

def validate(model, val_dataloader):
    model.eval()
    total_val_accuracy = 0
    with torch.no_grad():
        for batch in val_dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            approaches = batch['approaches'].to(device)
            ranks = batch['ranks'].to(device)
            tokens = batch['tokens'].to(device)
            effort = (tokens - tokens.min()) / (tokens.max() - tokens.min())
            best_approach_indices = ranks.argmin(dim=1)
            logits = model(input_ids, attention_mask, effort[:, 0])
            predictions = torch.argmax(logits, dim=-1)
            total_val_accuracy += calculate_accuracy(predictions, best_approach_indices)
    return total_val_accuracy / len(val_dataloader)

def inference(model, tokenizer, prompt, effort_levels):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(prompt, return_tensors='pt', max_length=MAX_LENGTH, truncation=True, padding='max_length')
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        results = []
        for effort in effort_levels:
            effort_tensor = torch.tensor([effort], dtype=torch.float).to(device)
            logits = model(input_ids, attention_mask, effort_tensor)
            probabilities = F.softmax(logits, dim=1)
            predicted_approach_index = torch.argmax(probabilities, dim=1).item()
            results.append((APPROACHES[predicted_approach_index], probabilities[0][predicted_approach_index].item()))
    return results

def main(args):
    if args.push_to_hub:
        base_model = AutoModel.from_pretrained(args.model_name)
        tokenizer = AutoTokenizer.from_pretrained(args.model_name)
        base_model.push_to_hub(args.hub_model_id)
        tokenizer.push_to_hub(args.hub_model_id)
        return
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    dataset = load_and_preprocess_data(tokenizer)
    kf = KFold(n_splits=args.k_folds, shuffle=True, random_state=42)
    best_val_accuracy = 0
    best_fold = 0
    for fold, (train_indices, val_indices) in enumerate(kf.split(dataset), 1):
        print(f'\nTraining Fold {fold}')
        train_sampler = SubsetRandomSampler(train_indices)
        val_sampler = SubsetRandomSampler(val_indices)
        train_dataloader = DataLoader(dataset, batch_size=args.batch_size, sampler=train_sampler)
        val_dataloader = DataLoader(dataset, batch_size=args.batch_size, sampler=val_sampler)
        base_model = AutoModel.from_pretrained(args.model_name)
        model = OptILMClassifier(base_model, num_labels=len(APPROACHES)).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
        scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.1, patience=2, verbose=True)
        train(model, train_dataloader, val_dataloader, optimizer, scheduler, args.num_epochs, args.patience, args.clip_value)
        fold_val_accuracy = validate(model, val_dataloader)
        print(f'Fold {fold} Validation Accuracy: {fold_val_accuracy:.4f}')
        save_model(model, f'model_fold_{fold}.safetensors')
        if fold_val_accuracy > best_val_accuracy:
            best_val_accuracy = fold_val_accuracy
            best_fold = fold
            save_model(model, 'best_model.safetensors')
    print(f'\nBest performing model was from fold {best_fold} with validation accuracy {best_val_accuracy:.4f}')
    base_model = AutoModel.from_pretrained(args.model_name)
    best_model = OptILMClassifier(base_model, num_labels=len(APPROACHES))
    best_model.to(device)
    load_model(best_model, 'best_model.safetensors')
    best_model.eval()
    test_prompts = ['Maximize x + y subject to: x + 2y <= 10, x >= 0, y >= 0', 'Find the shortest path between nodes A and B in the given graph', 'Solve the Tower of Hanoi problem with 4 disks', 'Determine if the given number is prime', 'Find all possible combinations of coins that sum up to $1', 'Solve the equation: 2x^3 - 5x^2 + 3x - 7 = 0', 'Summarize the main points of the given article in three sentences', 'Describe the contents of the image, including any text present', "Find the Nash equilibrium for the prisoner's dilemma game", 'Solve the Sudoku puzzle given the following initial configuration', 'Find the optimal route for a salesperson visiting 10 cities', 'If all A are B, and some B are C, what can we conclude about A and C?', "Predict the stock price for the next week given the past year's data", 'Plan a path for a robot to navigate through a room with obstacles', 'Identify the sentiment and main topics in the following customer review', 'Prove that the square root of 2 is irrational', 'Design a policy for an agent to maximize its score in a given game environment', 'Find the most relevant documents in the corpus for the given query', 'Decrypt the following message encrypted with a simple substitution cipher', 'Simulate a quantum circuit with 3 qubits and measure the output', 'Generate a 3D model of a house based on the given floor plan', 'Find potential binding sites for a given protein sequence in a DNA strand', 'Given a set of logical statements, determine if the conclusion follows', 'Write a short story in the style of Edgar Allan Poe about a haunted lighthouse']
    effort_levels = [0.0, 0.2, 0.5, 0.8, 1.0]
    print('\nInference Examples:')
    for prompt in test_prompts:
        print(f'\nTest Prompt: {prompt}')
        results = inference(best_model, tokenizer, prompt, effort_levels)
        for effort, (approach, confidence) in zip(effort_levels, results):
            print(f'Effort: {effort:.1f}, Predicted Approach: {approach}, Confidence: {confidence:.4f}')

def push_to_hub(dataset: DatasetDict, repo_id: str):
    """Push the dataset to HuggingFace Hub"""
    try:
        readme_content = f"""# OptiLLMBench Dataset\n\nA benchmark dataset for evaluating test-time optimization and scaling capabilities of language models.\n\n## Dataset Description\n\nOptiLLMBench contains {NUM_SAMPLES} carefully selected challenging problems across multiple domains:\n- Mathematical reasoning (from competition_math)\n- Code generation (from HumanEval)\n- Word problems (from GSM8K)\n- Multiple choice reasoning (from MMLU)\n- Logical deduction (from BBH)\n\nEach example is chosen to benefit from test-time optimization techniques like:\n- Increased context length\n- Chain-of-thought reasoning\n- Self-consistency\n- Multiple solution attempts\n- And other scaling approaches\n\n## Usage\n\n```python\nfrom datasets import load_dataset\n\ndataset = load_dataset("codelion/optillmbench")\n\n# Access examples\nfor example in dataset["train"]:\n    print(f"Category: {{example['category']}}")\n    print(f"Question: {{example['question']}}")\n    print(f"Answer: {{example['answer']}}")\n    print(f"Metadata: {{example['metadata']}}")\n```\n\n## Citation\n\nIf you use this dataset in your research, please cite:\n\n```bibtex\n@software{{optillm,\n  title = {{Optillm: Optimizing inference proxy for LLMs}},\n  author = {{Asankhaya Sharma}},\n  year = {{2024}},\n  publisher = {{GitHub}},\n  url = {{https://github.com/codelion/optillm}}\n}}\n```\n"""
        dataset.push_to_hub(repo_id, private=False, embed_external_files=True)
        api = HfApi()
        api.upload_file(path_or_fileobj=readme_content.encode(), path_in_repo='README.md', repo_id=repo_id, repo_type='dataset')
        print(f'Successfully pushed dataset to {repo_id}')
    except Exception as e:
        print(f'Error pushing to hub: {str(e)}')

def main():
    """Main execution function"""
    print('Starting OptILM Bench dataset generation...')
    dataset = create_benchmark_dataset()
    print('\nDataset Statistics:')
    for split in dataset:
        print(f'\n{split} split:')
        print(f'Number of examples: {len(dataset[split])}')
        categories = dataset[split].unique('category')
        for category in categories:
            count = len([ex for ex in dataset[split] if ex['category'] == category])
            print(f'- {category}: {count} examples')
    print('\nPushing dataset to HuggingFace Hub...')
    push_to_hub(dataset, DATASET_NAME)

class ThinkDeeperProcessor:

    def __init__(self, config: Dict[str, Any], tokenizer, model):
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
            logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
            logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
        for phrase, sequence in zip(self.config['thought_switch_tokens'], self.thought_switch_sequences):
            logger.debug(f"Thought switch marker '{phrase}' encoded as: {sequence}")
            logger.debug(f'Decoded back as: {self.tokenizer.decode(sequence)}')

    def is_thought_switch(self, token: int) -> bool:
        """Check if adding this token creates a thought switch sequence."""
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    @torch.inference_mode()
    def reasoning_effort(self, messages) -> str:
        """Generate response with ThinkDeeper's controlled thinking process"""
        messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
        tokens = self.tokenizer.apply_chat_template(messages, continue_final_message=True, return_tensors='pt')
        tokens = tokens.to(self.model.device)
        kv = DynamicCache()
        n_thinking_tokens = 0
        seen_end_think = False
        response_chunks = []
        while True:
            out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
            logits = out.logits[0, -1, :]
            force_end = n_thinking_tokens >= self.config['max_thinking_tokens'] or self.thought_count >= self.config['max_thoughts']
            if force_end and (not seen_end_think):
                logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                next_token = self.end_think_token
                response_chunks.append(self.tokenizer.decode([next_token]))
                seen_end_think = True
                tokens = torch.tensor([[next_token]]).to(tokens.device)
                continue
            else:
                next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
            kv = out.past_key_values
            next_str = self.tokenizer.decode([next_token])
            if not seen_end_think and self.is_thought_switch(next_token):
                self.thought_count += 1
                logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                self.current_sequence = []
            if next_token == self.end_think_token:
                seen_end_think = True
                logger.debug('Found end think token')
                if n_thinking_tokens < self.config['min_thinking_tokens']:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    seen_end_think = False
                    continue
            if next_token == self.model.config.eos_token_id:
                logger.debug('Found eos token')
                if seen_end_think:
                    logger.debug('Reached EOS after end think token - stopping generation')
                    response_chunks.append(next_str)
                    break
                elif n_thinking_tokens < self.config['min_thinking_tokens']:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    continue
                else:
                    logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                    response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                    tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                    seen_end_think = True
                    continue
            response_chunks.append(next_str)
            if not seen_end_think:
                n_thinking_tokens += 1
            tokens = torch.tensor([[next_token]]).to(tokens.device)
        response = ''.join(response_chunks)
        full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
        logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}, Thinking tokens: {n_thinking_tokens}')
        return (full_response, n_thinking_tokens)

def __init__(self, config: Dict[str, Any], tokenizer, model):
    self.config = {**DEFAULT_CONFIG, **config}
    self.tokenizer = tokenizer
    self.model = model
    start_tokens = self.tokenizer.encode(self.config['start_think_token'])
    end_tokens = self.tokenizer.encode(self.config['end_think_token'])
    self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
    self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
    self.thought_switch_sequences = []
    for phrase in self.config['thought_switch_tokens']:
        token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
        self.thought_switch_sequences.append(token_ids)
        logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
        logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
    self.thought_count = 0
    self.current_sequence = []
    self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
    for phrase, sequence in zip(self.config['thought_switch_tokens'], self.thought_switch_sequences):
        logger.debug(f"Thought switch marker '{phrase}' encoded as: {sequence}")
        logger.debug(f'Decoded back as: {self.tokenizer.decode(sequence)}')

@torch.inference_mode()
def reasoning_effort(self, messages) -> str:
    """Generate response with ThinkDeeper's controlled thinking process"""
    messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
    tokens = self.tokenizer.apply_chat_template(messages, continue_final_message=True, return_tensors='pt')
    tokens = tokens.to(self.model.device)
    kv = DynamicCache()
    n_thinking_tokens = 0
    seen_end_think = False
    response_chunks = []
    while True:
        out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
        logits = out.logits[0, -1, :]
        force_end = n_thinking_tokens >= self.config['max_thinking_tokens'] or self.thought_count >= self.config['max_thoughts']
        if force_end and (not seen_end_think):
            logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
            next_token = self.end_think_token
            response_chunks.append(self.tokenizer.decode([next_token]))
            seen_end_think = True
            tokens = torch.tensor([[next_token]]).to(tokens.device)
            continue
        else:
            next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
        kv = out.past_key_values
        next_str = self.tokenizer.decode([next_token])
        if not seen_end_think and self.is_thought_switch(next_token):
            self.thought_count += 1
            logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
            self.current_sequence = []
        if next_token == self.end_think_token:
            seen_end_think = True
            logger.debug('Found end think token')
            if n_thinking_tokens < self.config['min_thinking_tokens']:
                replacement = random.choice(self.config['thought_switch_tokens'])
                logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                response_chunks.append(replacement)
                replacement_tokens = self.tokenizer.encode(replacement)
                n_thinking_tokens += len(replacement_tokens)
                tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                self.thought_count += 1
                seen_end_think = False
                continue
        if next_token == self.model.config.eos_token_id:
            logger.debug('Found eos token')
            if seen_end_think:
                logger.debug('Reached EOS after end think token - stopping generation')
                response_chunks.append(next_str)
                break
            elif n_thinking_tokens < self.config['min_thinking_tokens']:
                replacement = random.choice(self.config['thought_switch_tokens'])
                logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                response_chunks.append(replacement)
                replacement_tokens = self.tokenizer.encode(replacement)
                n_thinking_tokens += len(replacement_tokens)
                tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                self.thought_count += 1
                continue
            else:
                logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                seen_end_think = True
                continue
        response_chunks.append(next_str)
        if not seen_end_think:
            n_thinking_tokens += 1
        tokens = torch.tensor([[next_token]]).to(tokens.device)
    response = ''.join(response_chunks)
    full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
    logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}, Thinking tokens: {n_thinking_tokens}')
    return (full_response, n_thinking_tokens)

class LogProbsCalculator:
    """Handles calculation of log probabilities for generated tokens"""

    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def _get_bytes_for_token(self, token: str) -> List[int]:
        """Get UTF-8 bytes for a token"""
        try:
            return list(token.encode('utf-8'))
        except UnicodeEncodeError:
            return []

    def _get_top_alternatives(self, logits: torch.Tensor, actual_token_id: int, num_alternatives: int) -> Dict[str, float]:
        """Calculate top alternative tokens and their logprobs"""
        probs = F.softmax(logits, dim=-1)
        logprobs = torch.log(probs)
        top_values, top_indices = torch.topk(logprobs, k=num_alternatives + 1)
        alternatives = {}
        for value, idx in zip(top_values, top_indices):
            token = self.tokenizer.decode([idx])
            if idx != actual_token_id:
                alternatives[token] = value.item()
                if len(alternatives) >= num_alternatives:
                    break
        return alternatives

    def calculate_logprobs(self, input_ids: torch.Tensor, generated_ids: torch.Tensor, attention_mask: torch.Tensor, num_alternatives: int=5) -> LogProbsResult:
        """Calculate log probabilities for a sequence of tokens"""
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)
            logprobs = torch.log(probs)
            all_tokens = []
            all_token_logprobs = []
            all_top_logprobs = []
            all_bytes = []
            sequence_length = generated_ids.shape[-1]
            for pos in range(sequence_length - 1):
                next_token_id = generated_ids[0, pos + 1]
                current_logits = logits[0, pos]
                token = self.tokenizer.decode([next_token_id])
                token_logprob = logprobs[0, pos, next_token_id].item()
                top_logprobs = self._get_top_alternatives(current_logits, next_token_id, num_alternatives)
                token_bytes = self._get_bytes_for_token(token)
                all_tokens.append(token)
                all_token_logprobs.append(token_logprob)
                all_top_logprobs.append(top_logprobs)
                all_bytes.append(token_bytes)
            all_tokens.append(self.tokenizer.decode([generated_ids[0, -1]]))
            all_token_logprobs.append(None)
            all_top_logprobs.append(None)
            all_bytes.append(self._get_bytes_for_token(all_tokens[-1]))
            return LogProbsResult(tokens=all_tokens, token_logprobs=all_token_logprobs, top_logprobs=all_top_logprobs, bytes_per_token=all_bytes)

def _get_top_alternatives(self, logits: torch.Tensor, actual_token_id: int, num_alternatives: int) -> Dict[str, float]:
    """Calculate top alternative tokens and their logprobs"""
    probs = F.softmax(logits, dim=-1)
    logprobs = torch.log(probs)
    top_values, top_indices = torch.topk(logprobs, k=num_alternatives + 1)
    alternatives = {}
    for value, idx in zip(top_values, top_indices):
        token = self.tokenizer.decode([idx])
        if idx != actual_token_id:
            alternatives[token] = value.item()
            if len(alternatives) >= num_alternatives:
                break
    return alternatives

def calculate_logprobs(self, input_ids: torch.Tensor, generated_ids: torch.Tensor, attention_mask: torch.Tensor, num_alternatives: int=5) -> LogProbsResult:
    """Calculate log probabilities for a sequence of tokens"""
    self.model.eval()
    with torch.no_grad():
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)
        logprobs = torch.log(probs)
        all_tokens = []
        all_token_logprobs = []
        all_top_logprobs = []
        all_bytes = []
        sequence_length = generated_ids.shape[-1]
        for pos in range(sequence_length - 1):
            next_token_id = generated_ids[0, pos + 1]
            current_logits = logits[0, pos]
            token = self.tokenizer.decode([next_token_id])
            token_logprob = logprobs[0, pos, next_token_id].item()
            top_logprobs = self._get_top_alternatives(current_logits, next_token_id, num_alternatives)
            token_bytes = self._get_bytes_for_token(token)
            all_tokens.append(token)
            all_token_logprobs.append(token_logprob)
            all_top_logprobs.append(top_logprobs)
            all_bytes.append(token_bytes)
        all_tokens.append(self.tokenizer.decode([generated_ids[0, -1]]))
        all_token_logprobs.append(None)
        all_top_logprobs.append(None)
        all_bytes.append(self._get_bytes_for_token(all_tokens[-1]))
        return LogProbsResult(tokens=all_tokens, token_logprobs=all_token_logprobs, top_logprobs=all_top_logprobs, bytes_per_token=all_bytes)

class MLXInferencePipeline:
    """MLX-based inference pipeline that mirrors PyTorch pipeline interface"""

    def __init__(self, model_config: MLXModelConfig, cache_manager):
        self.model_config = model_config
        self.cache_manager = cache_manager
        self.last_used = time.time()
        if not MLX_AVAILABLE:
            raise RuntimeError('MLX framework not available. Install with: pip install mlx-lm')
        if not is_apple_silicon():
            raise RuntimeError('MLX framework is only supported on Apple Silicon')
        try:
            logger.info(f'Loading MLX model: {model_config.model_id}')
            self.model, self.tokenizer = self._load_mlx_model(model_config.model_id)
            logger.info('MLX model loaded successfully')
        except Exception as e:
            logger.error(f'Failed to load MLX model: {str(e)}')
            raise

    def _load_mlx_model(self, model_id: str):
        """Load MLX model and tokenizer with caching"""

        def _load_model():
            start_time = time.time()
            logger.info(f'Loading MLX model: {model_id}')
            try:
                model, tokenizer = mlx_load(model_id)
                load_time = time.time() - start_time
                logger.info(f'MLX model loaded in {load_time:.2f}s')
                return (model, tokenizer)
            except Exception as e:
                logger.error(f'Error loading MLX model {model_id}: {str(e)}')
                raise
        return self.cache_manager.get_or_load_model(f'mlx_{model_id}', _load_model)

    def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int], List[Optional[Dict]]]:
        """Generate text using MLX"""
        start_time = time.time()
        if generation_params is None:
            generation_params = {}
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        num_return_sequences = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        responses = []
        token_counts = []
        logprobs_results = []
        for _ in range(num_return_sequences):
            try:
                logger.debug(f'Generating with MLX: max_tokens={max_tokens}, temp={temperature}')
                response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                responses.append(response)
                if isinstance(response, str):
                    token_count = len(self.tokenizer.encode(response))
                else:
                    token_count = len(response) if hasattr(response, '__len__') else 0
                token_counts.append(token_count)
                logprobs_results.append(None)
            except Exception as e:
                logger.error(f'Error during MLX generation: {str(e)}')
                logger.error(f'MLX generation parameters: max_tokens={max_tokens}, temp={temperature}, top_p={top_p}')
                responses.append('')
                token_counts.append(0)
                logprobs_results.append(None)
        generation_time = time.time() - start_time
        logger.info(f'MLX generation completed in {generation_time:.2f}s')
        return (responses, token_counts, logprobs_results)

    def _robust_mlx_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float, repetition_penalty: float) -> str:
        """Robust MLX generation using sampler approach"""
        try:
            sampler = make_sampler(temp=temperature, top_p=top_p, min_p=0.0, min_tokens_to_keep=1)
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, sampler=sampler, verbose=False)
            return response
        except Exception as e:
            logger.error(f'MLX generation with sampler failed: {str(e)}')
            try:
                logger.debug('Attempting MLX generation without sampler')
                response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, verbose=False)
                return response
            except Exception as fallback_e:
                logger.error(f'MLX fallback generation also failed: {str(fallback_e)}')
                raise

    def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format the prompt according to model's chat template"""
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            try:
                return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception as e:
                logger.warning(f'Failed to apply chat template: {e}, using fallback')
                return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'
        else:
            return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'

    def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
        """
        Process a batch of prompts with MLX-based batch inference
        
        This method provides true batch processing for MLX models, processing multiple
        prompts simultaneously for improved throughput.
        
        Args:
            system_prompts: List of system prompts
            user_prompts: List of user prompts
            generation_params: Generation parameters (temperature, max_tokens, etc.)
            active_adapter: Active adapter (not used in MLX)
            return_token_count: Whether to return token counts
            
        Returns:
            Tuple of (responses, token_counts)
        """
        import time
        if generation_params is None:
            generation_params = {}
        if len(system_prompts) != len(user_prompts):
            raise ValueError(f'Number of system prompts ({len(system_prompts)}) must match user prompts ({len(user_prompts)})')
        if not system_prompts:
            return ([], [])
        batch_size = len(system_prompts)
        logger.info(f'MLX batch processing {batch_size} prompts')
        start_time = time.time()
        formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        n = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        all_responses = []
        token_counts = []
        try:
            for i, prompt in enumerate(formatted_prompts):
                logger.debug(f'Processing MLX batch item {i + 1}/{batch_size}')
                for _ in range(n):
                    try:
                        response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                        all_responses.append(response)
                        if isinstance(response, str):
                            token_count = len(self.tokenizer.encode(response))
                        else:
                            token_count = len(response) if hasattr(response, '__len__') else 0
                        token_counts.append(token_count)
                    except Exception as e:
                        logger.error(f'Error generating response for batch item {i + 1}: {e}')
                        all_responses.append('')
                        token_counts.append(0)
            processing_time = time.time() - start_time
            logger.info(f'MLX batch processing completed in {processing_time:.2f}s')
            if return_token_count:
                return (all_responses, token_counts)
            return (all_responses, [0] * len(all_responses))
        except Exception as e:
            logger.error(f'MLX batch processing failed: {e}')
            raise

    def _batch_tokenize(self, prompts: List[str]) -> Dict[str, Any]:
        """
        Tokenize a batch of prompts with padding
        
        Args:
            prompts: List of text prompts
            
        Returns:
            Dictionary with tokenized inputs suitable for MLX
        """
        pass

    def _batch_generate(self, input_ids, attention_mask, generation_params: Dict) -> List[str]:
        """
        Perform batch generation using MLX model
        
        Args:
            input_ids: Batched input token IDs
            attention_mask: Attention mask for padded sequences
            generation_params: Generation parameters
            
        Returns:
            List of generated responses
        """
        pass

def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
    """Format the prompt according to model's chat template"""
    if hasattr(self.tokenizer, 'apply_chat_template'):
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        try:
            return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception as e:
            logger.warning(f'Failed to apply chat template: {e}, using fallback')
            return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'
    else:
        return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'

class MemoryEfficientAttention(nn.Module):
    """
    Memory-efficient attention using linear attention mechanism.
    Supports automatic fallback to optimized implementations when available.
    """

    def __init__(self, hidden_size: int, num_attention_heads: int, dropout: float=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.head_dim = hidden_size // num_attention_heads
        self.scale = self.head_dim ** (-0.5)
        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.o_proj = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.optimized_attention = None
        try:
            from flash_attn import flash_attn_func
            self.optimized_attention = flash_attn_func
            print('Using Flash Attention')
        except ImportError:
            pass
        if self.optimized_attention is None:
            try:
                import xformers.ops as xops
                self.optimized_attention = xops.memory_efficient_attention
                print('Using xFormers attention')
            except ImportError:
                pass

    def _linear_attention(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
        """Implements linear attention for more memory efficiency"""
        q = q * self.scale
        if attention_mask is not None:
            if attention_mask.dtype == torch.bool:
                attention_mask = attention_mask.float()
            k = k * attention_mask.unsqueeze(-1)
        if causal:
            batch_size, num_heads, seq_length, head_dim = q.shape
            positions = torch.arange(seq_length, device=q.device)
            causal_mask = positions.view(1, 1, -1, 1) <= positions.view(1, 1, 1, -1)
            k = k * causal_mask.float()
        context = torch.matmul(k.transpose(-2, -1), v)
        out = torch.matmul(q, context)
        return out

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
        batch_size, seq_length, _ = hidden_states.size()
        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)
        q = q.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        if self.optimized_attention is not None and hidden_states.device.type == 'cuda':
            if attention_mask is not None:
                if attention_mask.dtype != torch.bool:
                    attention_mask = attention_mask > 0
                attention_mask = attention_mask.view(batch_size, 1, 1, seq_length)
            try:
                attn_output = self.optimized_attention(q, k, v, attn_mask=attention_mask, causal=causal, scale=self.scale)
            except Exception as e:
                print(f'Optimized attention failed, falling back to linear attention: {e}')
                attn_output = self._linear_attention(q, k, v, attention_mask, causal)
        else:
            attn_output = self._linear_attention(q, k, v, attention_mask, causal)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_length, self.hidden_size)
        attn_output = self.o_proj(attn_output)
        return attn_output

def _linear_attention(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
    """Implements linear attention for more memory efficiency"""
    q = q * self.scale
    if attention_mask is not None:
        if attention_mask.dtype == torch.bool:
            attention_mask = attention_mask.float()
        k = k * attention_mask.unsqueeze(-1)
    if causal:
        batch_size, num_heads, seq_length, head_dim = q.shape
        positions = torch.arange(seq_length, device=q.device)
        causal_mask = positions.view(1, 1, -1, 1) <= positions.view(1, 1, 1, -1)
        k = k * causal_mask.float()
    context = torch.matmul(k.transpose(-2, -1), v)
    out = torch.matmul(q, context)
    return out

def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
    batch_size, seq_length, _ = hidden_states.size()
    q = self.q_proj(hidden_states)
    k = self.k_proj(hidden_states)
    v = self.v_proj(hidden_states)
    q = q.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
    k = k.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
    v = v.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
    if self.optimized_attention is not None and hidden_states.device.type == 'cuda':
        if attention_mask is not None:
            if attention_mask.dtype != torch.bool:
                attention_mask = attention_mask > 0
            attention_mask = attention_mask.view(batch_size, 1, 1, seq_length)
        try:
            attn_output = self.optimized_attention(q, k, v, attn_mask=attention_mask, causal=causal, scale=self.scale)
        except Exception as e:
            print(f'Optimized attention failed, falling back to linear attention: {e}')
            attn_output = self._linear_attention(q, k, v, attention_mask, causal)
    else:
        attn_output = self._linear_attention(q, k, v, attention_mask, causal)
    attn_output = attn_output.transpose(1, 2).contiguous()
    attn_output = attn_output.view(batch_size, seq_length, self.hidden_size)
    attn_output = self.o_proj(attn_output)
    return attn_output

class DynamicTemperature:
    """Implements dynamic temperature scaling based on input characteristics"""

    def __init__(self):
        self.token_entropy_cache = {}

    def _compute_token_entropy(self, tokens: List[int]) -> float:
        """Compute token distribution entropy"""
        token_counts = np.bincount(tokens)
        probabilities = token_counts / len(tokens)
        return entropy(probabilities)

    def get_optimal_temperature(self, prompt: str, tokenizer: AutoTokenizer, base_temperature: float) -> float:
        """Calculate optimal temperature based on prompt characteristics"""
        tokens = tokenizer.encode(prompt)
        token_entropy = self._compute_token_entropy(tokens)
        length_factor = np.clip(len(tokens) / 100, 0.5, 2.0)
        entropy_factor = np.clip(token_entropy / 4.0, 0.5, 1.5)
        optimal_temperature = base_temperature * length_factor * entropy_factor
        return np.clip(optimal_temperature, 0.1, 2.0)

def get_optimal_temperature(self, prompt: str, tokenizer: AutoTokenizer, base_temperature: float) -> float:
    """Calculate optimal temperature based on prompt characteristics"""
    tokens = tokenizer.encode(prompt)
    token_entropy = self._compute_token_entropy(tokens)
    length_factor = np.clip(len(tokens) / 100, 0.5, 2.0)
    entropy_factor = np.clip(token_entropy / 4.0, 0.5, 1.5)
    optimal_temperature = base_temperature * length_factor * entropy_factor
    return np.clip(optimal_temperature, 0.1, 2.0)

class DeviceManager:

    def __init__(self):
        self.available_devices = self._detect_devices()
        self.device_stats = {device: {'memory_used': 0, 'active_models': 0} for device in self.available_devices}

    def _detect_devices(self) -> List[str]:
        devices = ['cpu']
        if torch.cuda.is_available():
            devices.extend([f'cuda:{i}' for i in range(torch.cuda.device_count())])
        if torch.backends.mps.is_available():
            devices.append('mps')
        return devices

    def get_optimal_device(self, model_size: int=0) -> str:
        if not self.available_devices:
            return 'cpu'
        cuda_devices = [d for d in self.available_devices if 'cuda' in d]
        if cuda_devices:
            max_free_memory = 0
            optimal_device = cuda_devices[0]
            for device in cuda_devices:
                idx = int(device.split(':')[1])
                free_memory = torch.cuda.get_device_properties(idx).total_memory - torch.cuda.memory_allocated(idx)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    optimal_device = device
            return optimal_device
        if 'mps' in self.available_devices:
            return 'mps'
        return 'cpu'

    def track_device_usage(self, device: str, memory_delta: int):
        if device in self.device_stats:
            self.device_stats[device]['memory_used'] += memory_delta

def get_optimal_device(self, model_size: int=0) -> str:
    if not self.available_devices:
        return 'cpu'
    cuda_devices = [d for d in self.available_devices if 'cuda' in d]
    if cuda_devices:
        max_free_memory = 0
        optimal_device = cuda_devices[0]
        for device in cuda_devices:
            idx = int(device.split(':')[1])
            free_memory = torch.cuda.get_device_properties(idx).total_memory - torch.cuda.memory_allocated(idx)
            if free_memory > max_free_memory:
                max_free_memory = free_memory
                optimal_device = device
        return optimal_device
    if 'mps' in self.available_devices:
        return 'mps'
    return 'cpu'

class InferencePipeline:

    def __init__(self, model_config: ModelConfig, cache_manager, device_manager, model_manager, lora_manager):
        self.model_config = model_config
        self.cache_manager = cache_manager
        self.device_manager = device_manager
        self.model_manager = model_manager
        self.lora_manager = lora_manager
        self.last_used = time.time()
        try:
            self.base_model, self.tokenizer = self.model_manager.load_base_model(model_config.base_model_id, quantize=model_config.quantization_bits == 4)
            self.tokenizer = self.setup_tokenizer(self.tokenizer)
            if self.base_model.get_input_embeddings().num_embeddings != len(self.tokenizer):
                self.base_model.resize_token_embeddings(len(self.tokenizer))
            self.current_model = self.base_model
            if model_config.adapter_ids:
                for adapter_id in model_config.adapter_ids:
                    try:
                        self.current_model = self.lora_manager.load_adapter(self.current_model, adapter_id)
                    except Exception as e:
                        logger.error(f'Error loading adapter {adapter_id}: {e}')
                if isinstance(self.current_model, PeftModel):
                    success = self.lora_manager.set_active_adapter(self.current_model)
                    if not success:
                        logger.error('Failed to set active adapter')
            self.dtype = self.current_model.dtype
            self.optimal_batch_size = self._find_optimal_batch_size()
        except Exception as e:
            logger.error(f'Pipeline initialization error: {str(e)}')
            logger.error(f'Error traceback: {traceback.format_exc()}')
            raise

    def setup_tokenizer(self, tokenizer: AutoTokenizer) -> AutoTokenizer:
        """Use tokenizer with its default configuration for inference"""
        logger.debug('  a. Starting tokenizer setup')
        logger.debug(f'  b. Using tokenizer with vocab size: {len(tokenizer)}')
        logger.debug(f'  c. Special tokens: PAD={tokenizer.pad_token_id}, EOS={tokenizer.eos_token_id}, BOS={tokenizer.bos_token_id}')
        return tokenizer

    def get_optimized_generation_config(self, generation_params: Optional[Dict[str, Any]]=None) -> Dict:
        """Get optimized generation config"""
        config = {'max_new_tokens': generation_params.get('max_new_tokens', 4096), 'do_sample': generation_params.get('temperature', 1.0) > 0, 'temperature': generation_params.get('temperature', 1.0), 'top_p': generation_params.get('top_p', 0.95), 'num_return_sequences': generation_params.get('num_return_sequences', 1), 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id, 'return_dict_in_generate': True, 'output_scores': generation_params.get('logprobs', False), 'use_cache': True}
        return config

    def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int]]:
        """Generate completions with optional logprobs"""
        start_time = time.time()
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        tokenize_start = time.time()
        inputs = self.tokenizer(prompt, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
        logger.info(f'Tokenization time: {time.time() - tokenize_start:.2f}s')
        calculate_logprobs = generation_params.get('logprobs', False)
        top_logprobs = generation_params.get('top_logprobs', 0)
        if top_logprobs and (not calculate_logprobs):
            raise ValueError('logprobs must be true when top_logprobs is specified')
        if top_logprobs and (not 0 <= top_logprobs <= 20):
            raise ValueError('top_logprobs must be between 0 and 20')
        gen_config = self.get_optimized_generation_config(generation_params)
        if generation_params:
            if generation_params.get('presence_penalty', 0) != 0:
                gen_config['presence_penalty'] = generation_params['presence_penalty']
            if generation_params.get('frequency_penalty', 0) != 0:
                gen_config['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
            if generation_params.get('stop_sequences'):
                gen_config['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], inputs['input_ids'].shape[1])
            if generation_params.get('seed') is not None:
                torch.manual_seed(generation_params['seed'])
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(generation_params['seed'])
        generate_start = time.time()
        with torch.inference_mode():
            outputs = self.current_model.generate(**inputs, **gen_config)
        logger.info(f'Generation time: {time.time() - generate_start:.2f}s')
        generated_sequences = outputs.sequences
        input_length = inputs['input_ids'].shape[1]
        process_start = time.time()
        responses = []
        token_counts = []
        logprobs_results = []
        for sequence in generated_sequences:
            response_tokens = sequence[input_length:]
            response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            responses.append(response_text)
            token_counts.append(len(response_tokens))
            if calculate_logprobs:
                calculator = LogProbsCalculator(self.tokenizer, self.current_model)
                logprobs_result = calculator.calculate_logprobs(input_ids=sequence.unsqueeze(0), generated_ids=sequence.unsqueeze(0), attention_mask=torch.ones_like(sequence).unsqueeze(0), num_alternatives=top_logprobs or 5)
                logprobs_results.append({'content': [{'token': token, 'logprob': logprob, 'bytes': bytes_, 'top_logprobs': top_logprobs} for token, logprob, bytes_, top_logprobs in zip(logprobs_result.tokens[input_length:], logprobs_result.token_logprobs[input_length:], logprobs_result.bytes_per_token[input_length:], logprobs_result.top_logprobs[input_length:])]})
            else:
                logprobs_results.append(None)
        logger.info(f'Post-processing time: {time.time() - process_start:.2f}s')
        logger.info(f'Total generation time: {time.time() - start_time:.2f}s')
        return (responses, token_counts, logprobs_results)

    def setup_efficient_attention(self):
        """Replace standard attention with memory-efficient version"""
        if hasattr(self.current_model, 'config') and hasattr(self.current_model.config, 'hidden_size'):
            hidden_size = self.current_model.config.hidden_size
            num_attention_heads = self.current_model.config.num_attention_heads
            self.efficient_attention = MemoryEfficientAttention(hidden_size, num_attention_heads)
            if hasattr(self.current_model, 'encoder') and hasattr(self.current_model.encoder, 'layer'):
                for layer in self.current_model.encoder.layer:
                    if hasattr(layer, 'attention'):
                        layer.attention.self = self.efficient_attention
            logger.info('Memory-efficient attention mechanism enabled')

    def _find_optimal_batch_size(self, initial_batch_size: int=1, max_batch_size: int=128) -> int:
        """Find optimal batch size through binary search with memory monitoring"""
        if not torch.cuda.is_available():
            return initial_batch_size
        device = self.current_model.device
        if 'cuda' not in str(device):
            return initial_batch_size
        left, right = (initial_batch_size, max_batch_size)
        optimal_size = initial_batch_size
        sample_text = 'Sample input text for batch size optimization.'
        while left <= right:
            mid = (left + right) // 2
            try:
                torch.cuda.empty_cache()
                inputs = self.tokenizer([sample_text] * mid, padding=True, truncation=True, return_tensors='pt').to(device)
                with torch.amp.autocast('cuda', dtype=self.dtype):
                    with torch.no_grad():
                        _ = self.current_model.generate(**inputs, max_new_tokens=1, num_return_sequences=1, pad_token_id=self.tokenizer.pad_token_id)
                optimal_size = mid
                left = mid + 1
                memory_used = torch.cuda.memory_allocated(device)
                total_memory = torch.cuda.get_device_properties(device).total_memory
                if memory_used > 0.9 * total_memory:
                    break
            except torch.cuda.OutOfMemoryError:
                right = mid - 1
                torch.cuda.empty_cache()
        return max(1, int(optimal_size * 0.9))

    def optimize_generation_params(self, prompt: str) -> Dict[str, Any]:
        """Optimize generation parameters based on prompt characteristics"""
        base_params = {'max_new_tokens': self.model_config.max_new_tokens, 'do_sample': self.model_config.do_sample, 'top_p': self.model_config.top_p, 'top_k': self.model_config.top_k, 'temperature': self.model_config.temperature, 'num_return_sequences': self.model_config.num_return_sequences, 'repetition_penalty': self.model_config.repetition_penalty, 'pad_token_id': self.model_config.pad_token_id or self.tokenizer.pad_token_id}
        if self.model_config.dynamic_temperature:
            base_params['temperature'] = self.dynamic_temperature.get_optimal_temperature(prompt, self.tokenizer, base_params['temperature'])
        return base_params

    def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format the prompt according to model's chat template"""
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            return self.tokenizer.apply_chat_template(messages, tokenize=False)
        else:
            return f'<|system|>{system_prompt}</s><|user|>{user_prompt}</s><|assistant|>'

    def _create_stopping_criteria(self, stop_sequences: List[str], input_length: int):
        """Create stopping criteria for generation"""
        from transformers import StoppingCriteria, StoppingCriteriaList

        class StopSequenceCriteria(StoppingCriteria):

            def __init__(self, tokenizer, stop_sequences, input_length):
                self.tokenizer = tokenizer
                self.stop_ids = [self.tokenizer.encode(seq, add_special_tokens=False) for seq in stop_sequences]
                self.input_length = input_length

            def __call__(self, input_ids, scores, **kwargs):
                for stop_ids in self.stop_ids:
                    if input_ids[0, -len(stop_ids):].tolist() == stop_ids:
                        return True
                return False
        return StoppingCriteriaList([StopSequenceCriteria(self.tokenizer, stop_sequences, input_length=input_length)])

    def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
        """Process a batch of prompts with all optimizations"""
        if isinstance(self.current_model, PeftModel) and active_adapter is not None:
            self.lora_manager.set_active_adapter(self.current_model, active_adapter)
        all_responses = []
        token_counts = []
        formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
        n = generation_params.get('num_return_sequences', 1) if generation_params else 1
        for i in range(0, len(formatted_prompts), self.optimal_batch_size):
            batch_prompts = formatted_prompts[i:i + self.optimal_batch_size]
            batch_system = system_prompts[i:i + self.optimal_batch_size]
            batch_user = user_prompts[i:i + self.optimal_batch_size]
            if self.model_config.enable_prompt_caching:
                cached_responses = []
                uncached_indices = []
                for idx, prompt in enumerate(batch_prompts):
                    temp = generation_params.get('temperature', self.model_config.temperature) if generation_params else self.model_config.temperature
                    top_p = generation_params.get('top_p', self.model_config.top_p) if generation_params else self.model_config.top_p
                    cached_response = self.cache_manager.prompt_cache.get_cached_response(prompt, temp, top_p)
                    if cached_response is not None:
                        cached_responses.extend([cached_response] * n)
                    else:
                        uncached_indices.append(idx)
                if uncached_indices:
                    batch_prompts = [batch_prompts[i] for i in uncached_indices]
                else:
                    batch_prompts = []
            if batch_prompts:
                base_params = {'max_new_tokens': generation_params.get('max_new_tokens', 4096) if generation_params else self.model_config.max_new_tokens, 'do_sample': generation_params.get('temperature', 1.0) > 0 if generation_params else self.model_config.do_sample, 'temperature': generation_params.get('temperature', 1.0) if generation_params else self.model_config.temperature, 'top_p': generation_params.get('top_p', 1.0) if generation_params else self.model_config.top_p, 'num_return_sequences': n, 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id}
                if generation_params:
                    if generation_params.get('presence_penalty', 0) != 0:
                        base_params['presence_penalty'] = generation_params['presence_penalty']
                    if generation_params.get('frequency_penalty', 0) != 0:
                        base_params['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
                    if generation_params.get('logit_bias'):
                        base_params['logit_bias'] = generation_params['logit_bias']
                    if generation_params.get('seed') is not None:
                        torch.manual_seed(generation_params['seed'])
                        if torch.cuda.is_available():
                            torch.cuda.manual_seed(generation_params['seed'])
                inputs = self.tokenizer(batch_prompts, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
                input_lengths = inputs['input_ids'].shape[1]
                if generation_params and generation_params.get('stop_sequences'):
                    base_params['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], input_lengths)
                with torch.amp.autocast('cuda', dtype=self.dtype):
                    with torch.no_grad():
                        outputs = self.current_model.generate(**inputs, **base_params)
                batch_responses = []
                batch_token_counts = []
                num_return_sequences = base_params['num_return_sequences']
                for i in range(0, len(outputs), num_return_sequences):
                    sequences = outputs[i:i + num_return_sequences]
                    for seq in sequences:
                        response_tokens = seq[input_lengths:]
                        response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
                        batch_responses.append(response_text)
                        batch_token_counts.append(len(response_tokens))
                if self.model_config.enable_prompt_caching:
                    for prompt, response in zip(batch_prompts, batch_responses[::n]):
                        self.cache_manager.prompt_cache.add_to_cache(prompt, response, base_params['temperature'], base_params['top_p'])
                all_responses.extend(cached_responses)
                if uncached_indices:
                    response_idx = 0
                    for original_idx in range(len(formatted_prompts[i:i + self.optimal_batch_size])):
                        if original_idx in uncached_indices:
                            for _ in range(n):
                                while len(all_responses) < original_idx * n + _:
                                    all_responses.append('')
                                if response_idx < len(batch_responses):
                                    all_responses.append(batch_responses[response_idx])
                                    response_idx += 1
                if return_token_count:
                    token_counts.extend([0] * len(cached_responses))
                    token_counts.extend(batch_token_counts)
        if return_token_count:
            return (all_responses, token_counts)
        return (all_responses, [0] * len(all_responses))

def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int]]:
    """Generate completions with optional logprobs"""
    start_time = time.time()
    if self.tokenizer.pad_token is None:
        self.tokenizer.pad_token = self.tokenizer.eos_token
    tokenize_start = time.time()
    inputs = self.tokenizer(prompt, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
    logger.info(f'Tokenization time: {time.time() - tokenize_start:.2f}s')
    calculate_logprobs = generation_params.get('logprobs', False)
    top_logprobs = generation_params.get('top_logprobs', 0)
    if top_logprobs and (not calculate_logprobs):
        raise ValueError('logprobs must be true when top_logprobs is specified')
    if top_logprobs and (not 0 <= top_logprobs <= 20):
        raise ValueError('top_logprobs must be between 0 and 20')
    gen_config = self.get_optimized_generation_config(generation_params)
    if generation_params:
        if generation_params.get('presence_penalty', 0) != 0:
            gen_config['presence_penalty'] = generation_params['presence_penalty']
        if generation_params.get('frequency_penalty', 0) != 0:
            gen_config['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
        if generation_params.get('stop_sequences'):
            gen_config['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], inputs['input_ids'].shape[1])
        if generation_params.get('seed') is not None:
            torch.manual_seed(generation_params['seed'])
            if torch.cuda.is_available():
                torch.cuda.manual_seed(generation_params['seed'])
    generate_start = time.time()
    with torch.inference_mode():
        outputs = self.current_model.generate(**inputs, **gen_config)
    logger.info(f'Generation time: {time.time() - generate_start:.2f}s')
    generated_sequences = outputs.sequences
    input_length = inputs['input_ids'].shape[1]
    process_start = time.time()
    responses = []
    token_counts = []
    logprobs_results = []
    for sequence in generated_sequences:
        response_tokens = sequence[input_length:]
        response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
        responses.append(response_text)
        token_counts.append(len(response_tokens))
        if calculate_logprobs:
            calculator = LogProbsCalculator(self.tokenizer, self.current_model)
            logprobs_result = calculator.calculate_logprobs(input_ids=sequence.unsqueeze(0), generated_ids=sequence.unsqueeze(0), attention_mask=torch.ones_like(sequence).unsqueeze(0), num_alternatives=top_logprobs or 5)
            logprobs_results.append({'content': [{'token': token, 'logprob': logprob, 'bytes': bytes_, 'top_logprobs': top_logprobs} for token, logprob, bytes_, top_logprobs in zip(logprobs_result.tokens[input_length:], logprobs_result.token_logprobs[input_length:], logprobs_result.bytes_per_token[input_length:], logprobs_result.top_logprobs[input_length:])]})
        else:
            logprobs_results.append(None)
    logger.info(f'Post-processing time: {time.time() - process_start:.2f}s')
    logger.info(f'Total generation time: {time.time() - start_time:.2f}s')
    return (responses, token_counts, logprobs_results)

def _find_optimal_batch_size(self, initial_batch_size: int=1, max_batch_size: int=128) -> int:
    """Find optimal batch size through binary search with memory monitoring"""
    if not torch.cuda.is_available():
        return initial_batch_size
    device = self.current_model.device
    if 'cuda' not in str(device):
        return initial_batch_size
    left, right = (initial_batch_size, max_batch_size)
    optimal_size = initial_batch_size
    sample_text = 'Sample input text for batch size optimization.'
    while left <= right:
        mid = (left + right) // 2
        try:
            torch.cuda.empty_cache()
            inputs = self.tokenizer([sample_text] * mid, padding=True, truncation=True, return_tensors='pt').to(device)
            with torch.amp.autocast('cuda', dtype=self.dtype):
                with torch.no_grad():
                    _ = self.current_model.generate(**inputs, max_new_tokens=1, num_return_sequences=1, pad_token_id=self.tokenizer.pad_token_id)
            optimal_size = mid
            left = mid + 1
            memory_used = torch.cuda.memory_allocated(device)
            total_memory = torch.cuda.get_device_properties(device).total_memory
            if memory_used > 0.9 * total_memory:
                break
        except torch.cuda.OutOfMemoryError:
            right = mid - 1
            torch.cuda.empty_cache()
    return max(1, int(optimal_size * 0.9))

def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
    """Format the prompt according to model's chat template"""
    if hasattr(self.tokenizer, 'apply_chat_template'):
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        return self.tokenizer.apply_chat_template(messages, tokenize=False)
    else:
        return f'<|system|>{system_prompt}</s><|user|>{user_prompt}</s><|assistant|>'

class StopSequenceCriteria(StoppingCriteria):

    def __init__(self, tokenizer, stop_sequences, input_length):
        self.tokenizer = tokenizer
        self.stop_ids = [self.tokenizer.encode(seq, add_special_tokens=False) for seq in stop_sequences]
        self.input_length = input_length

    def __call__(self, input_ids, scores, **kwargs):
        for stop_ids in self.stop_ids:
            if input_ids[0, -len(stop_ids):].tolist() == stop_ids:
                return True
        return False

def __init__(self, tokenizer, stop_sequences, input_length):
    self.tokenizer = tokenizer
    self.stop_ids = [self.tokenizer.encode(seq, add_special_tokens=False) for seq in stop_sequences]
    self.input_length = input_length

def __call__(self, input_ids, scores, **kwargs):
    for stop_ids in self.stop_ids:
        if input_ids[0, -len(stop_ids):].tolist() == stop_ids:
            return True
    return False

def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
    """Process a batch of prompts with all optimizations"""
    if isinstance(self.current_model, PeftModel) and active_adapter is not None:
        self.lora_manager.set_active_adapter(self.current_model, active_adapter)
    all_responses = []
    token_counts = []
    formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
    n = generation_params.get('num_return_sequences', 1) if generation_params else 1
    for i in range(0, len(formatted_prompts), self.optimal_batch_size):
        batch_prompts = formatted_prompts[i:i + self.optimal_batch_size]
        batch_system = system_prompts[i:i + self.optimal_batch_size]
        batch_user = user_prompts[i:i + self.optimal_batch_size]
        if self.model_config.enable_prompt_caching:
            cached_responses = []
            uncached_indices = []
            for idx, prompt in enumerate(batch_prompts):
                temp = generation_params.get('temperature', self.model_config.temperature) if generation_params else self.model_config.temperature
                top_p = generation_params.get('top_p', self.model_config.top_p) if generation_params else self.model_config.top_p
                cached_response = self.cache_manager.prompt_cache.get_cached_response(prompt, temp, top_p)
                if cached_response is not None:
                    cached_responses.extend([cached_response] * n)
                else:
                    uncached_indices.append(idx)
            if uncached_indices:
                batch_prompts = [batch_prompts[i] for i in uncached_indices]
            else:
                batch_prompts = []
        if batch_prompts:
            base_params = {'max_new_tokens': generation_params.get('max_new_tokens', 4096) if generation_params else self.model_config.max_new_tokens, 'do_sample': generation_params.get('temperature', 1.0) > 0 if generation_params else self.model_config.do_sample, 'temperature': generation_params.get('temperature', 1.0) if generation_params else self.model_config.temperature, 'top_p': generation_params.get('top_p', 1.0) if generation_params else self.model_config.top_p, 'num_return_sequences': n, 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id}
            if generation_params:
                if generation_params.get('presence_penalty', 0) != 0:
                    base_params['presence_penalty'] = generation_params['presence_penalty']
                if generation_params.get('frequency_penalty', 0) != 0:
                    base_params['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
                if generation_params.get('logit_bias'):
                    base_params['logit_bias'] = generation_params['logit_bias']
                if generation_params.get('seed') is not None:
                    torch.manual_seed(generation_params['seed'])
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed(generation_params['seed'])
            inputs = self.tokenizer(batch_prompts, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
            input_lengths = inputs['input_ids'].shape[1]
            if generation_params and generation_params.get('stop_sequences'):
                base_params['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], input_lengths)
            with torch.amp.autocast('cuda', dtype=self.dtype):
                with torch.no_grad():
                    outputs = self.current_model.generate(**inputs, **base_params)
            batch_responses = []
            batch_token_counts = []
            num_return_sequences = base_params['num_return_sequences']
            for i in range(0, len(outputs), num_return_sequences):
                sequences = outputs[i:i + num_return_sequences]
                for seq in sequences:
                    response_tokens = seq[input_lengths:]
                    response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
                    batch_responses.append(response_text)
                    batch_token_counts.append(len(response_tokens))
            if self.model_config.enable_prompt_caching:
                for prompt, response in zip(batch_prompts, batch_responses[::n]):
                    self.cache_manager.prompt_cache.add_to_cache(prompt, response, base_params['temperature'], base_params['top_p'])
            all_responses.extend(cached_responses)
            if uncached_indices:
                response_idx = 0
                for original_idx in range(len(formatted_prompts[i:i + self.optimal_batch_size])):
                    if original_idx in uncached_indices:
                        for _ in range(n):
                            while len(all_responses) < original_idx * n + _:
                                all_responses.append('')
                            if response_idx < len(batch_responses):
                                all_responses.append(batch_responses[response_idx])
                                response_idx += 1
            if return_token_count:
                token_counts.extend([0] * len(cached_responses))
                token_counts.extend(batch_token_counts)
    if return_token_count:
        return (all_responses, token_counts)
    return (all_responses, [0] * len(all_responses))

class Completions:

    def __init__(self, client: 'InferenceClient'):
        self.client = client

    def create(self, messages: List[Dict[str, str]], model: str, temperature: float=1.0, top_p: float=1.0, n: int=1, stream: bool=False, stop: Optional[Union[str, List[str]]]=None, max_tokens: Optional[int]=None, presence_penalty: float=0, frequency_penalty: float=0, logit_bias: Optional[Dict[str, float]]=None, seed: Optional[int]=None, logprobs: Optional[bool]=None, top_logprobs: Optional[int]=None, active_adapter: Optional[Dict[str, Any]]=None, decoding: Optional[str]=None, k: int=10, num_beams: int=1, length_penalty: float=1.0, no_repeat_ngram_size: int=0, early_stopping: bool=False, aggregate_paths: bool=True, top_k: int=27, min_p: float=0.03, reasoning_effort: str='low', thought_switch_tokens: List[str]=[], min_thinking_tokens: Optional[int]=None, max_thinking_tokens: Optional[int]=None, max_thoughts: Optional[int]=None, prefill: str='', start_think_token: str='<think>', end_think_token: str='</think>', **kwargs) -> ChatCompletion:
        """Create a chat completion with OpenAI-compatible parameters"""
        logger.info('Starting chat completion creation')
        if stream:
            raise NotImplementedError('Streaming is not yet supported')
        logger.info(f'Getting pipeline for model: {model}')
        pipeline = self.client.get_pipeline(model)
        logger.info('Pipeline acquired')
        if active_adapter is not None:
            logger.info(f'Setting active adapter to: {active_adapter}')
            pipeline.lora_manager.set_active_adapter(pipeline.current_model, active_adapter)
        responses = []
        logprobs_results = []
        prompt_tokens = 0
        completion_tokens = 0
        try:
            if decoding:
                logger.info(f'Using specialized decoding approach: {decoding}')
                mlx_unsupported_decodings = ['cot_decoding', 'entropy_decoding', 'autothink', 'deepconf']
                if isinstance(pipeline, MLXInferencePipeline) and decoding in mlx_unsupported_decodings:
                    logger.warning(f'{decoding} is not supported for MLX models. Falling back to standard generation.')
                    decoding = None
            if decoding:
                if not isinstance(pipeline, MLXInferencePipeline):
                    pipeline.current_model.eval()
                    device = pipeline.current_model.device
                else:
                    device = None
                if decoding == 'cot_decoding':
                    cot_params = {'k': k, 'num_beams': num_beams, 'max_new_tokens': max_tokens if max_tokens is not None else 512, 'temperature': temperature, 'top_p': top_p, 'repetition_penalty': 1.0, 'length_penalty': length_penalty, 'no_repeat_ngram_size': no_repeat_ngram_size, 'early_stopping': early_stopping, 'aggregate_paths': aggregate_paths}
                    result, confidence = cot_decode(pipeline.current_model, pipeline.tokenizer, messages, **cot_params)
                    responses = [result]
                    logprobs_results = [{'confidence_score': confidence} if confidence is not None else None]
                    completion_tokens = len(pipeline.tokenizer.encode(result))
                elif decoding == 'entropy_decoding':
                    original_dtype = pipeline.current_model.dtype
                    pipeline.current_model = pipeline.current_model.to(torch.float32)
                    try:
                        generator = None
                        if seed is not None:
                            generator = torch.Generator(device=device)
                            generator.manual_seed(seed)
                        else:
                            generator = torch.Generator(device=device)
                            generator.manual_seed(1337)
                        entropy_params = {'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'temperature': temperature, 'top_p': top_p, 'top_k': top_k, 'min_p': min_p, 'generator': generator}
                        with torch.amp.autocast('cuda', enabled=False), torch.inference_mode():
                            result = entropy_decode(pipeline.current_model, pipeline.tokenizer, messages, **entropy_params)
                        responses = [result]
                        logprobs_results = [None]
                        completion_tokens = len(pipeline.tokenizer.encode(result))
                    finally:
                        pipeline.current_model = pipeline.current_model.to(original_dtype)
                elif decoding == 'thinkdeeper':
                    thinkdeeper_config = get_effort_profile(reasoning_effort, max_tokens)
                    custom_config = {'min_thinking_tokens': min_thinking_tokens if min_thinking_tokens is not None else thinkdeeper_config['min_thinking_tokens'], 'max_thinking_tokens': max_thinking_tokens if max_thinking_tokens is not None else thinkdeeper_config['max_thinking_tokens'], 'max_thoughts': max_thoughts if max_thoughts is not None else thinkdeeper_config['max_thoughts'], 'thought_switch_tokens': thought_switch_tokens if thought_switch_tokens else thinkdeeper_config['thought_switch_tokens'], 'prefill': prefill if prefill else thinkdeeper_config['prefill'], 'start_think_token': start_think_token, 'end_think_token': end_think_token}
                    thinkdeeper_config.update(custom_config)
                    if isinstance(pipeline, MLXInferencePipeline):
                        logger.info('Using MLX ThinkDeeper implementation')
                        user_max_tokens = max_tokens if max_tokens is not None else 512
                        total_tokens_needed = max_thinking_tokens + 512
                        adjusted_max_tokens = max(user_max_tokens, total_tokens_needed)
                        thinkdeeper_config_with_tokens = thinkdeeper_config.copy()
                        thinkdeeper_config_with_tokens['max_tokens'] = adjusted_max_tokens
                        logger.debug(f'ThinkDeeper tokens: user={user_max_tokens}, thinking={max_thinking_tokens}, adjusted={adjusted_max_tokens}')
                        result, reasoning_tokens = thinkdeeper_decode_mlx(pipeline.model, pipeline.tokenizer, messages, thinkdeeper_config_with_tokens)
                    else:
                        logger.info('Using PyTorch ThinkDeeper implementation')
                        result, reasoning_tokens = thinkdeeper_decode(pipeline.current_model, pipeline.tokenizer, messages, thinkdeeper_config)
                    responses = [result]
                    logprobs_results = [None]
                    completion_tokens = len(pipeline.tokenizer.encode(result))
                elif decoding == 'autothink':
                    steering_dataset = kwargs.get('steering_dataset', 'codelion/Qwen3-0.6B-pts-steering-vectors')
                    target_layer = kwargs.get('target_layer', 19)
                    autothink_config = {'steering_dataset': steering_dataset, 'target_layer': target_layer, 'pattern_strengths': kwargs.get('pattern_strengths', {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5})}
                    result = autothink_decode(pipeline.current_model, pipeline.tokenizer, messages, autothink_config)
                    responses = [result]
                    logprobs_results = [None]
                    completion_tokens = len(pipeline.tokenizer.encode(result))
                elif decoding == 'deepconf':
                    deepconf_config = {'variant': kwargs.get('variant', 'low'), 'warmup_samples': kwargs.get('warmup_samples', 16), 'consensus_threshold': kwargs.get('consensus_threshold', 0.95), 'max_traces': kwargs.get('max_traces', 128), 'window_size': kwargs.get('window_size', 2048), 'top_k': kwargs.get('top_k', 5), 'min_trace_length': kwargs.get('min_trace_length', 100), 'max_tokens_per_trace': kwargs.get('max_tokens_per_trace', 4096), 'temperature': temperature, 'confidence_metric': kwargs.get('confidence_metric', 'average_confidence'), 'include_stats': kwargs.get('include_stats', False)}
                    result, tokens_used = deepconf_decode(pipeline.current_model, pipeline.tokenizer, messages, deepconf_config)
                    responses = [result]
                    logprobs_results = [None]
                    completion_tokens = tokens_used
                else:
                    raise ValueError(f'Unknown specialized decoding approach: {decoding}')
                prompt_text = pipeline.tokenizer.apply_chat_template(messages, tokenize=False)
                prompt_tokens = len(pipeline.tokenizer.encode(prompt_text))
            else:
                prompt = pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                generation_params = {'temperature': temperature, 'top_p': top_p, 'num_return_sequences': n, 'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'presence_penalty': presence_penalty, 'frequency_penalty': frequency_penalty, 'stop_sequences': [stop] if isinstance(stop, str) else stop, 'seed': seed, 'logit_bias': logit_bias, 'logprobs': logprobs, 'top_logprobs': top_logprobs}
                responses, token_counts, logprobs_results = pipeline.generate(prompt, generation_params=generation_params)
                prompt_tokens = len(pipeline.tokenizer.encode(prompt))
                completion_tokens = sum(token_counts)
            total_reasoning_tokens = 0
            for response in responses:
                total_reasoning_tokens += count_reasoning_tokens(response, pipeline.tokenizer)
            response_dict = {'id': f'chatcmpl-{int(time.time() * 1000)}', 'object': 'chat.completion', 'created': int(time.time()), 'model': model, 'choices': [{'index': idx, 'message': {'role': 'assistant', 'content': response, **({'logprobs': logprob_result} if logprob_result else {})}, 'finish_reason': 'stop'} for idx, (response, logprob_result) in enumerate(zip(responses, logprobs_results))], 'usage': {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': completion_tokens + prompt_tokens, 'reasoning_tokens': total_reasoning_tokens}}
            logger.debug(f'Response : {response_dict}')
            return ChatCompletion(response_dict)
        except Exception as e:
            logger.error(f'Error in chat completion: {str(e)}')
            raise

def create(self, messages: List[Dict[str, str]], model: str, temperature: float=1.0, top_p: float=1.0, n: int=1, stream: bool=False, stop: Optional[Union[str, List[str]]]=None, max_tokens: Optional[int]=None, presence_penalty: float=0, frequency_penalty: float=0, logit_bias: Optional[Dict[str, float]]=None, seed: Optional[int]=None, logprobs: Optional[bool]=None, top_logprobs: Optional[int]=None, active_adapter: Optional[Dict[str, Any]]=None, decoding: Optional[str]=None, k: int=10, num_beams: int=1, length_penalty: float=1.0, no_repeat_ngram_size: int=0, early_stopping: bool=False, aggregate_paths: bool=True, top_k: int=27, min_p: float=0.03, reasoning_effort: str='low', thought_switch_tokens: List[str]=[], min_thinking_tokens: Optional[int]=None, max_thinking_tokens: Optional[int]=None, max_thoughts: Optional[int]=None, prefill: str='', start_think_token: str='<think>', end_think_token: str='</think>', **kwargs) -> ChatCompletion:
    """Create a chat completion with OpenAI-compatible parameters"""
    logger.info('Starting chat completion creation')
    if stream:
        raise NotImplementedError('Streaming is not yet supported')
    logger.info(f'Getting pipeline for model: {model}')
    pipeline = self.client.get_pipeline(model)
    logger.info('Pipeline acquired')
    if active_adapter is not None:
        logger.info(f'Setting active adapter to: {active_adapter}')
        pipeline.lora_manager.set_active_adapter(pipeline.current_model, active_adapter)
    responses = []
    logprobs_results = []
    prompt_tokens = 0
    completion_tokens = 0
    try:
        if decoding:
            logger.info(f'Using specialized decoding approach: {decoding}')
            mlx_unsupported_decodings = ['cot_decoding', 'entropy_decoding', 'autothink', 'deepconf']
            if isinstance(pipeline, MLXInferencePipeline) and decoding in mlx_unsupported_decodings:
                logger.warning(f'{decoding} is not supported for MLX models. Falling back to standard generation.')
                decoding = None
        if decoding:
            if not isinstance(pipeline, MLXInferencePipeline):
                pipeline.current_model.eval()
                device = pipeline.current_model.device
            else:
                device = None
            if decoding == 'cot_decoding':
                cot_params = {'k': k, 'num_beams': num_beams, 'max_new_tokens': max_tokens if max_tokens is not None else 512, 'temperature': temperature, 'top_p': top_p, 'repetition_penalty': 1.0, 'length_penalty': length_penalty, 'no_repeat_ngram_size': no_repeat_ngram_size, 'early_stopping': early_stopping, 'aggregate_paths': aggregate_paths}
                result, confidence = cot_decode(pipeline.current_model, pipeline.tokenizer, messages, **cot_params)
                responses = [result]
                logprobs_results = [{'confidence_score': confidence} if confidence is not None else None]
                completion_tokens = len(pipeline.tokenizer.encode(result))
            elif decoding == 'entropy_decoding':
                original_dtype = pipeline.current_model.dtype
                pipeline.current_model = pipeline.current_model.to(torch.float32)
                try:
                    generator = None
                    if seed is not None:
                        generator = torch.Generator(device=device)
                        generator.manual_seed(seed)
                    else:
                        generator = torch.Generator(device=device)
                        generator.manual_seed(1337)
                    entropy_params = {'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'temperature': temperature, 'top_p': top_p, 'top_k': top_k, 'min_p': min_p, 'generator': generator}
                    with torch.amp.autocast('cuda', enabled=False), torch.inference_mode():
                        result = entropy_decode(pipeline.current_model, pipeline.tokenizer, messages, **entropy_params)
                    responses = [result]
                    logprobs_results = [None]
                    completion_tokens = len(pipeline.tokenizer.encode(result))
                finally:
                    pipeline.current_model = pipeline.current_model.to(original_dtype)
            elif decoding == 'thinkdeeper':
                thinkdeeper_config = get_effort_profile(reasoning_effort, max_tokens)
                custom_config = {'min_thinking_tokens': min_thinking_tokens if min_thinking_tokens is not None else thinkdeeper_config['min_thinking_tokens'], 'max_thinking_tokens': max_thinking_tokens if max_thinking_tokens is not None else thinkdeeper_config['max_thinking_tokens'], 'max_thoughts': max_thoughts if max_thoughts is not None else thinkdeeper_config['max_thoughts'], 'thought_switch_tokens': thought_switch_tokens if thought_switch_tokens else thinkdeeper_config['thought_switch_tokens'], 'prefill': prefill if prefill else thinkdeeper_config['prefill'], 'start_think_token': start_think_token, 'end_think_token': end_think_token}
                thinkdeeper_config.update(custom_config)
                if isinstance(pipeline, MLXInferencePipeline):
                    logger.info('Using MLX ThinkDeeper implementation')
                    user_max_tokens = max_tokens if max_tokens is not None else 512
                    total_tokens_needed = max_thinking_tokens + 512
                    adjusted_max_tokens = max(user_max_tokens, total_tokens_needed)
                    thinkdeeper_config_with_tokens = thinkdeeper_config.copy()
                    thinkdeeper_config_with_tokens['max_tokens'] = adjusted_max_tokens
                    logger.debug(f'ThinkDeeper tokens: user={user_max_tokens}, thinking={max_thinking_tokens}, adjusted={adjusted_max_tokens}')
                    result, reasoning_tokens = thinkdeeper_decode_mlx(pipeline.model, pipeline.tokenizer, messages, thinkdeeper_config_with_tokens)
                else:
                    logger.info('Using PyTorch ThinkDeeper implementation')
                    result, reasoning_tokens = thinkdeeper_decode(pipeline.current_model, pipeline.tokenizer, messages, thinkdeeper_config)
                responses = [result]
                logprobs_results = [None]
                completion_tokens = len(pipeline.tokenizer.encode(result))
            elif decoding == 'autothink':
                steering_dataset = kwargs.get('steering_dataset', 'codelion/Qwen3-0.6B-pts-steering-vectors')
                target_layer = kwargs.get('target_layer', 19)
                autothink_config = {'steering_dataset': steering_dataset, 'target_layer': target_layer, 'pattern_strengths': kwargs.get('pattern_strengths', {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5})}
                result = autothink_decode(pipeline.current_model, pipeline.tokenizer, messages, autothink_config)
                responses = [result]
                logprobs_results = [None]
                completion_tokens = len(pipeline.tokenizer.encode(result))
            elif decoding == 'deepconf':
                deepconf_config = {'variant': kwargs.get('variant', 'low'), 'warmup_samples': kwargs.get('warmup_samples', 16), 'consensus_threshold': kwargs.get('consensus_threshold', 0.95), 'max_traces': kwargs.get('max_traces', 128), 'window_size': kwargs.get('window_size', 2048), 'top_k': kwargs.get('top_k', 5), 'min_trace_length': kwargs.get('min_trace_length', 100), 'max_tokens_per_trace': kwargs.get('max_tokens_per_trace', 4096), 'temperature': temperature, 'confidence_metric': kwargs.get('confidence_metric', 'average_confidence'), 'include_stats': kwargs.get('include_stats', False)}
                result, tokens_used = deepconf_decode(pipeline.current_model, pipeline.tokenizer, messages, deepconf_config)
                responses = [result]
                logprobs_results = [None]
                completion_tokens = tokens_used
            else:
                raise ValueError(f'Unknown specialized decoding approach: {decoding}')
            prompt_text = pipeline.tokenizer.apply_chat_template(messages, tokenize=False)
            prompt_tokens = len(pipeline.tokenizer.encode(prompt_text))
        else:
            prompt = pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            generation_params = {'temperature': temperature, 'top_p': top_p, 'num_return_sequences': n, 'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'presence_penalty': presence_penalty, 'frequency_penalty': frequency_penalty, 'stop_sequences': [stop] if isinstance(stop, str) else stop, 'seed': seed, 'logit_bias': logit_bias, 'logprobs': logprobs, 'top_logprobs': top_logprobs}
            responses, token_counts, logprobs_results = pipeline.generate(prompt, generation_params=generation_params)
            prompt_tokens = len(pipeline.tokenizer.encode(prompt))
            completion_tokens = sum(token_counts)
        total_reasoning_tokens = 0
        for response in responses:
            total_reasoning_tokens += count_reasoning_tokens(response, pipeline.tokenizer)
        response_dict = {'id': f'chatcmpl-{int(time.time() * 1000)}', 'object': 'chat.completion', 'created': int(time.time()), 'model': model, 'choices': [{'index': idx, 'message': {'role': 'assistant', 'content': response, **({'logprobs': logprob_result} if logprob_result else {})}, 'finish_reason': 'stop'} for idx, (response, logprob_result) in enumerate(zip(responses, logprobs_results))], 'usage': {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': completion_tokens + prompt_tokens, 'reasoning_tokens': total_reasoning_tokens}}
        logger.debug(f'Response : {response_dict}')
        return ChatCompletion(response_dict)
    except Exception as e:
        logger.error(f'Error in chat completion: {str(e)}')
        raise

def get_device():
    if torch.backends.mps.is_available():
        return torch.device('mps')
    elif torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

def calculate_confidence(logits: List[torch.Tensor], answer_ids: torch.Tensor) -> float:
    """
    Calculate the confidence score (Δ) as specified in the paper.
    
    Args:
        logits: List of logits for each decoding step
        answer_ids: Tensor of token ids for the answer
    
    Returns:
        Confidence score (Δ)
    """
    confidence_sum = 0.0
    valid_tokens = 0
    for t, token_id in enumerate(answer_ids):
        if t >= len(logits):
            break
        token_logits = logits[t]
        probs = torch.softmax(token_logits, dim=-1)
        if probs.size(-1) > 1:
            top_2_probs, _ = torch.topk(probs, min(2, probs.size(-1)))
            if top_2_probs.size(-1) > 1:
                confidence_sum += (top_2_probs[-1][0] - top_2_probs[-1][1]).item()
            else:
                confidence_sum += 1.0
        else:
            confidence_sum += 1.0
        valid_tokens += 1
    return confidence_sum / valid_tokens if valid_tokens > 0 else 0.0

def cot_decode(model: PreTrainedModel, tokenizer: PreTrainedTokenizer, messages: List[Dict[str, str]], k: int=10, num_beams: int=1, max_new_tokens: int=512, temperature: float=1.0, top_p: float=1.0, repetition_penalty: float=1.0, length_penalty: float=1.0, no_repeat_ngram_size: int=0, early_stopping: bool=False, aggregate_paths: bool=False) -> Tuple[str, float]:
    """
    Implement CoT-decoding for a given chat input.
    
    Args:
        model: The Hugging Face transformer model.
        tokenizer: The associated tokenizer.
        messages: List of chat messages in the format [{"role": "user", "content": "..."}]
        k: The number of alternative tokens to consider at the first step.
        num_beams: Number of beams for beam search.
        max_new_tokens: Maximum number of new tokens to generate.
        temperature: Sampling temperature.
        top_p: Nucleus sampling probability.
        repetition_penalty: Repetition penalty factor.
        length_penalty: Length penalty factor.
        no_repeat_ngram_size: Size of n-grams to avoid repeating.
        early_stopping: Whether to stop generation when all beams are finished.
        aggregate_paths: Whether to aggregate multiple paths.

    Returns:
        A tuple containing the best path (or aggregated result) and its confidence score.
    """
    device = get_device()
    model.to(device)
    if tokenizer.chat_template:
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        input_text = '\n'.join([f'{msg['role']}: {msg['content']}' for msg in messages])
        input_text += '\nassistant:'
    input_ids = tokenizer.encode(input_text, return_tensors='pt').to(device)
    attention_mask = torch.ones_like(input_ids).to(device)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        first_token_logits = outputs.logits[0, -1, :]
        top_k_logits, top_k_indices = torch.topk(first_token_logits, k)
    paths = []
    for idx in top_k_indices:
        start_ids = torch.cat([input_ids, idx.unsqueeze(0).unsqueeze(0)], dim=-1)
        start_mask = torch.cat([attention_mask, torch.ones((1, 1), dtype=torch.long, device=device)], dim=-1)
        output = model.generate(start_ids, attention_mask=start_mask, max_new_tokens=max_new_tokens, num_beams=num_beams, temperature=temperature, top_p=top_p, repetition_penalty=repetition_penalty, length_penalty=length_penalty, no_repeat_ngram_size=no_repeat_ngram_size, early_stopping=early_stopping, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id, output_scores=True, return_dict_in_generate=True)
        generated_sequence = output.sequences[0]
        answer_ids = generated_sequence[len(input_ids[0]):]
        answer_text = tokenizer.decode(answer_ids, skip_special_tokens=True)
        confidence = calculate_confidence(output.scores, answer_ids)
        paths.append((answer_text, confidence))
    if aggregate_paths:
        return aggregate_paths_based_on_scores(paths)
    else:
        return max(paths, key=lambda x: x[1])

class MLXThinkDeeperProcessor:

    def __init__(self, config: Dict[str, Any], tokenizer, model):
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences)) if self.thought_switch_sequences else 5
        self.total_tokens_generated = 0
        self.max_total_tokens = config.get('max_tokens', 8192)

    def is_thought_switch(self, token: int) -> bool:
        """Check if adding this token creates a thought switch sequence."""
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    def reasoning_effort(self, messages) -> str:
        """Generate response with ThinkDeeper's controlled thinking process using MLX"""
        thinking_messages = messages.copy()
        thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
        if hasattr(self.tokenizer, 'apply_chat_template'):
            prompt = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=False, tokenize=False, add_generation_prompt=True)
        else:
            prompt = ''
            for msg in thinking_messages:
                prompt += f'{msg['role']}: {msg['content']}\n'
        n_thinking_tokens = 0
        seen_end_think = False
        response_chunks = []
        current_prompt = prompt
        max_chunk_size = 150
        consecutive_empty_chunks = 0
        max_empty_chunks = 3
        while n_thinking_tokens < self.config['max_thinking_tokens'] and self.thought_count < self.config['max_thoughts'] and (self.total_tokens_generated < self.max_total_tokens - 512):
            try:
                chunk_response = self._generate_chunk(current_prompt, max_tokens=min(max_chunk_size, self.config['max_thinking_tokens'] - n_thinking_tokens), temperature=0.6)
                if not chunk_response or chunk_response.strip() == '':
                    consecutive_empty_chunks += 1
                    if consecutive_empty_chunks >= max_empty_chunks:
                        break
                    max_chunk_size = min(max_chunk_size + 50, 300)
                    continue
                else:
                    consecutive_empty_chunks = 0
                    max_chunk_size = 150
                    chunk_tokens = len(self.tokenizer.encode(chunk_response))
                    self.total_tokens_generated += chunk_tokens
                if self.config['end_think_token'] in chunk_response:
                    parts = chunk_response.split(self.config['end_think_token'], 1)
                    before_end = parts[0]
                    after_end = parts[1] if len(parts) > 1 else ''
                    response_chunks.append(before_end)
                    n_thinking_tokens += len(self.tokenizer.encode(before_end))
                    if n_thinking_tokens < self.config['min_thinking_tokens']:
                        transition = random.choice(self.config['thought_switch_tokens'])
                        response_chunks.append(transition)
                        current_prompt += before_end + transition
                        n_thinking_tokens += len(self.tokenizer.encode(transition))
                        self.thought_count += 1
                        continue
                    else:
                        response_chunks.append(self.config['end_think_token'])
                        current_prompt += before_end + self.config['end_think_token']
                        seen_end_think = True
                        if after_end.strip():
                            response_chunks.append(after_end)
                        else:
                            conclusion = self._generate_chunk(current_prompt, max_tokens=200, temperature=0.3)
                            if conclusion:
                                response_chunks.append(conclusion)
                        break
                else:
                    response_chunks.append(chunk_response)
                    current_prompt += chunk_response
                    n_thinking_tokens += len(self.tokenizer.encode(chunk_response))
                    for phrase in self.config['thought_switch_tokens']:
                        if phrase in chunk_response:
                            self.thought_count += 1
                            break
                if len(response_chunks) > 100:
                    logger.warning('Too many chunks generated, stopping to avoid infinite loop')
                    break
            except Exception as e:
                logger.error(f'Error during MLX chunk generation: {str(e)}')
                break
        if not seen_end_think and n_thinking_tokens < self.config['min_thinking_tokens']:
            while n_thinking_tokens < self.config['min_thinking_tokens'] and self.thought_count < self.config['max_thoughts']:
                transition = random.choice(self.config['thought_switch_tokens'])
                response_chunks.append(f' {transition} ')
                current_prompt += f' {transition} '
                additional_thinking = self._generate_chunk(current_prompt, max_tokens=min(200, self.config['min_thinking_tokens'] - n_thinking_tokens + 100), temperature=0.6)
                if additional_thinking and additional_thinking.strip():
                    response_chunks.append(additional_thinking)
                    current_prompt += additional_thinking
                    additional_tokens = len(self.tokenizer.encode(additional_thinking))
                    n_thinking_tokens += additional_tokens
                    self.thought_count += 1
                else:
                    break
        if not seen_end_think:
            response_chunks.append(self.config['end_think_token'])
            try:
                conclusion = self._generate_chunk(current_prompt + self.config['end_think_token'], max_tokens=100, temperature=0.3)
                if conclusion:
                    response_chunks.append(conclusion)
            except Exception as e:
                logger.error(f'Error generating conclusion: {str(e)}')
        response_content = ''.join(response_chunks)
        full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response_content}'
        logger.debug(f'MLX Final response length: {len(full_response)} chars, Thinking tokens: {n_thinking_tokens}')
        return (full_response, n_thinking_tokens)

    def _generate_chunk(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate a small chunk of text using MLX with proper sampler"""
        try:
            sampler = make_sampler(temp=temperature, top_p=0.95, top_k=20, min_p=0.0, min_tokens_to_keep=3)
            actual_max_tokens = max(max_tokens, 30)
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=actual_max_tokens, sampler=sampler, verbose=False)
            if response:
                if response.startswith(prompt):
                    new_content = response[len(prompt):]
                else:
                    new_content = response
                if new_content.strip():
                    return new_content
            return ''
        except Exception as e:
            logger.error(f'Error in MLX chunk generation: {str(e)}')
            return ''

def __init__(self, config: Dict[str, Any], tokenizer, model):
    self.config = {**DEFAULT_CONFIG, **config}
    self.tokenizer = tokenizer
    self.model = model
    start_tokens = self.tokenizer.encode(self.config['start_think_token'])
    end_tokens = self.tokenizer.encode(self.config['end_think_token'])
    self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
    self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
    self.thought_switch_sequences = []
    for phrase in self.config['thought_switch_tokens']:
        token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
        self.thought_switch_sequences.append(token_ids)
    self.thought_count = 0
    self.current_sequence = []
    self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences)) if self.thought_switch_sequences else 5
    self.total_tokens_generated = 0
    self.max_total_tokens = config.get('max_tokens', 8192)

def reasoning_effort(self, messages) -> str:
    """Generate response with ThinkDeeper's controlled thinking process using MLX"""
    thinking_messages = messages.copy()
    thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
    if hasattr(self.tokenizer, 'apply_chat_template'):
        prompt = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=False, tokenize=False, add_generation_prompt=True)
    else:
        prompt = ''
        for msg in thinking_messages:
            prompt += f'{msg['role']}: {msg['content']}\n'
    n_thinking_tokens = 0
    seen_end_think = False
    response_chunks = []
    current_prompt = prompt
    max_chunk_size = 150
    consecutive_empty_chunks = 0
    max_empty_chunks = 3
    while n_thinking_tokens < self.config['max_thinking_tokens'] and self.thought_count < self.config['max_thoughts'] and (self.total_tokens_generated < self.max_total_tokens - 512):
        try:
            chunk_response = self._generate_chunk(current_prompt, max_tokens=min(max_chunk_size, self.config['max_thinking_tokens'] - n_thinking_tokens), temperature=0.6)
            if not chunk_response or chunk_response.strip() == '':
                consecutive_empty_chunks += 1
                if consecutive_empty_chunks >= max_empty_chunks:
                    break
                max_chunk_size = min(max_chunk_size + 50, 300)
                continue
            else:
                consecutive_empty_chunks = 0
                max_chunk_size = 150
                chunk_tokens = len(self.tokenizer.encode(chunk_response))
                self.total_tokens_generated += chunk_tokens
            if self.config['end_think_token'] in chunk_response:
                parts = chunk_response.split(self.config['end_think_token'], 1)
                before_end = parts[0]
                after_end = parts[1] if len(parts) > 1 else ''
                response_chunks.append(before_end)
                n_thinking_tokens += len(self.tokenizer.encode(before_end))
                if n_thinking_tokens < self.config['min_thinking_tokens']:
                    transition = random.choice(self.config['thought_switch_tokens'])
                    response_chunks.append(transition)
                    current_prompt += before_end + transition
                    n_thinking_tokens += len(self.tokenizer.encode(transition))
                    self.thought_count += 1
                    continue
                else:
                    response_chunks.append(self.config['end_think_token'])
                    current_prompt += before_end + self.config['end_think_token']
                    seen_end_think = True
                    if after_end.strip():
                        response_chunks.append(after_end)
                    else:
                        conclusion = self._generate_chunk(current_prompt, max_tokens=200, temperature=0.3)
                        if conclusion:
                            response_chunks.append(conclusion)
                    break
            else:
                response_chunks.append(chunk_response)
                current_prompt += chunk_response
                n_thinking_tokens += len(self.tokenizer.encode(chunk_response))
                for phrase in self.config['thought_switch_tokens']:
                    if phrase in chunk_response:
                        self.thought_count += 1
                        break
            if len(response_chunks) > 100:
                logger.warning('Too many chunks generated, stopping to avoid infinite loop')
                break
        except Exception as e:
            logger.error(f'Error during MLX chunk generation: {str(e)}')
            break
    if not seen_end_think and n_thinking_tokens < self.config['min_thinking_tokens']:
        while n_thinking_tokens < self.config['min_thinking_tokens'] and self.thought_count < self.config['max_thoughts']:
            transition = random.choice(self.config['thought_switch_tokens'])
            response_chunks.append(f' {transition} ')
            current_prompt += f' {transition} '
            additional_thinking = self._generate_chunk(current_prompt, max_tokens=min(200, self.config['min_thinking_tokens'] - n_thinking_tokens + 100), temperature=0.6)
            if additional_thinking and additional_thinking.strip():
                response_chunks.append(additional_thinking)
                current_prompt += additional_thinking
                additional_tokens = len(self.tokenizer.encode(additional_thinking))
                n_thinking_tokens += additional_tokens
                self.thought_count += 1
            else:
                break
    if not seen_end_think:
        response_chunks.append(self.config['end_think_token'])
        try:
            conclusion = self._generate_chunk(current_prompt + self.config['end_think_token'], max_tokens=100, temperature=0.3)
            if conclusion:
                response_chunks.append(conclusion)
        except Exception as e:
            logger.error(f'Error generating conclusion: {str(e)}')
    response_content = ''.join(response_chunks)
    full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response_content}'
    logger.debug(f'MLX Final response length: {len(full_response)} chars, Thinking tokens: {n_thinking_tokens}')
    return (full_response, n_thinking_tokens)

def calculate_varentropy_logsoftmax(logits: torch.Tensor, axis: int=-1) -> Tuple[torch.Tensor, torch.Tensor]:
    log_probs = F.log_softmax(logits, dim=axis)
    probs = torch.exp(log_probs)
    entropy = -torch.sum(probs * log_probs, dim=axis) / LN_2
    varentropy = torch.sum(probs * (log_probs / LN_2 + entropy.unsqueeze(-1)) ** 2, dim=axis)
    return (entropy, varentropy)

def _sample(logits: torch.Tensor, temperature=0.666, top_p=0.9, top_k=27, min_p: float=0.0, generator: torch.Generator=None) -> torch.Tensor:
    bsz = logits.shape[0]
    logit = logits[:, -1]
    probs = F.softmax(logit / temperature, dim=-1)
    if min_p > 0.0:
        p_max = torch.max(probs, dim=-1, keepdim=True).values
        indices_to_remove = probs < min_p * p_max
        logit = torch.where(indices_to_remove, torch.full_like(logit, float('-inf')), logit)
    top_k_probs, top_k_indices = torch.topk(probs, k=min(top_k, probs.shape[-1]))
    probs_sort = torch.flip(top_k_probs, dims=[-1])
    probs_idx = torch.flip(top_k_indices, dims=[-1])
    probs_sum = torch.cumsum(probs_sort, dim=-1)
    mask = torch.where(probs_sum - probs_sort > top_p, torch.tensor(1.0, device=device), torch.tensor(0.0, device=device))
    probs_sort = probs_sort * (1 - mask)
    probs_sort = probs_sort / torch.sum(probs_sort, dim=-1, keepdim=True)
    next_token = torch.multinomial(probs_sort, 1, generator=generator)
    next_token_g = torch.gather(probs_idx, -1, next_token.reshape(bsz, 1).to(torch.int64))
    return next_token_g.to(torch.int32)

def adaptive_sample(logits: torch.Tensor, metrics: Dict[str, torch.Tensor], gen_tokens: torch.Tensor, n_samples: int, base_temp: float=0.666, base_top_p: float=0.9, base_top_k: int=40, base_min_p: float=0.03, generator: torch.Generator=None) -> torch.Tensor:
    logits_uncertainty = metrics['logits_entropy'] + metrics['logits_varentropy']
    attn_uncertainty = metrics['attn_entropy'] + metrics['attn_varentropy']
    temperature = base_temp * (1 + 0.3 * logits_uncertainty + 0.2 * attn_uncertainty - 0.2 * metrics['agreement'])
    top_p = torch.clamp(base_top_p * (1 + 0.1 * metrics['attn_varentropy']), 0.1, 1.0)
    top_k = int(torch.clamp(torch.round(torch.tensor(base_top_k) * (1 + 0.3 * metrics['interaction_strength'].item() - 0.2 * metrics['agreement'].item())), min=1, max=100).item())
    min_p = torch.clamp(base_min_p * (1 - 0.5 * logits_uncertainty), 0.01, 0.5)
    logging.debug(f'Adaptive sampling params: temp={temperature.item():.3f}, top_p={top_p.item():.3f}, top_k={top_k}, min_p={min_p.item():.3f}')
    samples = []
    for _ in range(n_samples):
        sample = _sample(logits, temperature=temperature.item(), top_p=top_p.item(), top_k=top_k, min_p=min_p.item(), generator=generator)
        samples.append(sample)

    def score_sample(sample):
        sample_flat = sample.flatten().to(torch.long)
        one_hot = F.one_hot(sample_flat, logits.shape[-1])
        log_probs = F.log_softmax(logits, dim=-1).view(-1, logits.shape[-1])
        log_prob = torch.sum(log_probs * one_hot)
        confidence_score = (1 - metrics['logits_entropy']) * 0.1 + (1 - metrics['attn_entropy']) * 0.2 + (1 - metrics['logits_varentropy']) * 0.3 + (1 - metrics['attn_varentropy']) * 0.4 + metrics['agreement'] * 0.5 + metrics['interaction_strength'] * 0.6
        return log_prob + confidence_score
    sample_scores = torch.stack([score_sample(sample) for sample in samples])
    best_sample_idx = torch.argmax(sample_scores)
    return samples[best_sample_idx]

def score_sample(sample):
    sample_flat = sample.flatten().to(torch.long)
    one_hot = F.one_hot(sample_flat, logits.shape[-1])
    log_probs = F.log_softmax(logits, dim=-1).view(-1, logits.shape[-1])
    log_prob = torch.sum(log_probs * one_hot)
    confidence_score = (1 - metrics['logits_entropy']) * 0.1 + (1 - metrics['attn_entropy']) * 0.2 + (1 - metrics['logits_varentropy']) * 0.3 + (1 - metrics['attn_varentropy']) * 0.4 + metrics['agreement'] * 0.5 + metrics['interaction_strength'] * 0.6
    return log_prob + confidence_score

def entropy_decode(model: PreTrainedModel, tokenizer: PreTrainedTokenizer, messages: List[Dict[str, str]], max_new_tokens: int=512, temperature: float=0.666, top_p: float=0.9, top_k: int=27, min_p: float=0.03, generator: torch.Generator=torch.Generator(device=device).manual_seed(1337)) -> str:
    model.to(device)
    logging.info('Starting entropy decoding')
    if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        input_text = '\n'.join([f'{msg['role']}: {msg['content']}' for msg in messages])
        input_text += '\nassistant:'
    input_ids = tokenizer.encode(input_text, return_tensors='pt').to(device)
    attention_mask = torch.ones_like(input_ids).to(device)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    generated_tokens = []
    gen_tokens = input_ids
    past_key_values = None
    stop = torch.tensor([tokenizer.eos_token_id], device=device, dtype=torch.int32)
    for step in range(max_new_tokens):
        logging.debug(f'Generation step: {step + 1}')
        with torch.no_grad():
            outputs = model(input_ids if past_key_values is None else input_ids[:, -1:], attention_mask=attention_mask, past_key_values=past_key_values, use_cache=True, output_attentions=True)
        logits = outputs.logits[:, -1:, :]
        attention_scores = outputs.attentions[-1]
        past_key_values = outputs.past_key_values
        entropy, varentropy = calculate_varentropy_logsoftmax(logits)
        attention_metrics = calculate_attention_metrics(attention_scores)
        metrics = {'logits_entropy': entropy, 'logits_varentropy': varentropy, **attention_metrics}
        logging.debug(f'Metrics: entropy={entropy.item():.3f}, varentropy={varentropy.item():.3f}')
        if entropy < 0.1 and varentropy < 0.1:
            next_token = torch.argmax(logits[:, -1], dim=-1, keepdim=True).to(torch.int32)
            logging.debug('Using greedy sampling')
        elif entropy > 3.0 and varentropy < 0.1:
            if not torch.isin(gen_tokens[:, -1], torch.tensor([2564], device=device)).any():
                next_token = torch.tensor([[2564]], dtype=torch.int32, device=device)
                logging.debug('Inserting clarification token')
            else:
                temp_adj = 1.3 + 0.2 * attention_metrics['attn_entropy'].item()
                next_token = _sample(logits, temperature=min(1.5, temperature * temp_adj), top_p=top_p, top_k=top_k, min_p=min_p, generator=generator)
                logging.debug(f'Using adjusted temperature sampling: {temp_adj:.3f}')
        elif entropy < 5.0 and varentropy > 5.0:
            temp_adj = 1.2 + 0.3 * attention_metrics['interaction_strength'].item()
            top_k_adj = max(5, int(top_k * (1 + 0.5 * (1 - attention_metrics['agreement'].item()))))
            next_token = _sample(logits, temperature=min(1.5, temperature * temp_adj), top_p=top_p, top_k=top_k_adj, min_p=min_p, generator=generator)
            logging.debug(f'Using exploration sampling: temp={temp_adj:.3f}, top_k={top_k_adj}')
        elif entropy > 5.0 and varentropy > 5.0:
            temp_adj = 2.0 + 0.5 * attention_metrics['attn_varentropy'].item()
            top_p_adj = max(0.5, top_p - 0.2 * attention_metrics['attn_entropy'].item())
            next_token = _sample(logits, temperature=max(2.0, temperature * temp_adj), top_p=top_p_adj, top_k=top_k, min_p=min_p, generator=generator)
            logging.debug(f'Using high uncertainty sampling: temp={temp_adj:.3f}, top_p={top_p_adj:.3f}')
        else:
            next_token = adaptive_sample(logits, metrics, gen_tokens, n_samples=5, base_temp=temperature, base_top_p=top_p, base_top_k=top_k, base_min_p=min_p, generator=generator)
            logging.debug('Using adaptive sampling')
        generated_tokens.append(next_token.item())
        gen_tokens = torch.cat((gen_tokens, next_token), dim=1)
        input_ids = torch.cat([input_ids, next_token], dim=-1)
        attention_mask = torch.cat([attention_mask, torch.ones((1, 1), device=device, dtype=torch.long)], dim=-1)
        logging.debug(f'Generated token: {tokenizer.decode([next_token.item()])}')
        if torch.isin(next_token, stop).any():
            logging.info('Reached stop token. Ending generation.')
            break
    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    logging.info('Finished entropy decoding')
    logging.info(f'Generated text: {generated_text}')
    return generated_text

class OptILMClassifier(nn.Module):

    def __init__(self, base_model, num_labels):
        super().__init__()
        self.base_model = base_model
        self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

    def forward(self, input_ids, attention_mask, effort):
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0]
        effort_encoded = self.effort_encoder(effort.unsqueeze(1))
        combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
        logits = self.classifier(combined_input)
        return logits

def forward(self, input_ids, attention_mask, effort):
    outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
    pooled_output = outputs.last_hidden_state[:, 0]
    effort_encoded = self.effort_encoder(effort.unsqueeze(1))
    combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
    logits = self.classifier(combined_input)
    return logits

def load_optillm_model():
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
    base_model = AutoModel.from_pretrained(BASE_MODEL)
    model = OptILMClassifier(base_model, num_labels=len(APPROACHES))
    model.to(device)
    safetensors_path = hf_hub_download(repo_id=OPTILLM_MODEL_NAME, filename='model.safetensors')
    load_model(model, safetensors_path)
    tokenizer = AutoTokenizer.from_pretrained(OPTILLM_MODEL_NAME)
    return (model, tokenizer, device)

def preprocess_input(tokenizer, system_prompt, initial_query):
    combined_input = f'{system_prompt}\n\nUser: {initial_query}'
    encoding = tokenizer.encode_plus(combined_input, add_special_tokens=True, max_length=MAX_LENGTH, padding='max_length', truncation=True, return_attention_mask=True, return_tensors='pt')
    return (encoding['input_ids'], encoding['attention_mask'])

def predict_approach(model, input_ids, attention_mask, device, effort=0.7):
    model.eval()
    with torch.no_grad():
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        effort_tensor = torch.tensor([effort], dtype=torch.float).to(device)
        logits = model(input_ids, attention_mask=attention_mask, effort=effort_tensor)
        probabilities = F.softmax(logits, dim=1)
        predicted_approach_index = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][predicted_approach_index].item()
    return (APPROACHES[predicted_approach_index], confidence)

class JSONGenerator:

    def get_device(self):
        """Get the appropriate device (mps, cuda, or cpu)."""
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')

    def __init__(self, model_name: str='google/gemma-3-270m-it'):
        """Initialize the JSON generator with a specific model."""
        self.device = self.get_device()
        logger.info(f'Using device: {self.device}')
        try:
            hf_model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto' if str(self.device) != 'cpu' else None, torch_dtype=torch.float16 if str(self.device) != 'cpu' else torch.float32)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = outlines.from_transformers(hf_model, self.tokenizer)
            logger.info(f'Successfully loaded model: {model_name}')
        except Exception as e:
            logger.error(f'Error loading model: {str(e)}')
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f'Error counting tokens: {str(e)}')
            return 0

    def parse_json_schema_to_pydantic(self, schema_str: str) -> type[BaseModel]:
        """Convert JSON schema string to Pydantic model."""
        try:
            schema_dict = json.loads(schema_str)
            properties = schema_dict.get('properties', {})
            required = schema_dict.get('required', [])
            fields = {}
            for field_name, field_def in properties.items():
                field_type = str
                if field_def.get('type') == 'integer':
                    field_type = int
                elif field_def.get('type') == 'number':
                    field_type = float
                elif field_def.get('type') == 'boolean':
                    field_type = bool
                elif field_def.get('type') == 'array':
                    field_type = list
                elif field_def.get('type') == 'object':
                    field_type = dict
                if field_name in required:
                    fields[field_name] = (field_type, ...)
                else:
                    fields[field_name] = (Optional[field_type], None)
            return create_model('DynamicModel', **fields)
        except Exception as e:
            logger.error(f'Error parsing JSON schema: {str(e)}')
            raise

    def generate_json(self, prompt: str, schema: str) -> Dict[str, Any]:
        """Generate JSON based on the provided schema and prompt."""
        try:
            pydantic_model = self.parse_json_schema_to_pydantic(schema)
            logger.info('Parsed JSON schema to Pydantic model')
            result = self.model(prompt, pydantic_model)
            logger.info('Successfully generated JSON response')
            if hasattr(result, 'model_dump'):
                return result.model_dump()
            elif hasattr(result, 'dict'):
                return result.dict()
            else:
                return dict(result)
        except Exception as e:
            logger.error(f'Error generating JSON: {str(e)}')
            raise

def get_device(self):
    """Get the appropriate device (mps, cuda, or cpu)."""
    if torch.backends.mps.is_available():
        return torch.device('mps')
    elif torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

class WeightedRouter(Router):
    """Weighted random routing strategy"""

    def __init__(self, providers: List):
        self.providers = providers

    def select(self, providers: List) -> Optional:
        if not providers:
            return None
        weights = [p.weight for p in providers]
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(providers)
        rand = random.uniform(0, total_weight)
        cumulative = 0
        for provider, weight in zip(providers, weights):
            cumulative += weight
            if rand <= cumulative:
                return provider
        return providers[-1]

def select(self, providers: List) -> Optional:
    if not providers:
        return None
    weights = [p.weight for p in providers]
    total_weight = sum(weights)
    if total_weight == 0:
        return random.choice(providers)
    rand = random.uniform(0, total_weight)
    cumulative = 0
    for provider, weight in zip(providers, weights):
        cumulative += weight
        if rand <= cumulative:
            return provider
    return providers[-1]

def get_prompt_length(prompt: str, tokenizer, no_special_tokens=False, **kwargs) -> int:
    """
    Returns the token length of a prompt using the given tokenizer.
    """
    if isinstance(prompt, list):
        prompt = '\n\n'.join(prompt)
    if no_special_tokens:
        kwargs['add_special_tokens'] = False
    return len(tokenizer.encode(prompt, **kwargs))

def split_sentences(text: str, spliter: str):
    """
    Splits text into sentences or segments based on a given delimiter while preserving punctuation.

    For punctuation-based splitters (e.g., ".", "!", "。"), it interleaves text and punctuation.
    For space-based splitting, it preserves trailing spaces.

    Args:
        text (str): The input text to split.
        spliter (str): Delimiter regex pattern (e.g., r"([.!?])", r"(。)", or " ").

    Returns:
        List[str]: List of split sentence-like segments with punctuation retained.
    """
    text = text.strip()
    sentence_list = re.split(spliter, text)
    if spliter != ' ':
        sentences = [''.join(i) for i in zip(sentence_list[0::2], sentence_list[1::2])]
        if len(sentence_list) % 2 != 0 and sentence_list[-1] != '':
            sentences.append(sentence_list[-1])
    else:
        sentences = [i + ' ' for i in sentence_list if i != '']
        sentences[-1] = sentences[-1].strip()
    return sentences

class AutoThinkProcessor:
    """
    AutoThink processor for controlled thinking with 
    complexity classification and steering vectors.
    """

    def __init__(self, config: Dict[str, Any], tokenizer: PreTrainedTokenizer, model: PreTrainedModel):
        """
        Initialize the AutoThink processor.
        
        Args:
            config: Configuration dictionary
            tokenizer: Model tokenizer
            model: Language model
        """
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        self.classifier = ComplexityClassifier(self.config['classifier_model'])
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
            logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
            logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
        self.steering_manager = None
        self.steering_hooks = []
        if self.config['steering_dataset']:
            self._setup_steering()

    def _setup_steering(self):
        """Set up steering vector management."""
        try:
            self.steering_manager = SteeringVectorManager(dataset_name=self.config['steering_dataset'], target_layer=self.config['target_layer'])
            if 'pattern_strengths' in self.config:
                for pattern, strength in self.config['pattern_strengths'].items():
                    self.steering_manager.set_steering_strength(pattern, strength)
            self.steering_manager.create_tokenized_contexts(self.tokenizer)
            self.steering_hooks = install_steering_hooks(self.model, self.steering_manager, self.tokenizer)
            logger.info(f'STEERING: Set up steering with {len(self.steering_hooks)} hooks')
        except Exception as e:
            logger.error(f'STEERING: Error setting up steering: {e}')
            self.steering_manager = None
            self.steering_hooks = []

    def _cleanup_steering(self):
        """Clean up steering hooks."""
        if self.steering_hooks:
            remove_steering_hooks(self.steering_hooks)
            self.steering_hooks = []
            logger.info('STEERING: Hooks removed successfully')

    def classify_complexity(self, query: str) -> Tuple[str, float]:
        """
        Classify query complexity.
        
        Args:
            query: The query to classify
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
        complexity, confidence = self.classifier.get_complexity_with_confidence(query)
        logger.info(f'Query classified as {complexity} with confidence {confidence:.2f}')
        return (complexity, confidence)

    def get_token_budget(self, complexity: str) -> Tuple[int, int]:
        """
        Get token budget based on complexity.
        
        Args:
            complexity: Complexity label (HIGH or LOW)
            
        Returns:
            Tuple of (min_tokens, max_tokens)
        """
        if complexity == 'HIGH':
            return (self.config['high_complexity_min_tokens'], self.config['high_complexity_max_tokens'])
        else:
            return (self.config['low_complexity_min_tokens'], self.config['low_complexity_max_tokens'])

    def is_thought_switch(self, token: int) -> bool:
        """
        Check if adding this token creates a thought switch sequence.
        
        Args:
            token: Token ID to check
            
        Returns:
            Boolean indicating if this completes a thought switch
        """
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    @torch.inference_mode()
    def process(self, messages: List[Dict[str, str]]) -> str:
        """
        Process messages with AutoThink's controlled thinking.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response
        """
        try:
            query = self._extract_query(messages)
            complexity, confidence = self.classify_complexity(query)
            min_tokens, max_tokens = self.get_token_budget(complexity)
            logger.info(f'Using token budget: {min_tokens}-{max_tokens} for {complexity} complexity')
            thinking_messages = messages.copy()
            thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
            tokens = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=True, return_tensors='pt').to(self.model.device)
            if self.steering_hooks:
                token_ids = tokens[0].tolist()
                prompt_text = self.tokenizer.decode(token_ids)
                for hook, _ in self.steering_hooks:
                    hook.reset()
                    hook.update_token_history(token_ids)
                    hook.update_context(prompt_text)
                    hook.try_match()
            kv = DynamicCache()
            n_thinking_tokens = 0
            seen_end_think = False
            response_chunks = []
            while True:
                out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
                logits = out.logits[0, -1, :]
                force_end = n_thinking_tokens >= max_tokens or self.thought_count >= self.config['max_thoughts']
                if force_end and (not seen_end_think):
                    logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                    next_token = self.end_think_token
                    response_chunks.append(self.tokenizer.decode([next_token]))
                    seen_end_think = True
                    tokens = torch.tensor([[next_token]]).to(tokens.device)
                    continue
                else:
                    next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
                kv = out.past_key_values
                next_str = self.tokenizer.decode([next_token])
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                if not seen_end_think and self.is_thought_switch(next_token):
                    self.thought_count += 1
                    logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                    self.current_sequence = []
                if next_token == self.end_think_token:
                    seen_end_think = True
                    logger.debug('Found end think token')
                    if n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        seen_end_think = False
                        continue
                if next_token == self.model.config.eos_token_id:
                    logger.debug('Found EOS token')
                    if seen_end_think:
                        logger.debug('Reached EOS after end think token - stopping generation')
                        response_chunks.append(next_str)
                        break
                    elif n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        continue
                    else:
                        logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                        response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                        tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                        seen_end_think = True
                        continue
                response_chunks.append(next_str)
                if not seen_end_think:
                    n_thinking_tokens += 1
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                        hook.update_context(next_str)
                        hook.try_match()
                tokens = torch.tensor([[next_token]]).to(tokens.device)
            if self.steering_hooks:
                for hook, _ in self.steering_hooks:
                    hook.reset()
            self._cleanup_steering()
            response = ''.join(response_chunks)
            full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
            logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}')
            return full_response
        except Exception as e:
            self._cleanup_steering()
            logger.error(f'Error in AutoThink processing: {str(e)}')
            raise

    def _extract_query(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract the query from messages for classification.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Extracted query string
        """
        user_messages = [m['content'] for m in messages if m['role'] == 'user']
        if user_messages:
            return user_messages[-1]
        return ' '.join((m['content'] for m in messages))

def __init__(self, config: Dict[str, Any], tokenizer: PreTrainedTokenizer, model: PreTrainedModel):
    """
        Initialize the AutoThink processor.
        
        Args:
            config: Configuration dictionary
            tokenizer: Model tokenizer
            model: Language model
        """
    self.config = {**DEFAULT_CONFIG, **config}
    self.tokenizer = tokenizer
    self.model = model
    self.classifier = ComplexityClassifier(self.config['classifier_model'])
    start_tokens = self.tokenizer.encode(self.config['start_think_token'])
    end_tokens = self.tokenizer.encode(self.config['end_think_token'])
    self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
    self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
    self.thought_switch_sequences = []
    for phrase in self.config['thought_switch_tokens']:
        token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
        self.thought_switch_sequences.append(token_ids)
        logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
        logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
    self.thought_count = 0
    self.current_sequence = []
    self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
    self.steering_manager = None
    self.steering_hooks = []
    if self.config['steering_dataset']:
        self._setup_steering()

@torch.inference_mode()
def process(self, messages: List[Dict[str, str]]) -> str:
    """
        Process messages with AutoThink's controlled thinking.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response
        """
    try:
        query = self._extract_query(messages)
        complexity, confidence = self.classify_complexity(query)
        min_tokens, max_tokens = self.get_token_budget(complexity)
        logger.info(f'Using token budget: {min_tokens}-{max_tokens} for {complexity} complexity')
        thinking_messages = messages.copy()
        thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
        tokens = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=True, return_tensors='pt').to(self.model.device)
        if self.steering_hooks:
            token_ids = tokens[0].tolist()
            prompt_text = self.tokenizer.decode(token_ids)
            for hook, _ in self.steering_hooks:
                hook.reset()
                hook.update_token_history(token_ids)
                hook.update_context(prompt_text)
                hook.try_match()
        kv = DynamicCache()
        n_thinking_tokens = 0
        seen_end_think = False
        response_chunks = []
        while True:
            out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
            logits = out.logits[0, -1, :]
            force_end = n_thinking_tokens >= max_tokens or self.thought_count >= self.config['max_thoughts']
            if force_end and (not seen_end_think):
                logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                next_token = self.end_think_token
                response_chunks.append(self.tokenizer.decode([next_token]))
                seen_end_think = True
                tokens = torch.tensor([[next_token]]).to(tokens.device)
                continue
            else:
                next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
            kv = out.past_key_values
            next_str = self.tokenizer.decode([next_token])
            if self.steering_hooks:
                for hook, _ in self.steering_hooks:
                    hook.update_token_history([next_token])
            if not seen_end_think and self.is_thought_switch(next_token):
                self.thought_count += 1
                logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                self.current_sequence = []
            if next_token == self.end_think_token:
                seen_end_think = True
                logger.debug('Found end think token')
                if n_thinking_tokens < min_tokens:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    seen_end_think = False
                    continue
            if next_token == self.model.config.eos_token_id:
                logger.debug('Found EOS token')
                if seen_end_think:
                    logger.debug('Reached EOS after end think token - stopping generation')
                    response_chunks.append(next_str)
                    break
                elif n_thinking_tokens < min_tokens:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    continue
                else:
                    logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                    response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                    tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                    seen_end_think = True
                    continue
            response_chunks.append(next_str)
            if not seen_end_think:
                n_thinking_tokens += 1
            if self.steering_hooks:
                for hook, _ in self.steering_hooks:
                    hook.update_token_history([next_token])
                    hook.update_context(next_str)
                    hook.try_match()
            tokens = torch.tensor([[next_token]]).to(tokens.device)
        if self.steering_hooks:
            for hook, _ in self.steering_hooks:
                hook.reset()
        self._cleanup_steering()
        response = ''.join(response_chunks)
        full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
        logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}')
        return full_response
    except Exception as e:
        self._cleanup_steering()
        logger.error(f'Error in AutoThink processing: {str(e)}')
        raise

class SteeringVectorManager:
    """
    Manager for loading and applying steering vectors from a dataset.
    """

    def __init__(self, dataset_name: str, target_layer: int=19, cache_dir: Optional[str]=None, device: Optional[str]=None):
        """
        Initialize the steering vector manager.
        
        Args:
            dataset_name: Name of the HuggingFace dataset containing steering vectors
            target_layer: Target layer for applying steering vectors
            cache_dir: Directory for caching the dataset
            device: Device to use for tensors
        """
        self.dataset_name = dataset_name
        self.target_layer = target_layer
        self.cache_dir = cache_dir
        self.device = device or ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        self.steering_vectors = []
        self.pattern_to_vectors = {}
        self.tokenized_contexts = {}
        self.default_strength = 2.0
        self.pattern_strengths = {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5, 'unknown': 1.0}
        if dataset_name:
            self.load_dataset()

    def load_dataset(self):
        """Load steering vectors from the HuggingFace dataset."""
        try:
            logger.info(f'Loading steering vectors from dataset: {self.dataset_name}')
            dataset = datasets.load_dataset(self.dataset_name, cache_dir=self.cache_dir)
            main_split = list(dataset.keys())[0]
            vector_data = dataset[main_split]
            for item in vector_data:
                vector = self._process_dataset_item(item)
                if vector:
                    self.steering_vectors.append(vector)
                    pattern = vector.get('reasoning_pattern', 'unknown')
                    if pattern not in self.pattern_to_vectors:
                        self.pattern_to_vectors[pattern] = []
                    self.pattern_to_vectors[pattern].append(vector)
            logger.info(f'Loaded {len(self.steering_vectors)} steering vectors')
            logger.info(f'Found {len(self.pattern_to_vectors)} reasoning patterns: {list(self.pattern_to_vectors.keys())}')
            if self.steering_vectors:
                first_vector = self.steering_vectors[0]
                logger.info(f'First vector sample - pattern: {first_vector.get('reasoning_pattern', 'missing')}')
                if 'pivot_context' in first_vector:
                    context_len = len(first_vector['pivot_context'])
                    logger.info(f'First vector pivot_context length: {context_len}')
        except Exception as e:
            logger.error(f'Error loading steering vectors: {e}')
            self.steering_vectors = []
            self.pattern_to_vectors = {}

    def _process_dataset_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dataset item into a steering vector.
        
        Args:
            item: Dataset item
            
        Returns:
            Processed steering vector or None if invalid
        """
        try:
            required_fields = ['pivot_context', 'steering_vector', 'reasoning_pattern']
            if not all((field in item for field in required_fields)):
                return None
            steering_vector = item['steering_vector']
            if isinstance(steering_vector, str):
                try:
                    steering_vector = json.loads(steering_vector)
                except json.JSONDecodeError:
                    steering_vector = [float(x) for x in steering_vector.strip('[]').split(',')]
            if not isinstance(steering_vector, list):
                logger.warning(f'Invalid steering vector format: {type(steering_vector)}')
                return None
            vector = {'pivot_context': item['pivot_context'], 'pivot_token': item.get('pivot_token', ''), 'pivot_token_id': item.get('pivot_token_id', -1), 'prob_before': item.get('prob_before', 0.0), 'prob_after': item.get('prob_after', 0.0), 'prob_delta': item.get('prob_delta', 0.0), 'model_id': item.get('model_id', ''), 'task_type': item.get('task_type', 'unknown'), 'steering_vector': steering_vector, 'cluster_id': item.get('cluster_id', -1), 'reasoning_pattern': item.get('reasoning_pattern', 'unknown'), 'cluster_vector': item.get('cluster_vector', steering_vector), 'steering_layer': item.get('steering_layer', self.target_layer)}
            return vector
        except Exception as e:
            logger.error(f'Error processing dataset item: {e}')
            return None

    def create_tokenized_contexts(self, tokenizer):
        """
        Pre-tokenize context patterns for efficient matching during generation.
        Similar to how guided mode does token-based matching.
        
        Args:
            tokenizer: Tokenizer for encoding contexts
        """
        max_pts_tokens = 256
        count = 0
        for vector in self.steering_vectors:
            context = vector.get('pivot_context', '')
            if not context:
                continue
            tokenized_context = tokenizer.encode(context, add_special_tokens=False)
            if len(tokenized_context) > max_pts_tokens:
                tokenized_context = tokenized_context[-max_pts_tokens:]
            tuple_key = tuple(tokenized_context)
            self.tokenized_contexts[tuple_key] = vector
            for suffix_len in [4, 8, 12]:
                if len(tokenized_context) > suffix_len:
                    suffix = tokenized_context[-suffix_len:]
                    suffix_tuple = tuple(suffix)
                    if suffix_tuple not in self.tokenized_contexts:
                        self.tokenized_contexts[suffix_tuple] = vector
            count += 1
        logger.info(f'STEERING: Pre-tokenized {count} contexts into {len(self.tokenized_contexts)} token patterns')
        length_counts = {}
        for key in self.tokenized_contexts.keys():
            length = len(key)
            if length not in length_counts:
                length_counts[length] = 0
            length_counts[length] += 1
        logger.info(f'STEERING: Token pattern length distribution: {sorted(length_counts.items())}')

    def get_steering_strength(self, pattern: str) -> float:
        """
        Get the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            The steering strength
        """
        return self.pattern_strengths.get(pattern, self.default_strength)

    def set_steering_strength(self, pattern: str, strength: float):
        """
        Set the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            strength: The steering strength
        """
        self.pattern_strengths[pattern] = strength
        logger.info(f'STEERING: Set strength for {pattern} to {strength}')

    def get_pattern_vectors(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Get all steering vectors for a specific reasoning pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            List of steering vectors
        """
        return self.pattern_to_vectors.get(pattern, [])

    def get_steering_vector(self, context: str, match_key: Optional[str]=None) -> Optional[Dict[str, Any]]:
        """
        Get the most appropriate steering vector for a context.
        
        Args:
            context: The current generation context.
            match_key: Optional key for matching.
            
        Returns:
            Dictionary with steering data or None if no match.
        """
        if match_key is not None:
            for vector in self.steering_vectors:
                vector_context = vector.get('pivot_context', '')
                vector_key = vector_context[-100:] if len(vector_context) >= 100 else vector_context
                if vector_key == match_key:
                    logger.debug(f"STEERING: Context match found for '{vector.get('pivot_token', '')}' with pattern {vector.get('reasoning_pattern', 'unknown')}")
                    return vector
                if random.random() < 0.001:
                    logger.debug(f'STEERING: Match failed - key length: {len(match_key)}, vector key length: {len(vector_key)}')
                    logger.debug(f"STEERING: Match key sample: '{match_key[:20]}...'")
                    logger.debug(f"STEERING: Vector key sample: '{vector_key[:20]}...'")
        return None

def __init__(self, dataset_name: str, target_layer: int=19, cache_dir: Optional[str]=None, device: Optional[str]=None):
    """
        Initialize the steering vector manager.
        
        Args:
            dataset_name: Name of the HuggingFace dataset containing steering vectors
            target_layer: Target layer for applying steering vectors
            cache_dir: Directory for caching the dataset
            device: Device to use for tensors
        """
    self.dataset_name = dataset_name
    self.target_layer = target_layer
    self.cache_dir = cache_dir
    self.device = device or ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    self.steering_vectors = []
    self.pattern_to_vectors = {}
    self.tokenized_contexts = {}
    self.default_strength = 2.0
    self.pattern_strengths = {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5, 'unknown': 1.0}
    if dataset_name:
        self.load_dataset()

class DeepConfProcessor:
    """
    Main DeepConf processor implementing online mode with early termination.
    """

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, config: Dict[str, Any]=None):
        """
        Initialize the DeepConf processor.
        
        Args:
            model: The language model
            tokenizer: The tokenizer
            config: Configuration dictionary
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.confidence_calculator = ConfidenceCalculator(window_size=self.config['window_size'], top_k=self.config['top_k'])
        self.threshold_calibrator = ConfidenceThresholdCalibrator(variant=self.config['variant'])
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        logger.info(f'DeepConf processor initialized with variant: {self.config['variant']}')

    def reset(self):
        """Reset processor state for new query."""
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        self.confidence_calculator.reset()

    def generate_single_trace(self, messages: List[Dict[str, str]], use_early_termination: bool=False) -> TraceResult:
        """
        Generate a single reasoning trace with optional early termination.
        
        Args:
            messages: Input messages
            use_early_termination: Whether to apply early termination
            
        Returns:
            TraceResult object containing trace and confidence stats
        """
        self.confidence_calculator.reset()
        tokens = self.tokenizer.apply_chat_template(messages, return_tensors='pt', add_generation_prompt=True).to(self.model.device)
        kv_cache = DynamicCache()
        generated_tokens = []
        generated_text_parts = []
        token_count = 0
        terminated_early = False
        while token_count < self.config['max_tokens_per_trace']:
            with torch.no_grad():
                outputs = self.model(input_ids=tokens, past_key_values=kv_cache, use_cache=True)
                logits = outputs.logits[0, -1, :]
                kv_cache = outputs.past_key_values
            token_confidence = self.confidence_calculator.add_token_confidence(logits)
            if use_early_termination and token_count >= self.config['min_trace_length'] and (self.confidence_threshold is not None):
                current_group_confidence = self.confidence_calculator.get_current_group_confidence()
                if current_group_confidence is not None and current_group_confidence < self.confidence_threshold:
                    logger.debug(f'Early termination at token {token_count}, confidence: {current_group_confidence:.4f} < {self.confidence_threshold:.4f}')
                    terminated_early = True
                    break
            probs = torch.softmax(logits / self.config['temperature'], dim=-1)
            next_token = torch.multinomial(probs, num_samples=1).item()
            if next_token == self.tokenizer.eos_token_id:
                break
            generated_tokens.append(next_token)
            token_text = self.tokenizer.decode([next_token])
            generated_text_parts.append(token_text)
            tokens = torch.tensor([[next_token]]).to(self.model.device)
            token_count += 1
        generated_text = ''.join(generated_text_parts)
        confidence_stats = self.confidence_calculator.get_trace_statistics()
        trace_result = TraceResult(generated_tokens, generated_text, confidence_stats)
        trace_result.terminated_early = terminated_early
        self.total_tokens_used += token_count
        logger.debug(f'Generated trace: {token_count} tokens, avg confidence: {confidence_stats['average_confidence']:.4f}, early termination: {terminated_early}')
        return trace_result

    def run_warmup_phase(self, messages: List[Dict[str, str]]) -> None:
        """
        Run the warmup phase to generate initial traces and calibrate threshold.
        
        Args:
            messages: Input messages
        """
        logger.info(f'Starting warmup phase with {self.config['warmup_samples']} traces')
        for i in range(self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=False)
            self.warmup_traces.append(trace)
            self.threshold_calibrator.add_warmup_trace(trace.confidence_stats)
            logger.debug(f'Warmup trace {i + 1}/{self.config['warmup_samples']} completed')
        self.confidence_threshold = self.threshold_calibrator.calculate_threshold(metric=self.config['confidence_metric'])
        logger.info(f'Warmup phase completed. Threshold: {self.confidence_threshold:.4f}')

    def check_consensus(self, traces: List[TraceResult]) -> Tuple[bool, str, float]:
        """
        Check if consensus has been reached among traces.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (has_consensus, consensus_answer, consensus_ratio)
        """
        if not traces:
            return (False, '', 0.0)
        answers = []
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answers.append(answer)
        answer_counts = Counter(answers)
        most_common_answer, most_common_count = answer_counts.most_common(1)[0]
        consensus_ratio = most_common_count / len(answers)
        has_consensus = consensus_ratio >= self.config['consensus_threshold']
        logger.debug(f'Consensus check: {consensus_ratio:.3f} ({('✓' if has_consensus else '✗')} >= {self.config['consensus_threshold']})')
        return (has_consensus, most_common_answer, consensus_ratio)

    def weighted_majority_vote(self, traces: List[TraceResult]) -> Tuple[str, Dict[str, float]]:
        """
        Perform weighted majority voting based on trace confidences.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (best_answer, voting_stats)
        """
        if not traces:
            return ('', {})
        answer_groups = defaultdict(list)
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answer_groups[answer].append(trace)
        answer_scores = {}
        for answer, group_traces in answer_groups.items():
            confidences = [trace.confidence_stats['average_confidence'] for trace in group_traces]
            weighted_score = sum(confidences) / len(confidences)
            count_weight = len(group_traces) / len(traces)
            final_score = weighted_score * 0.7 + count_weight * 0.3
            answer_scores[answer] = final_score
        best_answer = max(answer_scores.keys(), key=lambda x: answer_scores[x])
        voting_stats = {'num_unique_answers': len(answer_groups), 'best_score': answer_scores[best_answer], 'answer_distribution': {ans: len(traces) for ans, traces in answer_groups.items()}}
        logger.info(f'Weighted voting completed. Best answer score: {answer_scores[best_answer]:.4f}')
        return (best_answer, voting_stats)

    def process_online(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
        """
        Main online processing with warmup and early termination.
        
        Args:
            messages: Input messages
            
        Returns:
            Tuple of (final_answer, processing_stats)
        """
        self.reset()
        logger.info('Starting DeepConf online processing')
        self.run_warmup_phase(messages)
        logger.info('Starting online generation phase')
        all_traces = self.warmup_traces[:]
        for trace_num in range(self.config['max_traces'] - self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=True)
            all_traces.append(trace)
            self.online_traces.append(trace)
            has_consensus, consensus_answer, consensus_ratio = self.check_consensus(all_traces)
            logger.debug(f'Online trace {trace_num + 1} completed. Total traces: {len(all_traces)}, Consensus: {consensus_ratio:.3f}')
            if has_consensus:
                logger.info(f'Consensus reached after {len(all_traces)} traces (ratio: {consensus_ratio:.3f})')
                break
        final_answer, voting_stats = self.weighted_majority_vote(all_traces)
        processing_stats = {'total_traces': len(all_traces), 'warmup_traces': len(self.warmup_traces), 'online_traces': len(self.online_traces), 'early_terminations': sum((1 for trace in all_traces if trace.terminated_early)), 'total_tokens_used': self.total_tokens_used, 'confidence_threshold': self.confidence_threshold, 'variant': self.config['variant'], **voting_stats}
        logger.info(f'DeepConf processing completed. Traces: {processing_stats['total_traces']}, Tokens: {processing_stats['total_tokens_used']}, Early terminations: {processing_stats['early_terminations']}')
        return (final_answer, processing_stats)

def reset(self):
    """Reset processor state for new query."""
    self.warmup_traces = []
    self.online_traces = []
    self.confidence_threshold = None
    self.total_tokens_used = 0
    self.confidence_calculator.reset()

def generate_single_trace(self, messages: List[Dict[str, str]], use_early_termination: bool=False) -> TraceResult:
    """
        Generate a single reasoning trace with optional early termination.
        
        Args:
            messages: Input messages
            use_early_termination: Whether to apply early termination
            
        Returns:
            TraceResult object containing trace and confidence stats
        """
    self.confidence_calculator.reset()
    tokens = self.tokenizer.apply_chat_template(messages, return_tensors='pt', add_generation_prompt=True).to(self.model.device)
    kv_cache = DynamicCache()
    generated_tokens = []
    generated_text_parts = []
    token_count = 0
    terminated_early = False
    while token_count < self.config['max_tokens_per_trace']:
        with torch.no_grad():
            outputs = self.model(input_ids=tokens, past_key_values=kv_cache, use_cache=True)
            logits = outputs.logits[0, -1, :]
            kv_cache = outputs.past_key_values
        token_confidence = self.confidence_calculator.add_token_confidence(logits)
        if use_early_termination and token_count >= self.config['min_trace_length'] and (self.confidence_threshold is not None):
            current_group_confidence = self.confidence_calculator.get_current_group_confidence()
            if current_group_confidence is not None and current_group_confidence < self.confidence_threshold:
                logger.debug(f'Early termination at token {token_count}, confidence: {current_group_confidence:.4f} < {self.confidence_threshold:.4f}')
                terminated_early = True
                break
        probs = torch.softmax(logits / self.config['temperature'], dim=-1)
        next_token = torch.multinomial(probs, num_samples=1).item()
        if next_token == self.tokenizer.eos_token_id:
            break
        generated_tokens.append(next_token)
        token_text = self.tokenizer.decode([next_token])
        generated_text_parts.append(token_text)
        tokens = torch.tensor([[next_token]]).to(self.model.device)
        token_count += 1
    generated_text = ''.join(generated_text_parts)
    confidence_stats = self.confidence_calculator.get_trace_statistics()
    trace_result = TraceResult(generated_tokens, generated_text, confidence_stats)
    trace_result.terminated_early = terminated_early
    self.total_tokens_used += token_count
    logger.debug(f'Generated trace: {token_count} tokens, avg confidence: {confidence_stats['average_confidence']:.4f}, early termination: {terminated_early}')
    return trace_result

class ConfidenceCalculator:
    """
    Calculates various confidence metrics for token-level assessment.
    """

    def __init__(self, window_size: int=2048, top_k: int=5):
        """
        Initialize the confidence calculator.
        
        Args:
            window_size: Size of sliding window for group confidence
            top_k: Number of top tokens for token confidence calculation
        """
        self.window_size = window_size
        self.top_k = top_k
        self.token_confidences = []
        self.group_confidences = []

    def reset(self):
        """Reset internal state for new trace."""
        self.token_confidences = []
        self.group_confidences = []

    def calculate_token_entropy(self, logits: torch.Tensor) -> float:
        """
        Calculate token entropy: H = -∑P(j) log P(j)
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token entropy value
        """
        probs = F.softmax(logits, dim=-1)
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -(probs * log_probs).sum().item()
        return entropy

    def calculate_token_confidence(self, logits: torch.Tensor, k: Optional[int]=None) -> float:
        """
        Calculate token confidence: C = -(1/k) ∑log P(j) for top-k tokens
        
        Args:
            logits: Raw logits tensor for current token position
            k: Number of top tokens to consider (default: self.top_k)
            
        Returns:
            Token confidence value
        """
        if k is None:
            k = self.top_k
        log_probs = F.log_softmax(logits, dim=-1)
        top_log_probs, _ = torch.topk(log_probs, k=k)
        confidence = -top_log_probs.mean().item()
        return confidence

    def add_token_confidence(self, logits: torch.Tensor) -> float:
        """
        Add a new token's confidence and update group statistics.
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token confidence value
        """
        confidence = self.calculate_token_confidence(logits)
        self.token_confidences.append(confidence)
        if len(self.token_confidences) >= self.window_size:
            self._update_group_confidence()
        return confidence

    def _update_group_confidence(self):
        """Update group confidence based on current sliding window."""
        if len(self.token_confidences) < self.window_size:
            return
        start_idx = len(self.token_confidences) - self.window_size
        window_confidences = self.token_confidences[start_idx:]
        group_confidence = np.mean(window_confidences)
        self.group_confidences.append(group_confidence)

    def get_current_group_confidence(self) -> Optional[float]:
        """
        Get the most recent group confidence.
        
        Returns:
            Most recent group confidence or None if not available
        """
        if not self.group_confidences:
            return None
        return self.group_confidences[-1]

    def get_average_trace_confidence(self) -> float:
        """
        Calculate average confidence across all tokens in the trace.
        
        Returns:
            Average confidence value
        """
        if not self.token_confidences:
            return 0.0
        return np.mean(self.token_confidences)

    def get_bottom_10_percent_confidence(self) -> float:
        """
        Calculate average confidence of bottom 10% groups.
        
        Returns:
            Bottom 10% group confidence
        """
        if not self.group_confidences:
            return 0.0
        num_bottom = max(1, len(self.group_confidences) // 10)
        sorted_confidences = sorted(self.group_confidences)
        bottom_confidences = sorted_confidences[:num_bottom]
        return np.mean(bottom_confidences)

    def get_lowest_group_confidence(self) -> float:
        """
        Get the minimum confidence across all groups.
        
        Returns:
            Lowest group confidence
        """
        if not self.group_confidences:
            return 0.0
        return min(self.group_confidences)

    def get_trace_statistics(self) -> Dict[str, float]:
        """
        Get comprehensive confidence statistics for the current trace.
        
        Returns:
            Dictionary with various confidence metrics
        """
        return {'average_confidence': self.get_average_trace_confidence(), 'bottom_10_percent': self.get_bottom_10_percent_confidence(), 'lowest_group': self.get_lowest_group_confidence(), 'current_group': self.get_current_group_confidence() or 0.0, 'num_tokens': len(self.token_confidences), 'num_groups': len(self.group_confidences)}

def calculate_token_entropy(self, logits: torch.Tensor) -> float:
    """
        Calculate token entropy: H = -∑P(j) log P(j)
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token entropy value
        """
    probs = F.softmax(logits, dim=-1)
    log_probs = F.log_softmax(logits, dim=-1)
    entropy = -(probs * log_probs).sum().item()
    return entropy

def calculate_token_confidence(self, logits: torch.Tensor, k: Optional[int]=None) -> float:
    """
        Calculate token confidence: C = -(1/k) ∑log P(j) for top-k tokens
        
        Args:
            logits: Raw logits tensor for current token position
            k: Number of top tokens to consider (default: self.top_k)
            
        Returns:
            Token confidence value
        """
    if k is None:
        k = self.top_k
    log_probs = F.log_softmax(logits, dim=-1)
    top_log_probs, _ = torch.topk(log_probs, k=k)
    confidence = -top_log_probs.mean().item()
    return confidence

def add_token_confidence(self, logits: torch.Tensor) -> float:
    """
        Add a new token's confidence and update group statistics.
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token confidence value
        """
    confidence = self.calculate_token_confidence(logits)
    self.token_confidences.append(confidence)
    if len(self.token_confidences) >= self.window_size:
        self._update_group_confidence()
    return confidence

def get_trace_statistics(self) -> Dict[str, float]:
    """
        Get comprehensive confidence statistics for the current trace.
        
        Returns:
            Dictionary with various confidence metrics
        """
    return {'average_confidence': self.get_average_trace_confidence(), 'bottom_10_percent': self.get_bottom_10_percent_confidence(), 'lowest_group': self.get_lowest_group_confidence(), 'current_group': self.get_current_group_confidence() or 0.0, 'num_tokens': len(self.token_confidences), 'num_groups': len(self.group_confidences)}

def test_confidence_calculator():
    """Test ConfidenceCalculator functionality."""
    logger.info('Testing ConfidenceCalculator...')
    try:
        import torch
        from optillm.deepconf.confidence import ConfidenceCalculator
        calculator = ConfidenceCalculator(window_size=10, top_k=3)
        dummy_logits = torch.randn(1000)
        entropy = calculator.calculate_token_entropy(dummy_logits)
        assert isinstance(entropy, float) and entropy > 0
        confidence = calculator.calculate_token_confidence(dummy_logits)
        assert isinstance(confidence, float) and confidence > 0
        for _ in range(15):
            calculator.add_token_confidence(dummy_logits)
        stats = calculator.get_trace_statistics()
        assert 'average_confidence' in stats
        assert 'num_tokens' in stats
        assert stats['num_tokens'] == 15
        logger.info('✓ ConfidenceCalculator tests passed')
        return True
    except Exception as e:
        logger.error(f'✗ ConfidenceCalculator test failed: {e}')
        return False

