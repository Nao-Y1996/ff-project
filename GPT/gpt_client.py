import openai

from ff import settings


class GPT:
    def __init__(self, model: str = None, setting: str = None, setting_file_path: str = None):
        openai.api_key = settings.OPENAI_API_KEY
        self._system_prompts = []
        self._user_prompts = []
        self._assistant_prompts = []
        self._messages = []
        self._model = "gpt-3.5-turbo"
        if model is not None:
            self._model = model
        if setting is not None and setting_file_path is None:
            self.add_setting(setting)
        if setting is None and setting_file_path is not None:
            file = open(setting_file_path, "r")
            self.add_setting(file.read())
            file.close()

    def rebuild_messages(self, past_prompts: list[dict]):
        for prompt in past_prompts:
            self._messages.append(prompt)
        return self

    def add_prompt(self, prompt: dict):
        self._messages.append(prompt)
        return self

    def add_setting(self, setting: str):
        prompt = {
            "role": "system",
            "content": setting
        }
        self._system_prompts.append(prompt)
        self._messages.append(prompt)
        return self

    def add_user_message(self, message: str):
        prompt = {
            "role": "user",
            "content": message
        }
        self._user_prompts.append(prompt)
        self._messages.append(prompt)
        return self

    def add_assistant_message(self, message: str):
        prompt = {
            "role": "assistant",
            "content": message
        }
        self._assistant_prompts.append(prompt)
        self._messages.append(prompt)
        return self

    def latest_system_prompt(self):
        return self._system_prompts[-1]

    def latest_user_prompt(self):
        return self._user_prompts[-1]

    def latest_assistant_prompt(self):
        return self._assistant_prompts[-1]

    def request(self):

        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self._messages,
            timeout=2
        )

        response_message = res["choices"][0]["message"]["content"]
        self.add_assistant_message(response_message)
        return response_message
