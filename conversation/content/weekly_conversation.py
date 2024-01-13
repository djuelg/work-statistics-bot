from conversation.content.generic_messages import GoodbyeMessage, MorningMessage, YawningCatSticker
from conversation.engine import Message, ImageGroupMessage


def create_weekly_conversation(images):
    messages = [MorningMessage(), ]
    if images:
        messages.extend([WeeklyIntroductionMessage(), ImageGroupMessage(images), WeeklyReflectionMessage(),
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


class WeeklyReflectionMessage(Message):
    PROMPTS = [
        "Sollten Dimensionen konstant im höheren Bereich liegen, nimm dir am Besten Zeit darüber nachzudenken woran das liegen könnte "
        "und was du tun kannst um deine Umstände zu verbessern. Vielleicht fallen die Werte aber auch besser aus als du gedacht hättest."
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

class ProblematicDataMessage(Message):
    PROMPTS = [
        "Leider konnte ich diese Woche keine Statistiken aus deinen Angaben erzeugen. Dann eben nächstes mal wieder!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

class WeeklyGoodbyeMessage(Message):
    PROMPTS = [
        "Gut, das wars für heute auch schon wieder. Hab einen schönen und hoffentlich entspannten Tag!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
