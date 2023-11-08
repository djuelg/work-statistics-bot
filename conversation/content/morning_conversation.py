from conversation.content.generic_messages import GoodbyeMessage
from conversation.content.questionaire_conversation import QuestionnaireIntroductionMessage, \
    StressQuestion, SleepinessQuestion, MentalFatigueQuestion, MoodQuestion, QuestionnaireEvaluationMessage
from conversation.engine import Message

MORNING_STRESS_KEY = 'daily_questionnaire.morning.stress_state'
MORNING_SLEEPINESS_KEY = 'daily_questionnaire.morning.sleepiness_state'
MORNING_MENTAL_FATIGUE_KEY = 'daily_questionnaire.morning.mental_fatigue_state'
MORNING_MOOD_KEY = 'daily_questionnaire.morning.mood_state'


def create_morning_conversation():
    return [
        MorningMessage(),
        QuestionnaireIntroductionMessage(),
        StressQuestion(MORNING_STRESS_KEY),
        SleepinessQuestion(MORNING_SLEEPINESS_KEY),
        MentalFatigueQuestion(MORNING_MENTAL_FATIGUE_KEY),
        MoodQuestion(MORNING_MOOD_KEY),
        QuestionnaireEvaluationMessage([MORNING_STRESS_KEY, MORNING_SLEEPINESS_KEY, MORNING_MENTAL_FATIGUE_KEY]),
        GoodbyeMessage()
    ]


class MorningMessage(Message):
    PROMPTS = [
        "Guten Morgen!",
        "Hey!",
        "Hallo, ich wünsche einen guten Morgen.",
        # Add more greetings here
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


