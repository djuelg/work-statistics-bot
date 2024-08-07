import random
from datetime import datetime

from conversation.content.generic_messages import GoodbyeMessage, HelloMessage, WavingCatSticker, \
    FREEFORM_CLIENT_DESCRIPTIONS_ONESHOT
from conversation.content.questionaire_conversation import StressQuestion, \
    MentalFatigueQuestion, MoodQuestion, EnergyQuestion, TasksQuestion, finalize_questionnaire_callback, \
    MotivationQuestion
from conversation.content.questionnaire_evaluation import KEY_GROUPING_AFTERNOON, KEY_GROUPING_MORNING, \
    QuestionnaireEvaluationExpert
from conversation.engine import update_state_single_answer_callback, DAILY_QUESTIONNAIRE_KEY
from conversation.message_types import Message, SingleAnswerMessage, FreeformMessage


def create_afternoon_conversation():
    return [
        HelloMessage(),
        MorningSummary(),
        PositiveProgressQuestion(KEY_GROUPING_AFTERNOON),
        QuestionnaireIntroductionMessage(),
        EnergyQuestion(KEY_GROUPING_AFTERNOON),
        StressQuestion(KEY_GROUPING_AFTERNOON),
        MentalFatigueQuestion(KEY_GROUPING_AFTERNOON),
        MotivationQuestion(KEY_GROUPING_AFTERNOON),
        MoodQuestion(KEY_GROUPING_AFTERNOON),
        TasksQuestion(KEY_GROUPING_AFTERNOON, callback=finalize_questionnaire_callback),
        GoodbyeMessage(),
        WavingCatSticker(),
    ]


class MorningSummary(Message):

    def __init__(self):
        super().__init__("")

    def content(self, cengine=None):
        morning_tasks = cengine.get_state(TasksQuestion.CALLBACK_KEY.format(KEY_GROUPING_MORNING))
        if morning_tasks:
            self._content.text = "Du hattest dir ja folgendes vorgenommen: \n"
            for task in morning_tasks:
                self._content.text += f"• {task} \n"
        return self._content


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
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), respond_to_positive_progress_callback, self.STATES)


def create_questionnaire_summary(morning_results):
    try:
        return f"Stimmungsfragebogen {datetime.now().date()} vormittags: " \
               f"{QuestionnaireEvaluationExpert.STATE_NAMES['stress_state']}: {int(morning_results['stress_state'])}/5, " \
               f"{QuestionnaireEvaluationExpert.STATE_NAMES['mental_fatigue_state']}: {int(morning_results['mental_fatigue_state'])}/5, " \
               f"{QuestionnaireEvaluationExpert.STATE_NAMES['energy_state']}: {int(morning_results['energy_state'])}/5, " \
               f"{QuestionnaireEvaluationExpert.STATE_NAMES['motivation_state']}: {int(morning_results['motivation_state'])}/5."
    except:
        return ""


def respond_to_positive_progress_callback(key, value, cengine=None, is_multi_answer_finished=False):
    update_state_single_answer_callback(key, value, cengine, is_multi_answer_finished=is_multi_answer_finished)
    morning_results = cengine.get_state(f"{DAILY_QUESTIONNAIRE_KEY}.{KEY_GROUPING_MORNING}")
    morning_summary = create_questionnaire_summary(morning_results)
    context_descriptions = [*FREEFORM_CLIENT_DESCRIPTIONS_ONESHOT, f"Die User Angaben diesen Morgen waren im {morning_summary}. "
                            f"Gehe auf dieses Ergebnis, sowie die Aussagen des Users zu den morgendlichen Aufgaben ein."]

    if value == "Ja":
        return [Message(text=["Okay, schön zu hören. ", "Das freut mich zu hören!"])]
    else:
        return [FreeformMessage(text=["Tut mir leid zu können. Was war das Problen?",
                                     "Oh, das tut mir leid. Wo lag das Problen?"],
                               has_freeform_chaining=False,
                               context_descriptions=context_descriptions)]


# TODO: Remove as soon as ptb user_data does not rely on cengine anymore (after migration)
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
