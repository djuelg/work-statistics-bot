from conversation.content.generic_messages import GoodbyeMessage, MorningMessage, WavingCatSticker
from conversation.content.questionaire_conversation import StressQuestion, \
    MentalFatigueQuestion, MoodQuestion, EnergyQuestion, TasksQuestion, finalize_questionnaire_callback, \
    MotivationQuestion
from conversation.content.questionnaire_evaluation import KEY_GROUPING_MORNING
from conversation.message_types import Message


def create_morning_conversation():
    return [
        MorningMessage(),
        TasksQuestion(KEY_GROUPING_MORNING),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(KEY_GROUPING_MORNING),
        # AnxietyQuestion(KEY_GROUPING_MORNING),
        StressQuestion(KEY_GROUPING_MORNING),
        MentalFatigueQuestion(KEY_GROUPING_MORNING),
        MotivationQuestion(KEY_GROUPING_MORNING),
        MoodQuestion(KEY_GROUPING_MORNING, callback=finalize_questionnaire_callback),
        GoodbyeMessage(),
        WavingCatSticker(),
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns durch ein paar Aussagen deinen aktuellen Blick auf die Welt einordnen. Bewerte diese bitte auf "
        "einer Skala von *Eins* ➔ _\"trifft gar nicht zu\"_ bis *Fünf* ➔ _\"trifft vollkommen zu\"_.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
