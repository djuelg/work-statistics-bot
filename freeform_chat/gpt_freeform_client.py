from openai import OpenAI

from freeform_chat.freeform_client_base import FreeformClientBase

GPT3_MODEL = "gpt-3.5-turbo"
GPT4_MODEL = "gpt-4o"


class FreeformClient(FreeformClientBase):

    def __init__(self, openai_key, context_descriptions):
        self.client = OpenAI(api_key=openai_key)
        self.context_descriptions = context_descriptions

    def generate_responses(self, messages, context_descriptions=None, is_oneshot=False, max_tokens=200, model=None):
        if not context_descriptions:
            context_descriptions = self.context_descriptions
        if not model:
            model = GPT3_MODEL

        openai_formatted_messages = [
            *[{"role": self.ROLE_SYSTEM, "content": descr} for descr in context_descriptions],
            *[{"role": m[0], "content": m[1]} for m in messages],
        ]
        response = self.client.chat.completions.create(
            model=model,
            messages=openai_formatted_messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        if is_oneshot and '?' in response.choices[0].message.content:
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_formatted_messages,
                temperature=0.7,
                max_tokens=max_tokens
            )

        return [m.message.content for m in response.choices] if response.choices else []
