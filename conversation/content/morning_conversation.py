from conversation.content.generic_messages import GoodbyeMessage, MorningMessage, WavingCatSticker
from conversation.content.questionaire_conversation import StressQuestion, \
    MentalFatigueQuestion, MoodQuestion, EnergyQuestion, TasksQuestion, finalize_questionnaire_callback
from conversation.content.questionnaire_evaluation import KEY_GROUPING_MORNING
from conversation.engine import Message



def create_morning_conversation():
    return [
        MorningMessage(),
        TasksQuestion(KEY_GROUPING_MORNING),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(KEY_GROUPING_MORNING),
        # AnxietyQuestion(KEY_GROUPING_MORNING),
        StressQuestion(KEY_GROUPING_MORNING),
        MentalFatigueQuestion(KEY_GROUPING_MORNING),
        MoodQuestion(KEY_GROUPING_MORNING, callback=finalize_questionnaire_callback),
        WavingCatSticker(),
        GoodbyeMessage()
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns durch ein paar Aussagen deinen aktuellen Blick auf die Welt einordnen. Bewerte diese bitte auf "
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
