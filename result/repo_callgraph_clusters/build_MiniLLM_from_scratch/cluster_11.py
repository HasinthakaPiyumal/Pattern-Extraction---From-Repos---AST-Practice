# Cluster 11

def collate_train_fn(batch):
    batch_token_ids = [i['input_ids'] for i in batch]
    batch_labels = [i['labels'] for i in batch]
    batch_token_ids = torch.tensor(sequence_padding(batch_token_ids, value=args.pad_token_id), dtype=torch.long)
    batch_labels = torch.tensor(sequence_padding(batch_labels, value=args.pad_token_id), dtype=torch.long)
    return ([batch_token_ids], batch_labels)

def collate_train_fn(batch):
    chosen_ids, chosen_labels, rejected_ids, rejected_labels = ([], [], [], [])
    for smp in batch:
        prompt_id, chosen_id, rejected_id = (smp['prompt_ids'], smp['chosen_ids'], smp['rejected_ids'])
        chosen_ids.append(prompt_id + chosen_id)
        chosen_labels.append([args.pad_token_id] * (len(prompt_id) - 1) + chosen_id + [args.eos_token_id])
        rejected_ids.append(prompt_id + rejected_id)
        rejected_labels.append([args.pad_token_id] * (len(prompt_id) - 1) + rejected_id + [args.eos_token_id])
    input_ids = torch.tensor(sequence_padding(chosen_ids + rejected_ids, value=args.pad_token_id), dtype=torch.long)
    input_labels = torch.tensor(sequence_padding(chosen_labels + rejected_labels, value=args.pad_token_id), dtype=torch.long)
    return (input_ids, input_labels)

