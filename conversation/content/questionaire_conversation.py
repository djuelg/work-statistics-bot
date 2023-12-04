import random

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


class WhatElseMessage(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.what_else'
    STATES = [("Weiter...", "Weiter..."), ("Was kann ich sonst noch tun?", CALLBACK_KEY)]

    def __init__(self, text):
        super().__init__(text, self.CALLBACK_KEY, WhatElseMessage.remedy_callback, self.STATES)

    @staticmethod
    def remedy_callback(key, value, cengine=None, is_multi_answer_finished=False):
        if value == WhatElseMessage.CALLBACK_KEY:
            return [
                Message(text="- *Den Kreislauf aktivieren:* Bspw. wenn du stehend arbeitest, kurz spazieren gehst, oder eine kleine Sport- oder Yoga-Routine einlegst. \n"
                             "- *Sprich mit jemandem:* Führe ein kurzes Gespräch mit jemandem in deiner Nähe, oder rufe Freunde an. \n"
                             "- *Schreib deine Gedanken auf:* Falls niemand in der Nähe ist, oder du keine Lust hast deine Situation mit jemandem zu besprechen, kann es auch hilfreich sein, deine Gedanken zu verschriftlichen. \n"
                             "- *Eine Achtsamkeitsübung machen:* Bspw. sich ein paar Momente für Meditation oder Atemübungen zu nehmen \n"
                             "- *Mach etwas anderes:* Erledige etwas kleines, wofür du eher die Muße hast und mach danach mit deiner eigentlichen Aufgabe weiter. \n"),
                Message(
                    text="In einigen Situation kann auch folgendes hilfreich sein:"),
            ]
        else:
            return [Message(text="Okay, das wars erstmal.")]


class MentalFatigueExpert:
    def __init__(self, cengine, key_base):
        self._cengine = cengine
        self._key_base = key_base

    def run(self):
        return [
            Message(text="*Zum Thema mentale Ermüdung:* \n"
                         "Denk daran, dass mentale Ermüdung durch anhaltende mentale Anstrengungen entsteht. "
                         "Häufig geht sie mit einem Gefühl von Unlust weiterzumachen einher. "
                         "Dein Körper versucht also dir zu vermitteln, mehr Pausen einzulegen."),
            WhatElseMessage(text="Lass es ruhig angehen, und mache etwas was dich mental entlastet: Ein paar Minuten nicht sitzen, vielleicht etwas an die frische Luft gehen, oder ein paar Minuten dösen. "
                                 "Bei mentaler Ermüdung kann es auch helfen viele kurze Pausen zu machen, wie bei der Pomodoro Methode. Dafür kannst du dich z.B. an @pomodoro_timer_bot wenden."),
        ]


class QuestionnaireEvaluationExpert:
    STATE_EXPERTS = {
        "stress_state": "Stress",
        "sleepiness_state": "Schlaf",
        "mental_fatigue_state": MentalFatigueExpert,
        "energy_state": "Energie", # TODO: Ggf. Energetisch und wach, dafür sleepiness droppen
        "anxiety_state": "Anstalt"
    }

    def __init__(self, cengine, key_base):
        self._cengine = cengine
        self._key_base = key_base

    def _create_mood_state_statistics(self):
        mood_states = self._cengine.get_state(self._key_base)
        mood_states = {key: mood_states[key] for key in mood_states if key in self.STATE_EXPERTS.keys()}
        avg_mood = round(sum(mood_states.values()) / len(mood_states.values()), 2)
        most_severe_states = {key: value for key, value in mood_states.items() if value == 5}
        if not most_severe_states:
            most_severe_states = {key: value for key, value in mood_states.items() if value == 4}
        return mood_states, most_severe_states, avg_mood

    def run(self):
        responses = []
        mood_states, most_severe_states, avg_mood = self._create_mood_state_statistics()

        if most_severe_states or avg_mood >= 3.75:
            responses.append(Message(text="Gut, danke"))

            if avg_mood >= 3.75:
                responses.append(Message(text=f"Mit einem Durchschnitt von {avg_mood}/5 scheinst du deine Situation insgesamt als problematisch eingeschätzt zu haben."))
                # TODO: Hier, bisschen was dazu sagen entspannt zu machen und die GenericRemedyMessage einfügen
            else:
                responses.append(Message(text=f"Mit einem Schnitt von {avg_mood}/5 scheinst du nur einzelne Dimensionen als problematisch eingeschätzt zu haben."))

            if most_severe_states:
                most_severe_two = random.sample(list(most_severe_states.items()), k=2) \
                    if len(most_severe_states.items())  >= 2 else list(most_severe_states.items())
                if avg_mood >= 3.75 and most_severe_two[0][1] == 5:
                    expert = self.STATE_EXPERTS[most_severe_two[0][0]](self._cengine, self._key_base)
                    responses.extend(expert.run())
                else:
                    for state_pair in most_severe_two:
                        expert = self.STATE_EXPERTS[state_pair[0]](self._cengine, self._key_base)
                        responses.extend(expert.run())

        # TODO: Veränderungen zu vormittag / gestern einarbeiten

        responses.reverse()
        return responses


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