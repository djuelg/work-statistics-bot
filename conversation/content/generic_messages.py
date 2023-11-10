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


class MorningMessage(Message):
    PROMPTS = [
        "Guten Morgen!",
        "Hey!",
        "Hallo, ich wünsche einen guten Morgen.",
        # Add more greetings here
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)