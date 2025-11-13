# Cluster 80

class SlackHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        self.token = kwargs.get('token')
        self.channel_name = kwargs.get('channel')

    def connect(self):
        try:
            self.client = WebClient(token=self.token)
            return DBHandlerStatus(status=True)
        except Exception as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        TODO: integrate code for disconnecting from slack
        """
        raise NotImplementedError()

    def check_connection(self) -> DBHandlerStatus:
        try:
            self.client.api_test()
        except SlackApiError as e:
            assert e.response['ok'] is False
            return False
        return True

    def get_tables(self) -> DBHandlerResponse:
        if self.client:
            channels = self.client.conversations_list(types='public_channel,private_channel')['channels']
            self.channel_names = [c['name'] for c in channels]
            tables_df = pd.DataFrame(self.channel_names, columns=['table_name'])
            return DBHandlerResponse(data=tables_df)

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        columns = ['ts', 'text', 'message_created_at', 'user', 'channel', 'reactions', 'attachments', 'thread_ts', 'reply_count', 'reply_users_count', 'latest_reply', 'subtype', 'hidden']
        columns_df = pd.DataFrame(columns, columns=['column_name'])
        return DBHandlerResponse(data=columns_df)

    def post_message(self, message) -> DBHandlerResponse:
        try:
            response = self.client.chat_postMessage(channel=self.channel, text=message)
            return DBHandlerResponse(data=response['message']['text'])
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def _convert_json_response_to_DataFrame(self, json_response):
        messages = json_response['messages']
        columns = ['text', 'ts', 'user']
        data_df = pd.DataFrame(columns=columns)
        for message in messages:
            if message['text'] and message['ts'] and message['user']:
                data_df.loc[len(data_df.index)] = [message['text'], message['ts'], message['user']]
        return data_df

    def get_messages(self) -> DBHandlerResponse:
        try:
            channels = self.client.conversations_list(types='public_channel,private_channel')['channels']
            channel_ids = {c['name']: c['id'] for c in channels}
            response = self.client.conversations_history(channel=channel_ids[self.channel_name])
            data_df = self._convert_json_response_to_DataFrame(response)
            return data_df
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def del_message(self, timestamp) -> DBHandlerResponse:
        try:
            self.client.chat_delete(channel=self.channel, ts=timestamp)
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def execute_native_query(self, query_string: str) -> DBHandlerResponse:
        """
        TODO: integrate code for executing query on slack
        """
        raise NotImplementedError()

def check_connection(self) -> DBHandlerStatus:
    try:
        self.client.api_test()
    except SlackApiError as e:
        assert e.response['ok'] is False
        return False
    return True

