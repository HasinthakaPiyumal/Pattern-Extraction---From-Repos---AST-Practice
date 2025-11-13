# Cluster 0

def handle_oauth_callback():
    if 'code' in st.query_params:
        try:
            flow = Flow.from_client_secrets_file('client_secret.json', scopes=SCOPES, redirect_uri=get_redirect_uri())
            flow.fetch_token(code=st.query_params['code'])
            st.session_state['google_auth_token'] = flow.credentials.to_json()
            st.success('Successfully authenticated with Google!')
            st.query_params.clear()
        except Exception as e:
            st.error(f'Error during OAuth callback: {str(e)}')

def loading_animation(process_func, *args, **kwargs):
    loading_placeholder = st.empty()
    result = None
    start_time = time.time()
    while result is None:
        elapsed_time = time.time() - start_time
        if elapsed_time > 30:
            loading_placeholder.error('Request timed out. Please try again.')
            return None
        loading_message = get_loading_message()
        with st.spinner(loading_message):
            try:
                result = process_func(*args, **kwargs)
            except Exception as e:
                loading_placeholder.error(f'An error occurred: {str(e)}. Retrying...')
                time.sleep(1)
    loading_placeholder.empty()
    st.success('Done!')
    return result

def initiate_google_auth():
    if not os.path.exists('client_secret.json'):
        st.error('Google Sheets integration is not set up correctly.')
        st.markdown('Please follow the setup guide for Google Sheets integration in the [CyberScraper-2077 README](https://github.com/itsOwen/CyberScraper-2077/blob/main/README.md#setup-google-sheets-authentication).')
        st.info("Once you've completed the setup, restart the application.")
        return
    flow = Flow.from_client_secrets_file('client_secret.json', scopes=SCOPES, redirect_uri=get_redirect_uri())
    authorization_url, state = flow.authorization_url(prompt='consent')
    st.session_state['oauth_state'] = state
    st.markdown(f'Please visit this URL to authorize the application: [Auth URL]({authorization_url})')
    st.info("After authorizing, you'll be redirected back to this app. Then you can proceed with uploading.")

def get_google_sheets_credentials():
    if not os.path.exists('client_secret.json'):
        return None
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f'Error loading credentials from file: {str(e)}')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds)
            except Exception as e:
                print(f'Error refreshing credentials: {str(e)}')
                creds = None
        else:
            creds = None
    if not creds:
        if 'google_auth_token' in st.session_state:
            try:
                creds = Credentials.from_authorized_user_info(json.loads(st.session_state['google_auth_token']), SCOPES)
                save_credentials(creds)
            except Exception as e:
                print(f'Error creating credentials from session state: {str(e)}')
    return creds

def display_google_sheets_button(data, unique_key):
    if not os.path.exists('client_secret.json'):
        st.warning('Google Sheets integration is not set up.')
        st.markdown('To enable Google Sheets integration, please follow the setup guide in the [CyberScraper-2077 README](https://github.com/itsOwen/CyberScraper-2077/blob/main/README.md#setup-google-sheets-authentication).')
        return
    creds = get_google_sheets_credentials()
    if not creds:
        auth_button = '🔑 Authorize Google Sheets'
        if st.button(auth_button, key=f'auth_sheets_{unique_key}', help='Authorize access to Google Sheets'):
            initiate_google_auth()
    else:
        upload_button = '✅ Upload to Google Sheets'
        if st.button(upload_button, key=f'upload_{unique_key}', help='Upload data to Google Sheets'):
            with st.spinner('Uploading to Google Sheets...'):
                spreadsheet_id = upload_to_google_sheets(data)
                if spreadsheet_id:
                    st.success(f'Hey Choom! Data uploaded successfully. Spreadsheet ID: {spreadsheet_id}')
                    st.markdown(f'[Open Spreadsheet](https://docs.google.com/spreadsheets/d/{spreadsheet_id})')
                else:
                    st.error('Failed to upload data to Google Sheets. Check the console for error details.')

