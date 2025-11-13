# Cluster 9

@dataclass
class UserInfo:
    user_name: str | None = None
    name: str | None = None
    description: str | None = None
    profile: dict[str, Any] | None = None
    recsys_type: str = 'twitter'
    is_controllable: bool = False

    def to_custom_system_message(self, user_info_template: TextPrompt) -> str:
        required_keys = user_info_template.key_words
        info_keys = set(self.profile.keys())
        missing = required_keys - info_keys
        extra = info_keys - required_keys
        if missing:
            raise ValueError(f'Missing required keys in UserInfo.profile: {missing}')
        if extra:
            warnings.warn(f'Extra keys not used in UserInfo.profile: {extra}')
        return user_info_template.format(**self.profile)

    def to_system_message(self) -> str:
        if self.recsys_type != 'reddit':
            return self.to_twitter_system_message()
        else:
            return self.to_reddit_system_message()

    def to_twitter_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
        system_content = f"\n# OBJECTIVE\nYou're a Twitter user, and I'll present you with some posts. After you see the posts, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n        "
        return system_content

    def to_reddit_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
                print(self.profile['other_info'])
                description += f'You are a {self.profile['other_info']['gender']}, {self.profile['other_info']['age']} years old, with an MBTI personality type of {self.profile['other_info']['mbti']} from {self.profile['other_info']['country']}.'
        system_content = f"\n# OBJECTIVE\nYou're a Reddit user, and I'll present you with some tweets. After you see the tweets, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n"
        return system_content

def to_system_message(self) -> str:
    if self.recsys_type != 'reddit':
        return self.to_twitter_system_message()
    else:
        return self.to_reddit_system_message()

