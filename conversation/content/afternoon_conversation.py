from conversation.content.generic_messages import GoodbyeMessage, HelloMessage
from conversation.content.questionaire_conversation import QuestionnaireIntroductionMessage, \
    StressQuestion, SleepinessQuestion, MentalFatigueQuestion, MoodQuestion, QuestionnaireEvaluationMessage

AFTERNOON_STRESS_KEY = 'daily_questionnaire.afternoon.stress_state'
AFTERNOON_SLEEPINESS_KEY = 'daily_questionnaire.afternoon.sleepiness_state'
AFTERNOON_MENTAL_FATIGUE_KEY = 'daily_questionnaire.afternoon.mental_fatigue_state'
AFTERNOON_MOOD_KEY = 'daily_questionnaire.afternoon.mood_state'


def create_afternoon_conversation():
    return [
        HelloMessage(),
        QuestionnaireIntroductionMessage(),
        StressQuestion(AFTERNOON_STRESS_KEY),
        SleepinessQuestion(AFTERNOON_SLEEPINESS_KEY),
        MentalFatigueQuestion(AFTERNOON_MENTAL_FATIGUE_KEY),
        MoodQuestion(AFTERNOON_MOOD_KEY),
        QuestionnaireEvaluationMessage([AFTERNOON_STRESS_KEY, AFTERNOON_SLEEPINESS_KEY, AFTERNOON_MENTAL_FATIGUE_KEY]),
        GoodbyeMessage()
    ]

