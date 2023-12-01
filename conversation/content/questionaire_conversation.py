from conversation.engine import Message, SingleAnswerMessage, MultiAnswerMessage, update_state_multi_answer_callback, update_state_single_answer_callback


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

    responses = []

    key_base = ".".join(key.split(".")[0:2])
    mood_states = cengine.get_state(key_base)
    number_keys = ["stress_state", "sleepiness_state", "mental_fatigue_state", "energy_state", "anxiety_state"]
    mood_states = {key: mood_states[key] for key in mood_states if key in number_keys}

    # TODO evaluate and return list
    # gibt es ein Problem in einer bestimmten Kategorie oder allgemein?
    # falls allgemein
    # lass es ab jetzt lieber etwas langsamer angehen
    # vielleicht erleichtert eines der fogelnden Dinge die Arbeit:
    # aufgaben vorschlagen jenachdem welche werte am höchsten sind
    # falls einzelne Kategorie
    # konkrete tipps und aufgaben für kategorie

    avg_mood = round(sum(mood_states.values()) / len(mood_states.values()), 2)
    # get all keys where value is 5
    most_severe = [key for key, value in mood_states.items() if value == 5]
    if not most_severe:
        most_severe = [key for key, value in mood_states.items() if value == 4]

    if avg_mood >= 3.75:
        responses.append(Message(text=f"Im Mittel ergeben deine Angaben einen Wert von {avg_mood}."))
        responses.append(Message(text="Du scheinst allgemein nicht so fit zu sein heute, lass es entspannt angehen und mach nicht zu lange."))

    if most_severe:
        most_severe_shortened = [key.split('.')[-1] for key in most_severe]
        responses.append(Message(text='Besonders schlimm sind: ' + ', '.join(most_severe_shortened)))
        pass  # TODO: Hier sollte eine Evaluation kommen was das Problem ist damit konkret darauf eingegangen werden kann
        # TODO: Auch mit Vorschlägen von Aufgaben
    else:
        pass  # TODO: Hier sollten allgemeine Aufgaben/Verhalten vorgeschlagen werden, die vll hilfreich sein könnten

    # TODO Veränderungen zum morgen / gestern einarbeiten

    return responses


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


class QuestionnaireEvaluationMessage(Message):
    PROMPTS = [
        "Alles klar, danke für deine Zeit!\n",
    ]

    def __init__(self, keys):
        self.KEYS = keys
        super().__init__(self.PROMPTS)

    def content(self, cengine=None):
        avg_mood_states = [cengine.get_state(key) for key in self.KEYS]

        avg_mood = round(sum(avg_mood_states) / len(avg_mood_states), 2)
        self._content.text += f"Im Mittel ergeben deine Aussagen einen Wert von {avg_mood}"
        if avg_mood < 3:
            self._content.text += ", was relativ niedrig ist. Das freut mich :)\n"
        elif avg_mood >= 3.75:
            self._content.text += ". Das ist recht hoch. Also lass es ab jetzt lieber etwas langsamer angehen...\n"
        else:
            self._content.text += "."
        return self._content