# Cluster 22

class Prompter:

    @staticmethod
    def get_prompter(prompter: Union[Dict[str, Any], None]):
        if not prompter:
            return Prompter.default()
        assert isinstance(prompter, dict)
        prompter_name = prompter.get('name', None)
        prompter_args = prompter.get('args', {})
        if hasattr(Prompter, prompter_name) and callable(getattr(Prompter, prompter_name)):
            return getattr(Prompter, prompter_name)(**prompter_args)
        return Prompter.default()

    @staticmethod
    def default():
        return Prompter.role_content_dict()

    @staticmethod
    def batched_role_content_dict(*args, **kwargs):
        base = Prompter.role_content_dict(*args, **kwargs)

        def batched(messages):
            result = base(messages)
            return {key: [result[key]] for key in result}
        return batched

    @staticmethod
    def role_content_dict(message_key: str='messages', role_key: str='role', content_key: str='content', user_role: str='user', agent_role: str='agent'):

        def prompter(messages: List[Dict[str, str]]):
            nonlocal message_key, role_key, content_key, user_role, agent_role
            role_dict = {'user': user_role, 'agent': agent_role}
            prompt = []
            for item in messages:
                prompt.append({role_key: role_dict[item['role']], content_key: item['content']})
            return {message_key: prompt}
        return prompter

    @staticmethod
    def prompt_string(prefix: str='', suffix: str='AGENT:', user_format: str='USER: {content}\n\n', agent_format: str='AGENT: {content}\n\n', prompt_key: str='prompt'):

        def prompter(messages: List[Dict[str, str]]):
            nonlocal prefix, suffix, user_format, agent_format, prompt_key
            prompt = prefix
            for item in messages:
                if item['role'] == 'user':
                    prompt += user_format.format(content=item['content'])
                else:
                    prompt += agent_format.format(content=item['content'])
            prompt += suffix
            print(prompt)
            return {prompt_key: prompt}
        return prompter

    @staticmethod
    def claude():
        return Prompter.prompt_string(prefix='', suffix='Assistant:', user_format='Human: {content}\n\n', agent_format='Assistant: {content}\n\n')

    @staticmethod
    def palm():

        def prompter(messages):
            return {'instances': [Prompter.role_content_dict('messages', 'author', 'content', 'user', 'bot')(messages)]}
        return prompter

def batched(messages):
    result = base(messages)
    return {key: [result[key]] for key in result}

