import random

from conversation.engine import Message

NAME_KEY = 'username'


class HelloMessage(Message):
    PROMPTS = [
        "Hey{}! Ich bins wieder.",
        "Hallo{}, da bin ich wieder.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

    def content(self, cengine=None):
        name = " " + cengine.get_state(NAME_KEY) if random.random() <= 0.2 else ""
        self._content.text = self._content.text.format(name)
        return self._content


class GoodbyeMessage(Message):
    PROMPTS = [
        "Mach's gut!",
        "Bis später!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class MorningMessage(Message):
    PROMPTS = [
        "Guten Morgen{}!",
        "Hey{}!",
        "Hallo{}, ich wünsche einen guten Morgen.",
        # Add more greetings here
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

    def content(self, cengine=None):
        name = " " + cengine.get_state(NAME_KEY) if random.random() <= 0.2 else ""
        self._content.text = self._content.text.format(name)
        return self._content
