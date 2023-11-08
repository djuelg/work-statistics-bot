from conversation.engine import Message


class HelloMessage(Message):
    PROMPTS = [
        "Hey! Ich bins wieder.",
        "Hallo, da bin ich wieder.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class GoodbyeMessage(Message):
    PROMPTS = [
        "Mach's gut!",
        "Bis später!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)