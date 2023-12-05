from conversation.content.questionnaire_evaluation import QuestionnaireEvaluationExpert
from conversation.engine import SingleAnswerMessage, MultiAnswerMessage, update_state_multi_answer_callback, update_state_single_answer_callback


# def combine_key_and_states(key, states):
#     if isinstance(states[0], list):
#         responses = [combine_key_and_states(key, state) for state in states]
#     else:
#         responses = ["::>".join([key, state]) for state in states]
#     return responses


class TasksQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.tasks'
    PROMPTS = [
        "Was steht in den nächsten Stunden an? "
        "Wähle gerne aus den Beispielen unten, oder beschreibe selbst was ansteht."
    ]
    STATES = [
        ["Coding", "Bugfixing", "Doku schreiben"],
        ["Testen", "Ops-Aufgaben", "Konzeptionieren"],
        ["Fertig"]
    ]

    def __init__(self, key_grouping, callback=update_state_multi_answer_callback):
        super(TasksQuestion, self).__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)


def finalize_questionnaire_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if not is_multi_answer_finished:
        update_state_multi_answer_callback(key, value, cengine, is_multi_answer_finished=is_multi_answer_finished)
        return

    key_base = ".".join(key.split(".")[0:2])
    evaluation_expert = QuestionnaireEvaluationExpert(cengine, key_base)
    return evaluation_expert.run()


def update_reversed_numeric_answer_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if not is_multi_answer_finished:
        reverse_value = 6 - float(value)
        cengine.update_state(key, reverse_value)


class EnergyQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.energy_state'

    PROMPTS = [
        "Ich fühle mich energetisch. "
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key_grouping, callback=update_reversed_numeric_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)


class AnxietyQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.anxiety_state'
    PROMPTS = [
        "Ich fühle mich unruhig und nervös. "
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key_grouping, callback=update_state_single_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)


class StressQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.stress_state'
    PROMPTS = [
        "Ich fühle mich gestresst. "
        # "Dieser kann sich z.B. ausdrücken durch Empfindungen wie Unruhe oder leichte Reizbarkeit",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key_grouping, callback=update_state_single_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)


class SleepinessQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.sleepiness_state'
    PROMPTS = [
        "Ich fühle mich körperlich ermüdet. "
        # "Dies kann z.B. durch schlechten Schlaf entstehen und zu Kraftlosigkeit oder Unkonzentriertheit führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key_grouping):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), update_state_single_answer_callback, self.STATES)


class MentalFatigueQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.mental_fatigue_state'
    PROMPTS = [
        "Ich fühle mich geistig ermüdet. "
        # "Dies kann z.B. durch anhaltende geistige Arbeiten entstehen und zu Konzentrationsproblemen,"
        # "  Motivationslosigkeit und Unlust führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key_grouping, callback=update_state_single_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)


class MoodQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.{}.mood_state'
    PROMPTS = [
        "Versuche abschließend deine Laune mit den folgenden Begriffen zu beschreiben."
    ]
    STATES = [
        ["fröhlich", "glücklich", "produktiv"],
        ["müde", "genervt", "gestresst"],
        ["motiviert", "dankbar", "verliebt"],
        ["traurig", "wütend", "erschöpft"],
        ["ruhig", "unruhig", "ausgeglichen"],
        ["unsicher", "krank", "schlapp"],
        ["zufrieden", "gleichgültig", "stolz"],
        ["Fertig"]
    ]

    def __init__(self, key_grouping, callback=update_state_multi_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY.format(key_grouping), callback, self.STATES)
