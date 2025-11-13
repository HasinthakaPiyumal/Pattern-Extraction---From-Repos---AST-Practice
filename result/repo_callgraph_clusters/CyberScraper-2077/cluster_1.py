# Cluster 1

def serialize_bytesio(obj):
    if isinstance(obj, BytesIO):
        return {'_type': 'BytesIO', 'data': base64.b64encode(obj.getvalue()).decode('utf-8')}
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def save_chat_history(chat_history):
    with open('chat_history.json', 'w') as f:
        json.dump(chat_history, f, default=serialize_bytesio)

def load_chat_history():
    try:
        with open('chat_history.json', 'r') as f:
            return json.load(f, object_hook=deserialize_bytesio)
    except FileNotFoundError:
        return {}

def load_css():
    with open('app/styles.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def get_image_base64(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()

def save_credentials(creds):
    try:
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    except Exception as e:
        print(f'Error saving credentials: {str(e)}')

