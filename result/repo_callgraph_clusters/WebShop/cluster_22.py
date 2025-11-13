# Cluster 22

def main():
    args = parse_args()
    accelerator = Accelerator()
    wandb.init(project='bert_il', config=args, name=args.output_dir)
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)
    logger.info(accelerator.state, main_process_only=False)
    if accelerator.is_local_main_process:
        datasets.utils.logging.set_verbosity_warning()
        transformers.utils.logging.set_verbosity_info()
    else:
        datasets.utils.logging.set_verbosity_error()
        transformers.utils.logging.set_verbosity_error()
    if args.seed is not None:
        set_seed(args.seed)
    config = BertConfigForWebshop(image=args.image, pretrain_bert=args.pretrain)
    model = BertModelForWebshop(config)
    train_dataset = get_dataset('train', mem=args.mem)
    eval_dataset = get_dataset('eval', mem=args.mem)
    for index in random.sample(range(len(train_dataset)), 3):
        logger.info(f'Sample {index} of the training set: {train_dataset[index]}.')
    train_dataloader = DataLoader(train_dataset, shuffle=True, collate_fn=data_collator, batch_size=args.per_device_train_batch_size)
    eval_dataloader = DataLoader(eval_dataset, collate_fn=data_collator, batch_size=args.per_device_eval_batch_size)
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [{'params': [p for n, p in model.named_parameters() if not any((nd in n for nd in no_decay))], 'weight_decay': args.weight_decay}, {'params': [p for n, p in model.named_parameters() if any((nd in n for nd in no_decay))], 'weight_decay': 0.0}]
    optimizer = AdamW(optimizer_grouped_parameters, lr=args.learning_rate)
    num_update_steps_per_epoch = math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)
    if args.max_train_steps is None:
        args.max_train_steps = args.num_train_epochs * num_update_steps_per_epoch
    else:
        args.num_train_epochs = math.ceil(args.max_train_steps / num_update_steps_per_epoch)
    lr_scheduler = get_scheduler(name=args.lr_scheduler_type, optimizer=optimizer, num_warmup_steps=args.num_warmup_steps, num_training_steps=args.max_train_steps)
    model, optimizer, train_dataloader, eval_dataloader, lr_scheduler = accelerator.prepare(model, optimizer, train_dataloader, eval_dataloader, lr_scheduler)
    num_update_steps_per_epoch = math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)
    args.max_train_steps = args.num_train_epochs * num_update_steps_per_epoch
    if hasattr(args.checkpointing_steps, 'isdigit'):
        checkpointing_steps = args.checkpointing_steps
        if args.checkpointing_steps.isdigit():
            checkpointing_steps = int(args.checkpointing_steps)
    else:
        checkpointing_steps = None
    if args.with_tracking:
        experiment_config = vars(args)
        experiment_config['lr_scheduler_type'] = experiment_config['lr_scheduler_type'].value
        accelerator.init_trackers('glue_no_trainer', experiment_config)
    metric = load_metric('accuracy')
    total_batch_size = args.per_device_train_batch_size * accelerator.num_processes * args.gradient_accumulation_steps
    logger.info('***** Running training *****')
    logger.info(f'  Num examples = {len(train_dataset)}')
    logger.info(f'  Num Epochs = {args.num_train_epochs}')
    logger.info(f'  Instantaneous batch size per device = {args.per_device_train_batch_size}')
    logger.info(f'  Total train batch size (w. parallel, distributed & accumulation) = {total_batch_size}')
    logger.info(f'  Gradient Accumulation steps = {args.gradient_accumulation_steps}')
    logger.info(f'  Total optimization steps = {args.max_train_steps}')
    progress_bar = tqdm(range(args.max_train_steps), disable=not accelerator.is_local_main_process)
    completed_steps = 0
    starting_epoch = 0
    if args.resume_from_checkpoint:
        if args.resume_from_checkpoint is not None or args.resume_from_checkpoint != '':
            accelerator.print(f'Resumed from checkpoint: {args.resume_from_checkpoint}')
            accelerator.load_state(args.resume_from_checkpoint)
            path = os.path.basename(args.resume_from_checkpoint)
        else:
            dirs = [f.name for f in os.scandir(os.getcwd()) if f.is_dir()]
            dirs.sort(key=os.path.getctime)
            path = dirs[-1]
        training_difference = os.path.splitext(path)[0]
        if 'epoch' in training_difference:
            starting_epoch = int(training_difference.replace('epoch_', '')) + 1
            resume_step = None
        else:
            resume_step = int(training_difference.replace('step_', ''))
            starting_epoch = resume_step // len(train_dataloader)
            resume_step -= starting_epoch * len(train_dataloader)
    for epoch in range(starting_epoch, args.num_train_epochs):
        model.train()
        if args.with_tracking:
            total_loss = total_step = 0
        for step, batch in enumerate(train_dataloader):
            if args.resume_from_checkpoint and epoch == starting_epoch:
                if resume_step is not None and step < resume_step:
                    completed_steps += 1
                    continue
            outputs = model(**batch)
            loss = outputs.loss
            if args.with_tracking:
                total_loss += loss.detach().float()
                total_step += 1
            loss = loss / args.gradient_accumulation_steps
            accelerator.backward(loss)
            metric.add_batch(predictions=torch.stack([logit.argmax(dim=0) for logit in outputs.logits]), references=batch['labels'])
            if step % args.gradient_accumulation_steps == 0 or step == len(train_dataloader) - 1:
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()
                progress_bar.update(1)
                completed_steps += 1
                if args.with_tracking and args.logging_steps > 0 and (completed_steps % args.logging_steps == 0):
                    train_metric = metric.compute()
                    wandb.log({'train_accuracy': train_metric, 'train_loss': total_loss / total_step, 'train_step': completed_steps})
                    total_loss = total_step = 0
            if isinstance(checkpointing_steps, int):
                if completed_steps % checkpointing_steps == 0:
                    output_dir = f'step_{completed_steps}'
                    if args.output_dir is not None:
                        output_dir = os.path.join(args.output_dir, output_dir)
                    accelerator.save_state(output_dir)
            if completed_steps >= args.max_train_steps:
                break
        model.eval()
        samples_seen = 0
        total_loss = total_step = 0
        if len(metric) > 0:
            metric.compute()
        for step, batch in enumerate(eval_dataloader):
            with torch.no_grad():
                outputs = model(**batch)
            predictions = torch.stack([logit.argmax(dim=0) for logit in outputs.logits])
            predictions, references = accelerator.gather((predictions, batch['labels']))
            if accelerator.num_processes > 1:
                if step == len(eval_dataloader):
                    predictions = predictions[:len(eval_dataloader.dataset) - samples_seen]
                    references = references[:len(eval_dataloader.dataset) - samples_seen]
                else:
                    samples_seen += references.shape[0]
            metric.add_batch(predictions=predictions, references=references)
            total_loss += outputs.loss.detach().float()
            total_step += 1
        eval_metric = metric.compute()
        logger.info(f'epoch {epoch}: {eval_metric}')
        if args.with_tracking:
            wandb.log({'eval_accuracy': eval_metric, 'eval_loss': total_loss / total_step, 'epoch': epoch, 'epoch_step': completed_steps})
        if args.checkpointing_steps == 'epoch':
            output_dir = f'epoch_{epoch}'
            if args.output_dir is not None:
                output_dir = os.path.join(args.output_dir, output_dir)
            os.makedirs(output_dir, exist_ok=True)
            unwrapped_model = accelerator.unwrap_model(model)
            torch.save(unwrapped_model.state_dict(), os.path.join(output_dir, 'model.pth'))
    if args.output_dir is not None:
        with open(os.path.join(args.output_dir, 'all_results.json'), 'w') as f:
            json.dump({'eval_accuracy': eval_metric['accuracy']}, f)

def discount_reward(transitions, last_values, gamma):
    returns, advantages = ([], [])
    R = last_values.detach()
    for t in reversed(range(len(transitions))):
        _, _, rewards, values, _, dones = transitions[t]
        R = torch.FloatTensor(rewards).to(device) + gamma * R * (1 - torch.FloatTensor(dones).to(device))
        baseline = values
        adv = R - baseline
        returns.append(R)
        advantages.append(adv)
    return (returns[::-1], advantages[::-1])

class Agent:

    def __init__(self, args):
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', truncation_side='left', max_length=512)
        self.tokenizer.add_tokens(['[button], [button_], [clicked button], [clicked button_]'], special_tokens=True)
        vocab_size = len(self.tokenizer)
        embedding_dim = args.embedding_dim
        if args.network == 'rnn':
            self.network = RCDQN(vocab_size, embedding_dim, args.hidden_dim, args.arch_encoder, args.grad_encoder, None, args.gru_embed, args.get_image, args.bert_path)
            self.network.rl_forward = self.network.forward
        elif args.network == 'bert':
            config = BertConfigForWebshop(image=args.get_image, pretrained_bert=args.bert_path != 'scratch')
            self.network = BertModelForWebshop(config)
            if args.bert_path != '' and args.bert_path != 'scratch':
                self.network.load_state_dict(torch.load(args.bert_path, map_location=torch.device('cpu')), strict=False)
        else:
            raise ValueError('Unknown network: {}'.format(args.network))
        self.network = self.network.to(device)
        self.save_path = args.output_dir
        self.clip = args.clip
        self.w = {'loss_pg': args.w_pg, 'loss_td': args.w_td, 'loss_il': args.w_il, 'loss_en': args.w_en}
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=args.learning_rate)
        self.gamma = args.gamma

    def build_state(self, ob, info):
        """ Returns a state representation built from various info sources. """
        obs_ids = self.encode(ob)
        goal_ids = self.encode(info['goal'])
        click = info['valid'][0].startswith('click[')
        estimate = info['estimate_score']
        obs_str = ob.replace('\n', '[SEP]')
        goal_str = info['goal']
        image_feat = info.get('image_feat')
        return State(obs_ids, goal_ids, click, estimate, obs_str, goal_str, image_feat)

    def encode(self, observation, max_length=512):
        """ Encode an observation """
        observation = observation.lower().replace('"', '').replace("'", '').strip()
        observation = observation.replace('[sep]', '[SEP]')
        token_ids = self.tokenizer.encode(observation, truncation=True, max_length=max_length)
        return token_ids

    def decode(self, act):
        act = self.tokenizer.decode(act, skip_special_tokens=True)
        act = act.replace(' [ ', '[').replace(' ]', ']')
        return act

    def encode_valids(self, valids, max_length=64):
        """ Encode a list of lists of strs """
        return [[self.encode(act, max_length=max_length) for act in valid] for valid in valids]

    def act(self, states, valid_acts, method, state_strs=None, eps=0.1):
        """ Returns a string action from poss_acts. """
        act_ids = self.encode_valids(valid_acts)
        act_values, act_sizes, values = self.network.rl_forward(states, act_ids, value=True, act=True)
        act_values = act_values.split(act_sizes)
        if method == 'softmax':
            act_probs = [F.softmax(vals, dim=0) for vals in act_values]
            act_idxs = [torch.multinomial(probs, num_samples=1).item() for probs in act_probs]
        elif method == 'greedy':
            act_idxs = [vals.argmax(dim=0).item() for vals in act_values]
        elif method == 'eps':
            act_idxs = [vals.argmax(dim=0).item() if random.random() > eps else random.randint(0, len(vals) - 1) for vals in act_values]
        acts = [acts[idx] for acts, idx in zip(act_ids, act_idxs)]
        act_strs, act_ids = ([], [])
        for act, idx, valids in zip(acts, act_idxs, valid_acts):
            if torch.is_tensor(act):
                act = act.tolist()
            if 102 in act:
                act = act[:act.index(102) + 1]
            act_ids.append(act)
            if idx is None:
                act_str = self.decode(act)
            else:
                act_str = valids[idx]
            act_strs.append(act_str)
        return (act_strs, act_ids, values)

    def update(self, transitions, last_values, step=None, rewards_invdy=None):
        returns, advs = discount_reward(transitions, last_values, self.gamma)
        stats_global = defaultdict(float)
        for transition, adv in zip(transitions, advs):
            stats = {}
            log_valid, valid_sizes = self.network.rl_forward(transition.state, transition.valid_acts)
            act_values = log_valid.split(valid_sizes)
            log_a = torch.stack([values[acts.index(act)] for values, acts, act in zip(act_values, transition.valid_acts, transition.act)])
            stats['loss_pg'] = -(log_a * adv.detach()).mean()
            stats['loss_td'] = adv.pow(2).mean()
            stats['loss_il'] = -log_valid.mean()
            stats['loss_en'] = (log_valid * log_valid.exp()).mean()
            for k in stats:
                stats[k] = self.w[k] * stats[k] / len(transitions)
            stats['loss'] = sum((stats[k] for k in stats))
            stats['returns'] = torch.stack(returns).mean() / len(transitions)
            stats['advs'] = torch.stack(advs).mean() / len(transitions)
            stats['loss'].backward()
            stats['gradnorm_unclipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
            nn.utils.clip_grad_norm_(self.network.parameters(), self.clip)
            stats['gradnorm_clipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
            for k, v in stats.items():
                stats_global[k] += v.item() if torch.is_tensor(v) else v
            del stats
        self.optimizer.step()
        self.optimizer.zero_grad()
        return stats_global

    def load(self):
        try:
            self.network = torch.load(os.path.join(self.save_path, 'model.pt'))
        except Exception as e:
            print('Error saving model.', e)

    def save(self):
        try:
            torch.save(self.network, os.path.join(self.save_path, 'model.pt'))
        except Exception as e:
            print('Error saving model.', e)

def __init__(self, args):
    self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', truncation_side='left', max_length=512)
    self.tokenizer.add_tokens(['[button], [button_], [clicked button], [clicked button_]'], special_tokens=True)
    vocab_size = len(self.tokenizer)
    embedding_dim = args.embedding_dim
    if args.network == 'rnn':
        self.network = RCDQN(vocab_size, embedding_dim, args.hidden_dim, args.arch_encoder, args.grad_encoder, None, args.gru_embed, args.get_image, args.bert_path)
        self.network.rl_forward = self.network.forward
    elif args.network == 'bert':
        config = BertConfigForWebshop(image=args.get_image, pretrained_bert=args.bert_path != 'scratch')
        self.network = BertModelForWebshop(config)
        if args.bert_path != '' and args.bert_path != 'scratch':
            self.network.load_state_dict(torch.load(args.bert_path, map_location=torch.device('cpu')), strict=False)
    else:
        raise ValueError('Unknown network: {}'.format(args.network))
    self.network = self.network.to(device)
    self.save_path = args.output_dir
    self.clip = args.clip
    self.w = {'loss_pg': args.w_pg, 'loss_td': args.w_td, 'loss_il': args.w_il, 'loss_en': args.w_en}
    self.optimizer = torch.optim.Adam(self.network.parameters(), lr=args.learning_rate)
    self.gamma = args.gamma

def update(self, transitions, last_values, step=None, rewards_invdy=None):
    returns, advs = discount_reward(transitions, last_values, self.gamma)
    stats_global = defaultdict(float)
    for transition, adv in zip(transitions, advs):
        stats = {}
        log_valid, valid_sizes = self.network.rl_forward(transition.state, transition.valid_acts)
        act_values = log_valid.split(valid_sizes)
        log_a = torch.stack([values[acts.index(act)] for values, acts, act in zip(act_values, transition.valid_acts, transition.act)])
        stats['loss_pg'] = -(log_a * adv.detach()).mean()
        stats['loss_td'] = adv.pow(2).mean()
        stats['loss_il'] = -log_valid.mean()
        stats['loss_en'] = (log_valid * log_valid.exp()).mean()
        for k in stats:
            stats[k] = self.w[k] * stats[k] / len(transitions)
        stats['loss'] = sum((stats[k] for k in stats))
        stats['returns'] = torch.stack(returns).mean() / len(transitions)
        stats['advs'] = torch.stack(advs).mean() / len(transitions)
        stats['loss'].backward()
        stats['gradnorm_unclipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
        nn.utils.clip_grad_norm_(self.network.parameters(), self.clip)
        stats['gradnorm_clipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
        for k, v in stats.items():
            stats_global[k] += v.item() if torch.is_tensor(v) else v
        del stats
    self.optimizer.step()
    self.optimizer.zero_grad()
    return stats_global

def save(self):
    try:
        torch.save(self.network, os.path.join(self.save_path, 'model.pt'))
    except Exception as e:
        print('Error saving model.', e)

class WandBOutputFormat(KVWriter):

    def __init__(self, filename):
        group = None
        if filename.endswith('trial'):
            group = filename[:-6]
        wandb.init(project='web_drrn', name=filename, group=group)

    def writekvs(self, kvs):
        wandb.log(kvs)

    def close(self):
        pass

def __init__(self, filename):
    group = None
    if filename.endswith('trial'):
        group = filename[:-6]
    wandb.init(project='web_drrn', name=filename, group=group)

