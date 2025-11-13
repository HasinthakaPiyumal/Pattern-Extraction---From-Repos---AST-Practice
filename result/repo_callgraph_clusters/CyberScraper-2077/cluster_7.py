# Cluster 7

def get_date_group(date_str):
    date = datetime.strptime(date_str, '%Y-%m-%d')
    today = datetime.now().date()
    if date.date() == today:
        return 'Today'
    elif date.date() == today - timedelta(days=1):
        return 'Yesterday'
    elif date.date() > today - timedelta(days=7):
        return date.strftime('%A')
    else:
        return date.strftime('%B %d, %Y')

def upload_to_google_sheets(data):
    creds = get_google_sheets_credentials()
    if not creds:
        return None
    try:
        service = build('sheets', 'v4', credentials=creds)
        spreadsheet = {'properties': {'title': f'CyberScraper Data {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'}}
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        if isinstance(data, pd.DataFrame):
            df = clean_data_for_sheets(data)
        else:
            return None
        values = [df.columns.tolist()] + df.values.tolist()
        body = {'values': values}
        result = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range='Sheet1', valueInputOption='RAW', body=body).execute()
        return spreadsheet_id
    except HttpError as error:
        print(f'An HTTP error occurred: {error}')
        return None
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None

