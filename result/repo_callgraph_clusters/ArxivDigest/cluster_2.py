# Cluster 2

def sample(email, topic, physics_topic, categories, interest):
    if not topic:
        raise gr.Error('You must choose a topic.')
    if topic == 'Physics':
        if isinstance(physics_topic, list):
            raise gr.Error('You must choose a physics topic.')
        topic = physics_topic
        abbr = physics_topics[topic]
    else:
        abbr = topics[topic]
    if categories:
        papers = get_papers(abbr)
        papers = [t for t in papers if bool(set(process_subject_fields(t['subjects'])) & set(categories))][:4]
    else:
        papers = get_papers(abbr, limit=4)
    if interest:
        if not openai.api_key:
            raise gr.Error('Set your OpenAI api key on the left first')
        relevancy, _ = generate_relevance_score(papers, query={'interest': interest}, threshold_score=0, num_paper_in_prompt=4)
        return '\n\n'.join([paper['summarized_text'] for paper in relevancy])
    else:
        return '\n\n'.join((f'Title: {paper['title']}\nAuthors: {paper['authors']}' for paper in papers))

def test(email, topic, physics_topic, categories, interest, key):
    if not email:
        raise gr.Error('Set your email')
    if not key:
        raise gr.Error('Set your SendGrid key')
    if topic == 'Physics':
        if isinstance(physics_topic, list):
            raise gr.Error('You must choose a physics topic.')
        topic = physics_topic
        abbr = physics_topics[topic]
    else:
        abbr = topics[topic]
    if categories:
        papers = get_papers(abbr)
        papers = [t for t in papers if bool(set(process_subject_fields(t['subjects'])) & set(categories))][:4]
    else:
        papers = get_papers(abbr, limit=4)
    if interest:
        if not openai.api_key:
            raise gr.Error('Set your OpenAI api key on the left first')
        relevancy, hallucination = generate_relevance_score(papers, query={'interest': interest}, threshold_score=7, num_paper_in_prompt=8)
        body = '<br><br>'.join([f'Title: <a href="{paper['main_page']}">{paper['title']}</a><br>Authors: {paper['authors']}<br>Score: {paper['Relevancy score']}<br>Reason: {paper['Reasons for match']}' for paper in relevancy])
        if hallucination:
            body = 'Warning: the model hallucinated some papers. We have tried to remove them, but the scores may not be accurate.<br><br>' + body
    else:
        body = '<br><br>'.join([f'Title: <a href="{paper['main_page']}">{paper['title']}</a><br>Authors: {paper['authors']}' for paper in papers])
    sg = sendgrid.SendGridAPIClient(api_key=key)
    from_email = Email(email)
    to_email = To(email)
    subject = 'arXiv digest'
    content = Content('text/html', body)
    mail = Mail(from_email, to_email, subject, content)
    mail_json = mail.get()
    response = sg.client.mail.send.post(request_body=mail_json)
    if response.status_code >= 200 and response.status_code <= 300:
        return 'Success!'
    else:
        return 'Failure: ({response.status_code})'

def generate_body(topic, categories, interest, threshold):
    if topic == 'Physics':
        raise RuntimeError('You must choose a physics subtopic.')
    elif topic in physics_topics:
        abbr = physics_topics[topic]
    elif topic in topics:
        abbr = topics[topic]
    else:
        raise RuntimeError(f'Invalid topic {topic}')
    if categories:
        for category in categories:
            if category not in category_map[topic]:
                raise RuntimeError(f'{category} is not a category of {topic}')
        papers = get_papers(abbr)
        papers = [t for t in papers if bool(set(process_subject_fields(t['subjects'])) & set(categories))]
    else:
        papers = get_papers(abbr)
    if interest:
        relevancy, hallucination = generate_relevance_score(papers, query={'interest': interest}, threshold_score=threshold, num_paper_in_prompt=16)
        body = '<br><br>'.join([f'Title: <a href="{paper['main_page']}">{paper['title']}</a><br>Authors: {paper['authors']}<br>Score: {paper['Relevancy score']}<br>Reason: {paper['Reasons for match']}' for paper in relevancy])
        if hallucination:
            body = 'Warning: the model hallucinated some papers. We have tried to remove them, but the scores may not be accurate.<br><br>' + body
    else:
        body = '<br><br>'.join([f'Title: <a href="{paper['main_page']}">{paper['title']}</a><br>Authors: {paper['authors']}' for paper in papers])
    return body

