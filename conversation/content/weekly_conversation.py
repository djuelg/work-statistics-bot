from conversation.content.generic_messages import GoodbyeMessage, MorningMessage, YawningCatSticker, HelloAgainMessage, \
    ProblematicDataMessage, ReflectionMessage
from conversation.message_types import Message, ImageGroupMessage


def create_weekly_conversation(images):
    messages = [MorningMessage(), ]
    if images:
        messages.extend([WeeklyIntroductionMessage(), ImageGroupMessage(images), ReflectionMessage(),
                         WeeklyGoodbyeMessage(), YawningCatSticker()])
    else:
        messages.extend([ProblematicDataMessage(), GoodbyeMessage(), YawningCatSticker()])
    return messages


class WeeklyIntroductionMessage(Message):
    PROMPTS = [
        "Hier die wöchentliche Zusammenfassung deiner Angaben:"
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class WeeklyGoodbyeMessage(Message):
    PROMPTS = [
        "Gut, das wars für heute auch schon wieder. Hab einen schönen und hoffentlich entspannten Tag!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
