import random

from conversation.content.generic_messages import GoodbyeMessage, HelloMessage, WavingCatSticker
from conversation.content.questionaire_conversation import StressQuestion, \
    MentalFatigueQuestion, MoodQuestion, EnergyQuestion, TasksQuestion, finalize_questionnaire_callback, \
    MotivationQuestion
from conversation.content.questionnaire_evaluation import KEY_GROUPING_AFTERNOON
from conversation.engine import update_state_single_answer_callback
from conversation.message_types import Message, SingleAnswerMessage


def create_afternoon_conversation():
    return [
        HelloMessage(),
        PositiveProgressQuestion(KEY_GROUPING_AFTERNOON),
        PositiveProgressReaction(),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(KEY_GROUPING_AFTERNOON),
        # AnxietyQuestion(KEY_GROUPING_AFTERNOON),
        StressQuestion(KEY_GROUPING_AFTERNOON),
        MentalFatigueQuestion(KEY_GROUPING_AFTERNOON),
        MotivationQuestion(KEY_GROUPING_AFTERNOON),
        MoodQuestion(KEY_GROUPING_AFTERNOON),
        TasksQuestion(KEY_GROUPING_AFTERNOON, callback=finalize_questionnaire_callback),
        GoodbyeMessage(),
        WavingCatSticker(),
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns schauen, wie sich deine Selbsteinschätzung jetzt zum Nachmittag entwickelt hat. "
        "Bitte bewerte die folgenden Aussagen auf einer Skala von "
        "*Eins* ➔ _\"trifft gar nicht zu\"_ bis *Fünf* ➔ _\"trifft vollkommen zu\"_."
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class PositiveProgressQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.positive_progress'
    PROMPTS = [
        "Hast du das Gefühl mit deinen morgendlichen Aufgaben gut vorangekommen zu sein? ",
        "Bist du gut mit deinen morgendlichen Aufgaben vorangekommen? ",
        "Hat in Hinblick auf deine morgendlichen Aufgaben alles geklappt? ",
        "Ging in Hinblick auf deine morgendlichen Aufgaben alles nach Plan? ",
    ]
    STATES = ["Ja", "Eher nicht"]

    def __init__(self, key_grouping):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), update_state_single_answer_callback, self.STATES)


class PositiveProgressReaction(Message):
    CALLBACK_KEY = 'daily_questionnaire.{}.positive_progress'
    POSITIVE_REACTION = ["Okay, schön zu hören. ", "Das freut mich zu hören!"]
    NEGATIVE_REACTION = ["Tut mir leid zu hören. ", "Oh, das tut mir leid."]

    def __init__(self):
        super().__init__("")

    def content(self, cengine=None):
        positive_progress = cengine.get_state(self.CALLBACK_KEY.format(KEY_GROUPING_AFTERNOON))
        if positive_progress == "Ja":
            self._content.text += random.choice(self.POSITIVE_REACTION)
        else:
            self._content.text += random.choice(self.NEGATIVE_REACTION)
        return self._content
