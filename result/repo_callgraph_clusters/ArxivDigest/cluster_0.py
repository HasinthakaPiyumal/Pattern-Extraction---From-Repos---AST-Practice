# Cluster 0

def change_subsubject(subject, physics_subject):
    if subject != 'Physics':
        return gr.Dropdown.update(choices=categories_map[subject], value=[], visible=True)
    elif physics_subject and (not isinstance(physics_subject, list)):
        return gr.Dropdown.update(choices=categories_map[physics_subject], value=[], visible=True)
    else:
        return gr.Dropdown.update(choices=[], value=[], visible=False)

def change_physics(subject):
    if subject != 'Physics':
        return gr.Dropdown.update(visible=False, value=[])
    else:
        return gr.Dropdown.update(physics_topics, visible=True)

def post_process_chat_gpt_response(paper_data, response, threshold_score=8):
    selected_data = []
    if response is None:
        return []
    json_items = response['message']['content'].replace('\n\n', '\n').split('\n')
    pattern = '^\\d+\\. |\\\\'
    import pprint
    try:
        score_items = [json.loads(re.sub(pattern, '', line)) for line in json_items if 'relevancy score' in line.lower()]
    except Exception:
        pprint.pprint([re.sub(pattern, '', line) for line in json_items if 'relevancy score' in line.lower()])
        raise RuntimeError('failed')
    pprint.pprint(score_items)
    scores = []
    for item in score_items:
        temp = item['Relevancy score']
        if isinstance(temp, str) and '/' in temp:
            scores.append(int(temp.split('/')[0]))
        else:
            scores.append(int(temp))
    if len(score_items) != len(paper_data):
        score_items = score_items[:len(paper_data)]
        hallucination = True
    else:
        hallucination = False
    for idx, inst in enumerate(score_items):
        if scores[idx] < threshold_score:
            continue
        output_str = 'Title: ' + paper_data[idx]['title'] + '\n'
        output_str += 'Authors: ' + paper_data[idx]['authors'] + '\n'
        output_str += 'Link: ' + paper_data[idx]['main_page'] + '\n'
        for key, value in inst.items():
            paper_data[idx][key] = value
            output_str += str(key) + ': ' + str(value) + '\n'
        paper_data[idx]['summarized_text'] = output_str
        selected_data.append(paper_data[idx])
    return (selected_data, hallucination)

def process_subject_fields(subjects):
    all_subjects = subjects.split(';')
    all_subjects = [s.split(' (')[0] for s in all_subjects]
    return all_subjects

