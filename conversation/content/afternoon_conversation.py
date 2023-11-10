from conversation.content.generic_messages import GoodbyeMessage, HelloMessage
from conversation.content.questionaire_conversation import StressQuestion, \
    SleepinessQuestion, MentalFatigueQuestion, MoodQuestion, QuestionnaireEvaluationMessage, \
    EnergyQuestion, AnxietyQuestion, TasksQuestion
from conversation.engine import Message, SingleAnswerMessage, update_state_single_answer_callback

AFTERNOON_POSITIVE_PROGRESS_KEY = 'daily_questionnaire.afternoon.positive_progress'
AFTERNOON_TASKS_KEY = 'daily_questionnaire.afternoon.tasks'
AFTERNOON_ENERGY_KEY = 'daily_questionnaire.afternoon.energy_state'
AFTERNOON_STRESS_KEY = 'daily_questionnaire.afternoon.stress_state'
AFTERNOON_ANXIETY_KEY = 'daily_questionnaire.afternoon.anxiety_state'
AFTERNOON_SLEEPINESS_KEY = 'daily_questionnaire.afternoon.sleepiness_state'
AFTERNOON_MENTAL_FATIGUE_KEY = 'daily_questionnaire.afternoon.mental_fatigue_state'
AFTERNOON_MOOD_KEY = 'daily_questionnaire.afternoon.mood_state'


def create_afternoon_conversation():
    return [
        HelloMessage(),
        PositiveProgressQuestion(AFTERNOON_POSITIVE_PROGRESS_KEY),
        PositiveProgressReaction(),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(AFTERNOON_ENERGY_KEY),
        SleepinessQuestion(AFTERNOON_SLEEPINESS_KEY),
        AnxietyQuestion(AFTERNOON_ANXIETY_KEY),
        MentalFatigueQuestion(AFTERNOON_MENTAL_FATIGUE_KEY),
        StressQuestion(AFTERNOON_STRESS_KEY),
        MoodQuestion(AFTERNOON_MOOD_KEY),
        TasksQuestion(AFTERNOON_TASKS_KEY),
        QuestionnaireEvaluationMessage([AFTERNOON_STRESS_KEY, AFTERNOON_SLEEPINESS_KEY, AFTERNOON_MENTAL_FATIGUE_KEY]),
        GoodbyeMessage()
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Mal sehen wie sich deine Selbsteinschätzung gegenüber heute morgen verändert hat. "
        "Bitte bewerte die folgenden Aussagen auf"
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'."
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class PositiveProgressQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Hast du das Gefühl mit deinen morgendlichen Aufgaben gut vorangekommen zu sein? "
    ]
    STATES = ["Ja", "Eher nicht"]

    def __init__(self, key):
        self.KEY = key
        super().__init__(self.PROMPTS, update_state_single_answer_callback, self.STATES)


class PositiveProgressReaction(Message):

    def __init__(self):
        super().__init__("")

    def content(self, cengine=None):
        positive_progress = cengine.get_state(AFTERNOON_POSITIVE_PROGRESS_KEY)
        if positive_progress == "Ja":
            self._content.text += "Okay, schön zu hören. "
        else:
            self._content.text += "Okay, dann stellt sich die Frage, was das Problem sein könnte. "
        return self._content
