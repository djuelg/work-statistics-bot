from conversation.content.generic_messages import GoodbyeMessage, MorningMessage
from conversation.content.questionaire_conversation import StressQuestion, \
    SleepinessQuestion, MentalFatigueQuestion, MoodQuestion, QuestionnaireEvaluationMessage, \
    EnergyQuestion, AnxietyQuestion, TasksQuestion
from conversation.engine import Message

MORNING_TASKS_KEY = 'daily_questionnaire.morning.tasks'
MORNING_ENERGY_KEY = 'daily_questionnaire.morning.energy_state'
MORNING_STRESS_KEY = 'daily_questionnaire.morning.stress_state'
MORNING_ANXIETY_KEY = 'daily_questionnaire.morning.anxiety_state'
MORNING_SLEEPINESS_KEY = 'daily_questionnaire.morning.sleepiness_state'
MORNING_MENTAL_FATIGUE_KEY = 'daily_questionnaire.morning.mental_fatigue_state'
MORNING_MOOD_KEY = 'daily_questionnaire.morning.mood_state'


def create_morning_conversation():
    return [
        MorningMessage(),
        TasksQuestion(MORNING_TASKS_KEY),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(MORNING_ENERGY_KEY),
        SleepinessQuestion(MORNING_SLEEPINESS_KEY),
        AnxietyQuestion(MORNING_ANXIETY_KEY),
        MentalFatigueQuestion(MORNING_MENTAL_FATIGUE_KEY),
        StressQuestion(MORNING_STRESS_KEY),
        MoodQuestion(MORNING_MOOD_KEY),
        QuestionnaireEvaluationMessage([MORNING_STRESS_KEY, MORNING_SLEEPINESS_KEY, MORNING_MENTAL_FATIGUE_KEY]),
        GoodbyeMessage()
    ]


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns durch ein paar Aussagen deinen aktuellen Blick auf die Welt einordnen. Bewerte diese bitte auf "
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
