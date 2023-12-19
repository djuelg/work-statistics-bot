from conversation.content.generic_messages import GoodbyeMessage, HelloMessage
from conversation.content.questionaire_conversation import StressQuestion, \
    MentalFatigueQuestion, MoodQuestion, EnergyQuestion, TasksQuestion, finalize_questionnaire_callback
from conversation.content.questionnaire_evaluation import KEY_GROUPING_AFTERNOON
from conversation.engine import Message, SingleAnswerMessage, update_state_single_answer_callback


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
        MoodQuestion(KEY_GROUPING_AFTERNOON),  # TODO: Ggf. allgemeine happiness Question
        TasksQuestion(KEY_GROUPING_AFTERNOON, callback=finalize_questionnaire_callback),
        GoodbyeMessage()
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Mal sehen wie sich deine Selbsteinschätzung jetzt zum Nachmittag entwickelt hat. "
        "Bitte bewerte die folgenden Aussagen auf"
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'."
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class PositiveProgressQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.positive_progress'
    PROMPTS = [
        "Hast du das Gefühl mit deinen morgendlichen Aufgaben gut vorangekommen zu sein? "
    ]
    STATES = ["Ja", "Eher nicht"]

    def __init__(self, key_grouping):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), update_state_single_answer_callback, self.STATES)


class PositiveProgressReaction(Message):
    CALLBACK_KEY = 'daily_questionnaire.{}.positive_progress'

    def __init__(self):
        super().__init__("")

    def content(self, cengine=None):
        positive_progress = cengine.get_state(self.CALLBACK_KEY.format(KEY_GROUPING_AFTERNOON))
        if positive_progress == "Ja":
            self._content.text += "Okay, schön zu hören. "
        else:
            self._content.text += "Okay, dann stellt sich die Frage, was das Problem sein könnte. "
        return self._content
