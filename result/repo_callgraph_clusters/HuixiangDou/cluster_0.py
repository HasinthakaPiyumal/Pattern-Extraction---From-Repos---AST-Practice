# Cluster 0

def get_wechat_on_message_url(suffix: str) -> str:
    endpoint = HuixiangDouEnv.get_message_endpoint()
    return endpoint + 'api/v1/message/v1/wechat/' + suffix

def get_lark_on_message_url() -> str:
    endpoint = HuixiangDouEnv.get_message_endpoint()
    return endpoint + 'api/v1/message/v1/lark'

