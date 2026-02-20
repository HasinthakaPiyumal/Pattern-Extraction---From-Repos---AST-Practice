# Cluster 2

# Node: list_collections
def upload_files():
    uploaded_files = st.file_uploader('Upload txt files', type='txt', accept_multiple_files=False)
    if uploaded_files:
        files = [('files', (uploaded_files.name, uploaded_files.getvalue(), 'text/plain'))]
        try:
            response = requests.post(f'{CHATBOT_URL}/upload/', files=files)
            if response.status_code == 200:
                st.session_state.collections = list_collections()
                st.success('Collections created successfully')
            else:
                st.error('Failed to create collections')
        except Exception as e:
            st.error(f'Error uploading files: {e}')

# Node: file_uploader
# Node: getvalue
# Node: post
# Node: success
def ask():
    with st.spinner('Analyzing... Please wait...'):
        qst = st.session_state.user_input
        response = requests.post(f'{CHATBOT_URL}/ask/{st.session_state.collection.name}', json={'question': qst, 'conversation_id': st.session_state.collection.name})
        if response.status_code == 200:
            bot_response = response.json()
            st.session_state.conversation.append(bot_response)
            st.session_state.user_input = ''
        else:
            st.error('Failed to get response')

# Node: spinner
# Node: append
def format_docs(docs) -> str:
    """Format the documents for the AI model."""
    formatted_docs = []
    for doc in docs:
        formatted_docs.append(doc['page_content'])
    return '\n'.join(formatted_docs)

# Node: join
