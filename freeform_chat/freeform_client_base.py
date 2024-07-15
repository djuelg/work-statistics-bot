
ROLE_ASSISTANT = 'assistant'
ROLE_USER = 'user'
ROLE_SYSTEM = 'system'


class FreeformClientBase:
    def generate_responses(self, messages, context_descriptions="", is_oneshot=False):
        pass
