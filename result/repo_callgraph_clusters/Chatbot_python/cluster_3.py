# Cluster 3

def main():
    st.title('Chatbot Collections')
    st.session_state.collections = list_collections()
    upload_files()
    if st.session_state.collections:
        st.subheader('Existing Collections')
        cols = st.columns(4)
        for index, collection in enumerate(st.session_state.collections):
            col = cols[index % 4]
            with col:
                st.button(f'{collection.name}', key=collection.id, on_click=lambda c=collection: st.session_state.update({'collection': c}))
    else:
        st.subheader('No collections found')

# Node: title
# Node: upload_files
# Node: subheader
# Node: columns
# Node: enumerate
# Node: button
# Node: update
def chat_page():
    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
    with col1:
        st.title(f'Chat with {st.session_state.collection.name}')
    with col2:
        st.button('Back to collections', on_click=lambda: st.session_state.pop('collection'))
    response = requests.get(f'{CHATBOT_URL}/collectionChat/{st.session_state.collection.name}')
    conversation = [message for message in response.json()['conversation'] if message['role'] != 'system']
    st.session_state.conversation = conversation
    if st.session_state.conversation:
        chat_container = st.container(border=True, height=450)
        with chat_container:
            for idx, message in enumerate(st.session_state.conversation):
                with st.chat_message(message['role']):
                    if idx == len(st.session_state.conversation) - 1:
                        st.write_stream(stream_response(message['content']))
                    else:
                        st.markdown(message['content'])
    st.text_input('Ask a question:', key='user_input', on_change=ask)

# Node: pop
# Node: container
# Node: chat_message
# Node: len
# Node: write_stream
# Node: stream_response
# Node: markdown
# Node: text_input
def text_to_documents(text: str, metadata: dict) -> List[Document]:
    """Convert text into a list of Document objects."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(text)
    return [Document(page_content=t, metadata={'chunk_id': idx, 'total_chunks': len(texts), **metadata}) for idx, t in enumerate(texts)]

# Node: RecursiveCharacterTextSplitter
# Node: split_text
# Node: Document
