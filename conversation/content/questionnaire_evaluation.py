import random

from conversation.engine import SingleAnswerMessage, Message

GENERIC_REMEDY_STATE_KEY = "current_conversation.is_generic_remedy_shown"
KEY_GROUPING_AFTERNOON = 'afternoon'
KEY_GROUPING_MORNING = 'morning'

BAD_MOOD_CONSTANT = 4
GOOD_MOOD_CONSTANT = 2

MATRIX_LINK = "https://www.orghandbuch.de/OHB/DE/OrganisationshandbuchNEU/4_MethodenUndTechniken/Methoden_A_bis_Z/Eisenhower_Matrix/Eisenhower_Matrix_node.html"
SPORT_LINK = "https://www.youtube.com/results?search_query=5+minute+warmup+tabata"
YOGA_LINK = "https://www.youtube.com/results?search_query=easy+10+minute+yoga-routine"
MEDITATION_LINK = "https://www.youtube.com/results?search_query=10+minute+guided+meditation"
BREATHING_LINK = "https://www.youtube.com/results?search_query=5+minute+breathing+exercise"


class GenericRemedyMessage(Message):
    PROMPTS = [
        f"- *Den Kreislauf aktivieren:* Bspw. wenn du stehend arbeitest, kurz spazieren gehst, oder eine kleine [Sport-]({SPORT_LINK}) "
        f"oder [Yoga-Routine]({YOGA_LINK}) einlegst. \n"
         "- *Sprich mit jemandem:* Führe ein kurzes Gespräch mit jemandem in deiner Nähe, oder rufe Freunde an. \n"
         "- *Schreib deine Gedanken auf:* Falls niemand in der Nähe ist, oder du keine Lust hast deine Situation mit jemandem zu besprechen, kann es auch hilfreich sein, deine Gedanken zu verschriftlichen. \n"
         f"- *Eine Achtsamkeitsübung machen:* Bspw. sich ein paar Momente für [Meditation]({MEDITATION_LINK}) oder [Atemübungen]({BREATHING_LINK}) zu nehmen \n"
         "- *Mach etwas anderes:* Erledige etwas kleines, wofür du eher die Muße hast und mach danach mit deiner eigentlichen Aufgabe weiter. \n"
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


def remedy_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if value == WhatElseMessage.CALLBACK_KEY:
        return [
            Message(text="Meist lohnt es sich ein paar Minuten Arbeitszeit zu opfern und die Aufgaben danach wieder mit einem frischeren Kopf anzugehen"),
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


class GenericExpert:
    def __init__(self, cengine, key_base):
        self._cengine = cengine
        self._key_base = key_base

    def run(self):
        raise NotImplementedError("Must be implemented by subclass")

    def remedy_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        responses = self.run()
        responses.reverse()
        return responses


class StressExpert(GenericExpert):
    STRESS_INTRODUCTION = "*Zum Thema Stress:* \n" \
                          "Stress lässt sich natürlich nicht immer vermeiden. " \
                          "Versuche deine Tage in stressigen Phasen pragmatisch zu planen: " \
                          "Kümmere dich zuerst um die wirklich wichtigen Dinge und versuche es zu akzeptieren, falls du nicht alles schaffst. Das ist in Ordnung. " \
                          f"Bei der Planung kann dir z.B. eine To-Do Liste oder die [Eisenhower Matrix]({MATRIX_LINK}) helfen"
    REMEDY_MEDITATION = f"[Achtsamkeitsübungen]({MEDITATION_LINK}) können helfen Stress abzubauen. Sie können jedoch auch problematisch sein, " \
                        "wenn du sie nur als weiteres To-Do in deinem schon vollen Tag betrachtest. Vor dem Arbeitsalltag, " \
                        "oder anstelle von Zeit auf sozialen Medien sind gute Möglichkeiten Achtsamkeitsübungen in den Tag einzubauen."
    REMEDY_RELAX = "Nach der Arbeit solltest du dir möglichst Zeit zur Entspannung nehmen. " \
                   "Wenn das nicht möglich ist, setze dir doch schonmal eine feste Zeit zum Entspannen in der Zuknft."

    def run(self):
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        responses = [Message(text=self.STRESS_INTRODUCTION),
                     Message(text=self.REMEDY_RELAX)
                     ]

        # TODO History: Auf andauernden Stress eingehen
        # TODO Später: Z.B. Fragen ob Achtsamkeitsübungen überhaupt für einen etwas sind
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(Message(text=self.REMEDY_MEDITATION))
        else:
            responses.append(WhatElseMessage(text=self.REMEDY_MEDITATION))
        return responses


class MentalFatigueExpert(GenericExpert):
    MENTAL_FATIGUE_INTRODUCTION = "*Zum Thema mentale Ermüdung:* \n" \
                                  "Denk daran, dass mentale Ermüdung durch anhaltende mentale Anstrengungen entsteht. " \
                                  "Häufig geht sie mit einem Gefühl von Unlust weiterzumachen einher. " \
                                  "Dein Körper versucht also dir zu vermitteln, mehr Pausen einzulegen."
    REMEDY_SLOW_DOWN = "Lass es ruhig angehen, und mache etwas was dich mental entlastet: Ein paar Minuten nicht sitzen, vielleicht etwas an die frische Luft gehen, oder ein paar Minuten dösen. "
    REMEDY_PAUSES_1 = "Bei mentaler Ermüdung kann es auch helfen viele kurze Pausen zu machen, wie bei der oben genannten Pomodoro Methode."
    REMEDY_PAUSES_2 = "Bei mentaler Ermüdung kann es auch helfen viele kurze Pausen zu machen, wie bei der Pomodoro Methode. Dafür kannst du dich z.B. an @pomodoro\_timer\_bot wenden."

    def run(self):
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        responses = [Message(text=self.MENTAL_FATIGUE_INTRODUCTION)]
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(Message(self.REMEDY_SLOW_DOWN + self.REMEDY_PAUSES_1))
        else:
            responses.append(WhatElseMessage(self.REMEDY_SLOW_DOWN + self.REMEDY_PAUSES_2))
        return responses


class SleepinessExpert(GenericExpert):
    SLEEPINESS_HEADLINE = "*Zum Thema wenig Energie und Schläfrigkeit:* \n"
    SLEEPINESS_INTRODUCTION_1 = "Es ist völlig normal und in Ordnung sich am Morgen energielos zu fühlen. "
    SLEEPINESS_INTRODUCTION_2 = "Sich im Laufe des Tages und vor allem am frühen Nachmittag müde oder energielos zu fühlen ist ganz normal. " \
                                "Nimm dir für diese Zeit eher leichte Aufgaben vor und lass es entspannt angehen. "
    SLEEPINESS_INTRODUCTION_3 = "Denk daran regelmäßig Pausen zu machen und genug zu trinken. " \
                                "Falls möglich arbeite ein bisschen im Stehen und nutze die Pausen um dich kurz zu bewegen. "
    REMEDY_NAP = "Solltest du schlecht oder zu kurz geschlafen haben, wird dir außer einem Nap vermutlich nicht viel helfen, " \
                 "also wenn du die Zeit dafür hast nimm sie dir gerne. In Maßen können auch proteinreiche Snacks oder koffeinhaltige Getränke helfen."
    REMEDEY_POMODORO = "Um sie nicht zu vergessen empfehle ich dir die Pomodoro Methode und dafür z.B. den Bot @pomodoro\_timer\_bot zu nutzen."

    def run(self):
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        introduction = self.SLEEPINESS_HEADLINE
        introduction += self.SLEEPINESS_INTRODUCTION_1 if KEY_GROUPING_MORNING in self._key_base \
            else self.SLEEPINESS_INTRODUCTION_2
        introduction += self.SLEEPINESS_INTRODUCTION_3
        responses = [Message(text=introduction)]
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(Message(text=self.REMEDY_NAP))
        else:
            responses.append(Message(text=self.REMEDEY_POMODORO))
            responses.append(WhatElseMessage(text=self.REMEDY_NAP))
        return responses


class QuestionnaireEvaluationExpert(GenericExpert):
    THANKS = "Gut, danke"
    HAPPY_RESPONSE = f"Es freut mich, dass es dir relativ gut zu gehen scheint! Dann will ich gar nicht weiter stören."
    MEDIOCRE_RESPONSE = "Deine Angaben sind mit einem Durchschnitt von {}/5 im mittleren Bereich, wobei nichts besonders problematisch erscheint. " \
                        "Wenn du dich nicht in Topform fühlst, lass es einfach etwas ruhiger angehen. Viel Erfolg bei der restlichen Arbeit."
    SOME_BAD_RESPONSE = "Deine Bewertung ergibt einen Durchschnitt von {}/5, und es lässt sich erkennen, dass du bestimmte Aspekte des Tages als anspruchsvoll empfunden hast."
    BAD_RESPONSE = "Der Durchschnitt von {}/5 deutet darauf hin, dass es dir allgemein nicht so gut zu gehen scheint."
    REMEDY_LOW_EXPECTATIONS = f"Ich würde dir empfehlen nicht allzu hohe Erwartungen an dich zu haben, nicht " \
                              f"länger als nötig zu arbeiten und dir häufiger mal eine kurze Auszeit zu nehmen. " \
                              f"Diese kannst du dann z.B. für folgendes nutzen:"
    REMEDEY_POMODORO = f"Um die Auszeiten nicht zu vergessen, kannst du es auch mit der Pomodoro-Methode probieren. Bspw. mithilfe von @pomodoro\_timer\_bot"

    STATE_NAMES = {
        "stress_state": "Stress Level",
        "mental_fatigue_state": "Mentale Ermüdung",
        "energy_state": "Schläfrigkeit",
    }
    STATE_EXPERTS = {
        "stress_state": StressExpert,
        "mental_fatigue_state": MentalFatigueExpert,
        "energy_state": SleepinessExpert,
    }

    def _create_mood_state_statistics(self):
        mood_states = self._cengine.get_state(self._key_base)
        mood_states = {key: mood_states[key] for key in mood_states if key in self.STATE_EXPERTS.keys()}
        avg_mood = round(sum(mood_states.values()) / len(mood_states.values()), 2)
        med_mood = int(sorted(mood_states.values())[len(mood_states) // 2])
        most_severe_states = {key: value for key, value in mood_states.items() if value == 5}
        if not most_severe_states:
            most_severe_states = {key: value for key, value in mood_states.items() if value == 4}
        return mood_states, most_severe_states, avg_mood, med_mood

    def short_evaluation(self, mood_states):
        answer = f"*Zusammengefasst waren deine Angaben:* \n"
        for key, value in mood_states.items():
            answer += f"{self.STATE_NAMES[key]}: *{int(value)}*/5 \n"
        return answer


    def run(self):
        responses = []
        mood_states, most_severe_states, avg_mood, med_mood = self._create_mood_state_statistics()

        if not most_severe_states and med_mood < BAD_MOOD_CONSTANT:
            responses.append(Message(text=self.THANKS))
            responses.append(Message(text=self.short_evaluation(mood_states)))
            if med_mood <= GOOD_MOOD_CONSTANT:
                responses.append(Message(text=self.HAPPY_RESPONSE))
            else:
                responses.append(Message(text=self.MEDIOCRE_RESPONSE.format(med_mood)))
        elif most_severe_states or med_mood >= BAD_MOOD_CONSTANT:
            most_severe_two = random.sample(list(most_severe_states.items()), k=2) \
                if len(most_severe_states.items()) >= 2 else list(most_severe_states.items())
            responses.append(Message(text=self.THANKS))
            responses.append(Message(text=self.short_evaluation(mood_states)))

            if med_mood >= BAD_MOOD_CONSTANT:
                responses.append(Message(text=self.BAD_RESPONSE.format(med_mood)))
                responses.append(Message(text=self.REMEDY_LOW_EXPECTATIONS))
                responses.append(GenericRemedyMessage())

                if most_severe_two and most_severe_two[0][1] == 5:
                    expert = self.STATE_EXPERTS[most_severe_two[0][0]](self._cengine, self._key_base)
                    responses.append(WhatElseMessage(text=self.REMEDEY_POMODORO, callback=expert.remedy_callback))
                else:
                    responses.append(Message(text=self.REMEDEY_POMODORO))
                self._cengine.update_state(GENERIC_REMEDY_STATE_KEY, True)

            else:
                responses.append(Message(text=self.SOME_BAD_RESPONSE.format(med_mood)))

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


