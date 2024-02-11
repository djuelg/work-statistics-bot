import random

from conversation.message_types import Message, StickerMessage, FreeformMessage, SingleAnswerMessage

NAME_KEY = 'username'

MATRIX_LINK = "https://www.orghandbuch.de/OHB/DE/OrganisationshandbuchNEU/4_MethodenUndTechniken/Methoden_A_bis_Z/Eisenhower_Matrix/Eisenhower_Matrix_node.html"
SPORT_LINK = "https://www.youtube.com/results?search_query=5+minute+warmup+tabata"
YOGA_LINK = "https://www.youtube.com/results?search_query=easy+10+minute+yoga-routine"
MEDITATION_LINK = "https://www.youtube.com/results?search_query=10+minute+guided+meditation"
BREATHING_LINK = "https://www.youtube.com/results?search_query=5+minute+breathing+exercise"


def remedy_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if value == WhatElseMessage.ANSWER_WHAT_ELSE:
        return [
            Message(text="Meist lohnt es sich ein paar Minuten Arbeitszeit zu opfern und die Aufgaben danach wieder mit einem frischeren Kopf anzugehen"),
                GenericRemedyMessage(),
            Message(
                text=["In einigen Situation kann auch folgendes hilfreich sein:", "Je nach Situation kann auch folgendes hilfreich sein:"]),
        ]
    elif value == WhatElseMessage.ANSWER_FREETEXT:
        return [FreeformMessage(text=["Okay, dann schieß los!", "Gut, erzähl mal."])]
    else:
        return [Message(text=["Okay, das wars erstmal.", "Dann wars das erstmal.", "Gut, dann wars das vorerst."])]


class GenericRemedyMessage(Message):
    PROMPTS = [
        f"• *Den Kreislauf aktivieren:* Bspw. wenn du stehend arbeitest, kurz spazieren gehst, oder eine kleine [Sport-]({SPORT_LINK}) "
        f"oder [Yoga-Routine]({YOGA_LINK}) einlegst. \n"
         "• *Sprich mit jemandem:* Führe ein kurzes Gespräch mit jemandem in deiner Nähe, oder rufe Freunde an. \n"
         "• *Schreib deine Gedanken auf:* Nimm dir kurz Zeit, um deine Gedanken auf Papier zu bringen. Das kann helfen, sie zu ordnen und einen klaren Kopf zu bekommen. \n"
         f"• *Eine Achtsamkeitsübung machen:* Sich ein paar Momente für bspw. [Meditation]({MEDITATION_LINK}) oder [Atemübungen]({BREATHING_LINK}) nehmen \n"
         "• *Mach etwas anderes:* Erledige etwas kleines, wofür du eher die Muße hast und mach danach mit deiner eigentlichen Aufgabe weiter. \n"
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class WhatElseMessage(SingleAnswerMessage):
    WHAT_ELSE_CALLBACK_KEY = 'daily_questionnaire.remedy.what_else'
    ANSWER_ENOUGH = f'{WHAT_ELSE_CALLBACK_KEY}.ANSWER_ENOUGH'
    ANSWER_WHAT_ELSE = f'{WHAT_ELSE_CALLBACK_KEY}.ANSWER_WHAT_ELSE'
    ANSWER_FREETEXT = f'{WHAT_ELSE_CALLBACK_KEY}.ANSWER_FREETEXT'
    STATES = [
        [("Das reicht an Infos", ANSWER_ENOUGH)],
        [("Was kann ich sonst noch tun?", ANSWER_WHAT_ELSE)],
        [("Ich möchte meine Situation beschreiben", ANSWER_FREETEXT)]
    ]

    def __init__(self, text, callback=remedy_callback):
        super().__init__(text, self.WHAT_ELSE_CALLBACK_KEY, callback, self.STATES)


class ExpertSpecificationQuestion(SingleAnswerMessage):
    SPECIFY_CALLBACK_KEY = 'daily_questionnaire.remedy.expert_specification'
    PROMPTS = [
        "Möchtest du ein Thema im speziellen besprechen?",
        "Gibt es ein Thema, dass du genauer besprechen möchtest?",
    ]
    ANSWER_NO = ("Nein danke", "ANSWER_NO")

    def __init__(self, callback, answers):
        formatted_answers = [[answer] for answer in [*answers, self.ANSWER_NO]]
        super().__init__(self.PROMPTS, self.SPECIFY_CALLBACK_KEY, callback, formatted_answers)


class HelloMessage(Message):
    PROMPTS = [
        "Hey{}! Ich bins wieder.",
        "Hallo{}, da bin ich wieder.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

    def content(self, cengine=None):
        name = " " + cengine.get_state(NAME_KEY) if random.random() <= 0.4 else ""
        self._content.text = self._content.text.format(name)
        return self._content


class ThumbsUpCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoYeNlhK4C3Eqmy297ceXoI6W1E5KnPAACP0YAAg_EKEh1NETO709qWDME"

    def __init__(self):
        super(ThumbsUpCatSticker, self).__init__(self.ID)


class YawningCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoqbFllvUQEINFMjoeyEX8MIMqolKw-AACwUQAAotwIUiVbldFvH-vkDQE"

    def __init__(self):
        super(YawningCatSticker, self).__init__(self.ID)


class WavingCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoYcNlhKgRGBOYzALHxGMGkThWelkThQACaUMAAmBJKUgZplO_8QeEJDME"

    def __init__(self):
        super(WavingCatSticker, self).__init__(self.ID)

class ByeCatSticker(StickerMessage):
    ID = "CAACAgIAAxkBAAEoaJdlhxeWjLMTKwySrHEBZHN2daALxAACIkQAAgnJIEiTYD5CYYFWczME"

    def __init__(self):
        super(ByeCatSticker, self).__init__(self.ID)


class GoodbyeMessage(Message):
    PROMPTS = [
        "Mach's gut!",
        "Bis später!",
        "Bis dann!",
        "Bis bald!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class MorningMessage(Message):
    PROMPTS = [
        "Guten Morgen{}!",
        "Hey{}!",
        "Hallo{}, ich wünsche einen guten Morgen.",
        "Hey{}, guten Morgen.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

    def content(self, cengine=None):
        name = " " + cengine.get_state(NAME_KEY) if random.random() <= 0.4 else ""
        self._content.text = self._content.text.format(name)
        return self._content
