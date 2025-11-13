# Cluster 1

def encode_prompt(query, prompt_papers):
    """Encode multiple prompt instructions into a single string."""
    prompt = open('src/relevancy_prompt.txt').read() + '\n'
    prompt += query['interest']
    for idx, task_dict in enumerate(prompt_papers):
        title, authors, abstract = (task_dict['title'], task_dict['authors'], task_dict['abstract'])
        if not title:
            raise
        prompt += f'###\n'
        prompt += f'{idx + 1}. Title: {title}\n'
        prompt += f'{idx + 1}. Authors: {authors}\n'
        prompt += f'{idx + 1}. Abstract: {abstract}\n'
    prompt += f'\n Generate response:\n1.'
    print(prompt)
    return prompt

def run_all_day_paper(query={'interest': '', 'subjects': ['Computation and Language', 'Artificial Intelligence']}, date=None, data_dir='../data', model_name='gpt-3.5-turbo-16k', threshold_score=8, num_paper_in_prompt=8, temperature=0.4, top_p=1.0):
    if date is None:
        date = datetime.today().strftime('%a, %d %b %y')
    print('the date for the arxiv data is: ', date)
    all_papers = [json.loads(l) for l in open(f'{data_dir}/{date}.jsonl', 'r')]
    print(f'We found {len(all_papers)}.')
    all_papers_in_subjects = [t for t in all_papers if bool(set(process_subject_fields(t['subjects'])) & set(query['subjects']))]
    print(f'After filtering subjects, we have {len(all_papers_in_subjects)} papers left.')
    ans_data = generate_relevance_score(all_papers_in_subjects, query, model_name, threshold_score, num_paper_in_prompt, temperature, top_p)
    utils.write_ans_to_file(ans_data, date, output_dir='../outputs')
    return ans_data

