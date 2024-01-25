from openai import OpenAI

from conversation.engine import FreeformClientBase


class FreeformClient(FreeformClientBase):
    ROLE_SYSTEM = 'system'
    GPT_MODEL = "gpt-3.5-turbo-1106"

    def __init__(self, openai_key, context_description):
        self.client = OpenAI(api_key=openai_key)
        self.context_description = context_description

    def generate_responses(self, messages):
        openai_formatted_messages = [
            {"role": self.ROLE_SYSTEM, "content": self.context_description},
            *[{"role": m[0], "content": m[1]} for m in messages]
        ]
        response = self.client.chat.completions.create(
            model=self.GPT_MODEL,
            messages=openai_formatted_messages,
            temperature=0.7,
            max_tokens=200
        )
        return [m.message.content for m in response.choices] if response.choices else []
