from conversation.content.generic_messages import GoodbyeMessage, MorningMessage, YawningCatSticker, \
    ProblematicDataMessage, ReflectionMessage, HelloAgainMessage
from conversation.message_types import Message, ImageGroupMessage


def create_monthly_conversation(images):
    messages = [HelloAgainMessage(), ]
    if images:
        messages.extend([MonthlyIntroductionMessage(), ImageGroupMessage(images), ReflectionMessage(),
                         MonthlyGoodbyeMessage(), YawningCatSticker()])
    else:
        messages.extend([ProblematicDataMessage(), GoodbyeMessage(), YawningCatSticker()])
    return messages


class MonthlyIntroductionMessage(Message):
    PROMPTS = [
        "Es ist Ende des Monats und da gibt es natürlich auch ein paar monatliche Statistiken"
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class MonthlyGoodbyeMessage(Message):
    PROMPTS = [
        "Okay, ich hoffe die Grafiken waren hilfreich. Hab einen schönen Abend!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
