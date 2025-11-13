# Cluster 5

def openai_completion(prompts, decoding_args: OpenAIDecodingArguments, model_name='text-davinci-003', sleep_time=2, batch_size=1, max_instances=sys.maxsize, max_batches=sys.maxsize, return_text=False, **decoding_kwargs) -> Union[Union[StrOrOpenAIObject], Sequence[StrOrOpenAIObject], Sequence[Sequence[StrOrOpenAIObject]]]:
    """Decode with OpenAI API.

    Args:
        prompts: A string or a list of strings to complete. If it is a chat model the strings should be formatted
            as explained here: https://github.com/openai/openai-python/blob/main/chatml.md. If it is a chat model
            it can also be a dictionary (or list thereof) as explained here:
            https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb
        decoding_args: Decoding arguments.
        model_name: Model name. Can be either in the format of "org/model" or just "model".
        sleep_time: Time to sleep once the rate-limit is hit.
        batch_size: Number of prompts to send in a single request. Only for non chat model.
        max_instances: Maximum number of prompts to decode.
        max_batches: Maximum number of batches to decode. This argument will be deprecated in the future.
        return_text: If True, return text instead of full completion object (which contains things like logprob).
        decoding_kwargs: Additional decoding arguments. Pass in `best_of` and `logit_bias` if you need them.

    Returns:
        A completion or a list of completions.
        Depending on return_text, return_openai_object, and decoding_args.n, the completion type can be one of
            - a string (if return_text is True)
            - an openai_object.OpenAIObject object (if return_text is False)
            - a list of objects of the above types (if decoding_args.n > 1)
    """
    is_chat_model = 'gpt-3.5' in model_name or 'gpt-4' in model_name
    is_single_prompt = isinstance(prompts, (str, dict))
    if is_single_prompt:
        prompts = [prompts]
    if max_batches < sys.maxsize:
        logging.warning('`max_batches` will be deprecated in the future, please use `max_instances` instead.Setting `max_instances` to `max_batches * batch_size` for now.')
        max_instances = max_batches * batch_size
    prompts = prompts[:max_instances]
    num_prompts = len(prompts)
    prompt_batches = [prompts[batch_id * batch_size:(batch_id + 1) * batch_size] for batch_id in range(int(math.ceil(num_prompts / batch_size)))]
    completions = []
    for batch_id, prompt_batch in tqdm.tqdm(enumerate(prompt_batches), desc='prompt_batches', total=len(prompt_batches)):
        batch_decoding_args = copy.deepcopy(decoding_args)
        backoff = 3
        while True:
            try:
                shared_kwargs = dict(model=model_name, **batch_decoding_args.__dict__, **decoding_kwargs)
                if is_chat_model:
                    completion_batch = openai.ChatCompletion.create(messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': prompt_batch[0]}], **shared_kwargs)
                else:
                    completion_batch = openai.Completion.create(prompt=prompt_batch, **shared_kwargs)
                choices = completion_batch.choices
                for choice in choices:
                    choice['total_tokens'] = completion_batch.usage.total_tokens
                completions.extend(choices)
                break
            except openai.error.OpenAIError as e:
                logging.warning(f'OpenAIError: {e}.')
                if 'Please reduce your prompt' in str(e):
                    batch_decoding_args.max_tokens = int(batch_decoding_args.max_tokens * 0.8)
                    logging.warning(f'Reducing target length to {batch_decoding_args.max_tokens}, Retrying...')
                elif not backoff:
                    logging.error('Hit too many failures, exiting')
                    raise e
                else:
                    backoff -= 1
                    logging.warning('Hit request rate limit; retrying...')
                    time.sleep(sleep_time)
    if return_text:
        completions = [completion.text for completion in completions]
    if decoding_args.n > 1:
        completions = [completions[i:i + decoding_args.n] for i in range(0, len(completions), decoding_args.n)]
    if is_single_prompt:
        completions, = completions
    return completions

def generate_relevance_score(all_papers, query, model_name='gpt-3.5-turbo-16k', threshold_score=8, num_paper_in_prompt=4, temperature=0.4, top_p=1.0, sorting=True):
    ans_data = []
    request_idx = 1
    hallucination = False
    for id in tqdm.tqdm(range(0, len(all_papers), num_paper_in_prompt)):
        prompt_papers = all_papers[id:id + num_paper_in_prompt]
        prompt = encode_prompt(query, prompt_papers)
        decoding_args = utils.OpenAIDecodingArguments(temperature=temperature, n=1, max_tokens=128 * num_paper_in_prompt, top_p=top_p)
        request_start = time.time()
        response = utils.openai_completion(prompts=prompt, model_name=model_name, batch_size=1, decoding_args=decoding_args, logit_bias={'100257': -100})
        print('response', response['message']['content'])
        request_duration = time.time() - request_start
        process_start = time.time()
        batch_data, hallu = post_process_chat_gpt_response(prompt_papers, response, threshold_score=threshold_score)
        hallucination = hallucination or hallu
        ans_data.extend(batch_data)
        print(f'Request {request_idx + 1} took {request_duration:.2f}s')
        print(f'Post-processing took {time.time() - process_start:.2f}s')
    if sorting:
        ans_data = sorted(ans_data, key=lambda x: int(x['Relevancy score']), reverse=True)
    return (ans_data, hallucination)

