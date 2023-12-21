import random

from conversation.engine import Message, StickerMessage

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


class ThumbsUpCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoYeNlhK4C3Eqmy297ceXoI6W1E5KnPAACP0YAAg_EKEh1NETO709qWDME"

    def __init__(self):
        super(StickerMessage, self).__init__(self.ID)


class WavingCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoYcNlhKgRGBOYzALHxGMGkThWelkThQACaUMAAmBJKUgZplO_8QeEJDME"

    def __init__(self):
        super(StickerMessage, self).__init__(self.ID)


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
