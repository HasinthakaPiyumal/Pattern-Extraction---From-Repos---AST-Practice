# Cluster 16

class PromptManager:

    def __init__(self):
        self.config_dir = Path.home() / '.grunty'
        self.config_file = self.config_dir / 'prompts.json'
        self.current_prompt = self.load_prompt()

    def load_prompt(self) -> str:
        """Load the system prompt from the config file or return the default"""
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True)
            if not self.config_file.exists():
                self.save_prompt(DEFAULT_SYSTEM_PROMPT)
                return DEFAULT_SYSTEM_PROMPT
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        except Exception as e:
            print(f'Error loading prompt: {e}')
            return DEFAULT_SYSTEM_PROMPT

    def save_prompt(self, prompt: str) -> bool:
        """Save the system prompt to the config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'system_prompt': prompt}, f, indent=2)
            self.current_prompt = prompt
            return True
        except Exception as e:
            print(f'Error saving prompt: {e}')
            return False

    def reset_to_default(self) -> bool:
        """Reset the system prompt to the default value"""
        return self.save_prompt(DEFAULT_SYSTEM_PROMPT)

    def get_current_prompt(self) -> str:
        """Get the current system prompt"""
        return self.current_prompt

def __init__(self):
    self.config_dir = Path.home() / '.grunty'
    self.config_file = self.config_dir / 'prompts.json'
    self.current_prompt = self.load_prompt()

