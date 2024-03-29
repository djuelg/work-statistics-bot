from conversation.content.generic_messages import GoodbyeMessage, YawningCatSticker, \
    ProblematicDataMessage, HelloAgainMessage, CumulatedStatisticsMessage, \
    FrequentDimensionsMessage
from conversation.message_types import Message, ImageGroupMessage


def create_monthly_conversation(stats, images):
    messages = [HelloAgainMessage(), ]
    if images:
        messages.extend([MonthlyIntroductionMessage(), CumulatedStatisticsMessage(stats), ImageGroupMessage(images),
                         FrequentDimensionsMessage(stats), MonthlyGoodbyeMessage(), YawningCatSticker()])
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
        "Okay, das wars mit der monatlichen Zusammenfassung. Hab einen schönen Abend!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
