import random

from conversation.engine import SingleAnswerMessage, Message

GENERIC_REMEDY_STATE_KEY = "current_conversation.is_generic_remedy_shown"

BAD_MOOD_CONSTANT = 4
GOOD_MOOD_CONSTANT = 2


class GenericRemedyMessage(Message):
    PROMPTS = [
        "- *Den Kreislauf aktivieren:* Bspw. wenn du stehend arbeitest, kurz spazieren gehst, oder eine kleine Sport- oder Yoga-Routine einlegst. \n"
         "- *Sprich mit jemandem:* Führe ein kurzes Gespräch mit jemandem in deiner Nähe, oder rufe Freunde an. \n"
         "- *Schreib deine Gedanken auf:* Falls niemand in der Nähe ist, oder du keine Lust hast deine Situation mit jemandem zu besprechen, kann es auch hilfreich sein, deine Gedanken zu verschriftlichen. \n"
         "- *Eine Achtsamkeitsübung machen:* Bspw. sich ein paar Momente für Meditation oder Atemübungen zu nehmen \n"
         "- *Mach etwas anderes:* Erledige etwas kleines, wofür du eher die Muße hast und mach danach mit deiner eigentlichen Aufgabe weiter. \n"
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


def remedy_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if value == WhatElseMessage.CALLBACK_KEY:
        return [
            GenericRemedyMessage(),
            Message(
                text="In einigen Situation kann auch folgendes hilfreich sein:"),
        ]
    else:
        return [Message(text="Okay, das wars erstmal.")]


class WhatElseMessage(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.what_else'
    STATES = [("Das reicht an Infos", "True"), ("Was kann ich sonst noch tun?", CALLBACK_KEY)]

    def __init__(self, text, callback=remedy_callback):
        super().__init__(text, self.CALLBACK_KEY, callback, self.STATES)


class MentalFatigueExpert:
    def __init__(self, cengine, key_base):
        self._cengine = cengine
        self._key_base = key_base

    def run(self):
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        responses = [Message(text="*Zum Thema mentale Ermüdung:* \n"
                         "Denk daran, dass mentale Ermüdung durch anhaltende mentale Anstrengungen entsteht. "
                         "Häufig geht sie mit einem Gefühl von Unlust weiterzumachen einher. "
                         "Dein Körper versucht also dir zu vermitteln, mehr Pausen einzulegen.")]
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(Message(text="Lass es ruhig angehen, und mache etwas was dich mental entlastet: Ein paar Minuten nicht sitzen, vielleicht etwas an die frische Luft gehen, oder ein paar Minuten dösen. "
                                 "Bei mentaler Ermüdung kann es auch helfen viele kurze Pausen zu machen, wie bei der oben genannten Pomodoro Methode."))
        else:
            responses.append(WhatElseMessage(text="Lass es ruhig angehen, und mache etwas was dich mental entlastet: Ein paar Minuten nicht sitzen, vielleicht etwas an die frische Luft gehen, oder ein paar Minuten dösen. "
                                 "Bei mentaler Ermüdung kann es auch helfen viele kurze Pausen zu machen, wie bei der Pomodoro Methode. Dafür kannst du dich z.B. an @pomodoro_timer_bot wenden."),
        )
        return responses

    def remedy_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        responses = self.run()
        responses.reverse()
        return responses


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
        med_mood = int(sorted(mood_states.values())[len(mood_states) // 2])
        most_severe_states = {key: value for key, value in mood_states.items() if value == 5}
        if not most_severe_states:
            most_severe_states = {key: value for key, value in mood_states.items() if value == 4}
        return mood_states, most_severe_states, avg_mood, med_mood

    def run(self):
        responses = []
        mood_states, most_severe_states, avg_mood, med_mood = self._create_mood_state_statistics()

        if not most_severe_states and med_mood < BAD_MOOD_CONSTANT:
            responses.append(Message(text="Gut, danke"))
            if med_mood <= GOOD_MOOD_CONSTANT:
                responses.append(Message(text=f"Es freut mich, dass es dir relativ gut zu gehen scheint."))
            else:
                responses.append(Message(text=f"Deine Angaben ergeben einen Durchschnitt von {med_mood}/5, wobei nichts besonders problematisch erscheint. Viel Erfolg bei der restlichen Arbeit."))
        elif most_severe_states or med_mood >= BAD_MOOD_CONSTANT:
            most_severe_two = random.sample(list(most_severe_states.items()), k=2) \
                if len(most_severe_states.items()) >= 2 else list(most_severe_states.items())
            responses.append(Message(text="Gut, danke"))

            if med_mood >= BAD_MOOD_CONSTANT:
                responses.append(Message(text=f"Mit einem Durchschnitt von {med_mood}/5 scheinst du allgemein in keiner guten Situation zu sein."))
                responses.append(Message(text=f"Ich würde dir empfehlen nicht allzu hohe Erwartungen an dich zu haben, nicht "
                                              f"länger als nötig zu arbeiten und dir häufiger mal eine kurze Auszeit zu nehmen. "
                                              f"Diese kannst du dann z.B. für folgendes nutzen:"))
                responses.append(GenericRemedyMessage())

                if most_severe_two and most_severe_two[0][1] == 5:
                    expert = self.STATE_EXPERTS[most_severe_two[0][0]](self._cengine, self._key_base)
                    responses.append(WhatElseMessage(
                        text=f"Um die Auszeiten nicht zu vergessen, kannst du es auch mit der Pomodoro-Methode probieren. Bspw. mithilfe von @pomodoro_timer_bot",
                        callback=expert.remedy_callback
                    ))
                else:
                    responses.append(Message(
                        text=f"Um die Auszeiten nicht zu vergessen, kannst du es auch mit der Pomodoro-Methode probieren. Bspw. mithilfe von @pomodoro_timer_bot"
                    ))
                self._cengine.update_state(GENERIC_REMEDY_STATE_KEY, True)

            else:
                responses.append(Message(text=f"Mit einem Schnitt von {med_mood}/5 scheinst du nur einzelne Dimensionen als problematisch eingeschätzt zu haben."))

                if most_severe_two:
                    if med_mood >= BAD_MOOD_CONSTANT and most_severe_two[0][1] == 5:
                        expert = self.STATE_EXPERTS[most_severe_two[0][0]](self._cengine, self._key_base)
                        responses.extend(expert.run())
                    else:
                        for state_pair in most_severe_two:
                            expert = self.STATE_EXPERTS[state_pair[0]](self._cengine, self._key_base)
                            responses.extend(expert.run())

        # TODO: Veränderungen zu vormittag / gestern einarbeiten

        responses.reverse()
        return responses


