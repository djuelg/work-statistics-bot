import random

from conversation.content.generic_messages import WhatElseMessage, MEDITATION_LINK, remedy_callback, \
    GenericRemedyMessage, ExpertSpecificationQuestion
from conversation.message_types import Message, FreeformMessage

GENERIC_REMEDY_STATE_KEY = "current_conversation.is_generic_remedy_shown"
KEY_GROUPING_AFTERNOON = 'afternoon'
KEY_GROUPING_MORNING = 'morning'

BAD_MOOD_CONSTANT = 3.5
GOOD_MOOD_CONSTANT = 2

FREEFORM_CLIENT_DESCRIPTION = ["Du bist ein empathischer Assistent, der wie ein guter Freund, mit dem User bespricht, woran dieser tagtäglich arbeitet und in welcher Verfassung er dabei bist. ",
                               "Bedenke beim Formulieren einer Antwort folgende Schritte: \n"
                               "1. Großes Ganzes betrachten: In welcher Situation befindet sich der User\n"
                               "2. Analyse: Welche Probleme sind in dieser Situation entstanden\n"
                               "3. Einordnung: Wie verbreitet ist diese Art von Problem\n"
                               "4. Recherche: Was haben seriöse wissenschaftliche Quellen (z.B. Gesundheitsportale, Ärzte, Hirnforschung, oder Psychologie) dazu herausgefunden\n"
                               "5. Lösung: Wie kann produktiv damit umgegangen werden\n",
                               "Besser als konkrete Empfehlungen sind in manchen Situationen Rückfragen, die zur Selbstreflexion anregen. "
                               "Drücke dich kurz und präzise aus. Wiederhole nicht was schon gesagt wurde, sondern bringe neue Perspektiven ein. "
                               "Verwende weniger als 100 completion_tokens."]


class GenericExpert:
    def __init__(self, cengine, key_base):
        self._cengine = cengine
        self._key_base = key_base

    def run(self):
        raise NotImplementedError("Must be implemented by subclass")

    def remedy_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        if value == WhatElseMessage.ANSWER_WHAT_ELSE:
            responses = self.run()
            responses.reverse()
            return responses
        elif value == WhatElseMessage.ANSWER_FREETEXT:
            return [FreeformMessage(text=["Okay, dann schieß los!", "Gut, erzähl mal."])]
        else:
            return [Message(text=["Okay, das wars erstmal.", "Dann wars das erstmal.", "Gut, dann wars das vorerst."])]


class StressExpert(GenericExpert):
    STRESS_INTRODUCTION = "*Zum Thema Stress:* \n" \
                          "Stress lässt sich natürlich nicht immer vermeiden. " \
                          "Versuche deine Tage in stressigen Phasen pragmatisch zu planen: " \
                          "Kümmere dich zuerst um die wirklich wichtigen Dinge und versuche es zu akzeptieren, falls du nicht alles schaffst. Das ist in Ordnung. "
    REMEDY_MEDITATION = f"[Achtsamkeitsübungen]({MEDITATION_LINK}) sind effektiv beim Stressabbau. Allerdings können sie problematisch werden, " \
                        "wenn du sie lediglich als zusätzliche Aufgabe in einem ohnehin vollen Tag betrachtest. Versuche daher Zeiten zu finden " \
                        "an denen du die Übung in feste Tagesabläufe integrieren kannst."
    REMEDY_RELAX = "Nach der Arbeit solltest du dir möglichst Zeit zur Entspannung nehmen. " \
                   "Wenn das nicht möglich ist, blockiere dir schonmal eine feste Zeit zum Entspannen in der Zukunft."

    def run(self):
        # TODO Später: Z.B. Fragen ob Achtsamkeitsübungen überhaupt für einen etwas sind
        # TODO Später: Bzw. Zum Denken anregen: Auf welche Entspannung würdest du dich freuen?
        return [Message(text=self.STRESS_INTRODUCTION),
                WhatElseMessage(text=self.REMEDY_RELAX, callback=self.get_more_info_callback)]

    def get_more_info_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        messages = remedy_callback(key, value, cengine, is_multi_answer_finished)
        if value == WhatElseMessage.ANSWER_WHAT_ELSE:
            messages.append(Message(text=self.REMEDY_MEDITATION))
        return messages


class MentalFatigueExpert(GenericExpert):
    MENTAL_FATIGUE_INTRODUCTION = "*Zum Thema mentale Ermüdung:* \n" \
                                  "Mentale Ermüdung entsteht durch anhaltende geistige Anstrengungen. " \
                                  "Häufig geht sie mit einem Gefühl von Unlust einher. " \
                                  "Dein Körper versucht dir damit zu vermitteln, Erholungspausen einzulegen. "
    REMEDY_PAUSES_1 = "Die oben genannte Pomodoro Methode kann helfen, diese nicht zu vergessen."
    REMEDY_PAUSES_2 = "Die Pomodoro Methode kann helfen, diese nicht zu vergessen. Bspw. mithilfe des @pomodoro\_timer\_bot."
    REMEDY_SLOW_DOWN = "Mach in den Pausen etwas, was dich mental entlastet: Ein paar Minuten nicht sitzen, an die frische Luft gehen, oder z.B. einen Power-Nap. "
    REMEDY_WHOLE_SYSTEM = "Ergänzend ist es ratsam, regelmäßige körperliche Aktivität in den Tagesablauf einzubauen, " \
                          "um die mentale Ermüdung zu reduzieren und die allgemeine geistige Gesundheit zu fördern. " \
                          "Zudem ist eine ausgewogene Ernährung und ausreichender Schlaf entscheidend, um die Belastbarkeit des Gehirns zu unterstützen."

    def run(self):
        responses = []
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(Message(text=self.MENTAL_FATIGUE_INTRODUCTION + self.REMEDY_PAUSES_1))
        else:
            responses.append(Message(text=self.MENTAL_FATIGUE_INTRODUCTION + self.REMEDY_PAUSES_2))
        responses.append(WhatElseMessage(self.REMEDY_SLOW_DOWN, callback=self.get_more_info_callback))
        return responses

    def get_more_info_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        messages = remedy_callback(key, value, cengine, is_multi_answer_finished)
        if value == WhatElseMessage.ANSWER_WHAT_ELSE:
            messages.append(Message(text=self.REMEDY_WHOLE_SYSTEM))
        return messages


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
            responses.append(WhatElseMessage(text=self.REMEDY_NAP))
        else:
            responses.append(Message(text=self.REMEDEY_POMODORO))
            responses.append(WhatElseMessage(text=self.REMEDY_NAP))
        return responses


class DemotivationExpert(GenericExpert):
    DEMOTIVATION_INTRODUCTION = "*Zum Thema wenig Motivation und Unlust:* \n" \
                                "Für manche Aufgaben keine intrinsische Motivation zu haben ist normal. " \
                                "Oft hilft es jedoch schon sich nur für einen Moment zu überwinden und den Anfang zu machen, bis die Unlust verfliegt. " \
                                "Außerdem fördert es die Willenskraft, Aufgaben trotz innerem Widerstand zu erledigen! " \
                                "Natürlich nur im Rahmen deiner Belastungsgrenzen: Lass es ruhig angehen, wenn es nicht so gut läuft wie erhofft."
    REMEDY_CELEBRATE = "Frag dich warum du das Geplante trotz Unlust erledigen möchtest. Vielleicht ist es nur der finanzielle Aspekt. " \
                       "Vielleicht hilfst du damit aber auch jemand Anderem. Vielleicht gönnst du dir auch etwas, nachdem du dich überwunden hast: " \
                       "Zeit für dein Lieblingshobby, oder ein gutes Essen zum Beispiel. "
    REMEDY_PAUSES_1 = "Es kann auch helfen viele kurze Pausen zu machen, wie bei der oben genannten Pomodoro Methode."
    REMEDY_PAUSES_2 = "Es kann auch helfen viele kurze Pausen zu machen, wie bei der Pomodoro Methode. Dafür kannst du dich z.B. an @pomodoro\_timer\_bot wenden."
    REMEDY_REFLECTION = "Hilfreich ist es außerdem die Gründe für die fehlende Motivation zu reflektieren. War dein Tag einfach anstrengend? " \
                        "Ist die konkrete Aufgabe unangenehm? Oder gibt es vielleicht allgemein etwas, dass dich unglücklich macht? " \
                        "Was kannst du tun, um in Zukunft wieder mit mehr Motivation durch den Tag zu gehen?"

    def run(self):
        is_generic_remedy_shown = self._cengine.get_state(GENERIC_REMEDY_STATE_KEY)
        responses = [Message(text=self.DEMOTIVATION_INTRODUCTION), Message(text=self.REMEDY_CELEBRATE)]
        if is_generic_remedy_shown and not isinstance(is_generic_remedy_shown, dict):
            responses.append(WhatElseMessage(self.REMEDY_PAUSES_1, callback=self.get_more_info_callback))
        else:
            responses.append(WhatElseMessage(self.REMEDY_PAUSES_2, callback=self.get_more_info_callback))
        return responses

    def get_more_info_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        messages = remedy_callback(key, value, cengine, is_multi_answer_finished)
        if value == WhatElseMessage.ANSWER_WHAT_ELSE:
            messages.append(Message(text=self.REMEDY_REFLECTION))
        return messages


class QuestionnaireEvaluationExpert(GenericExpert):
    THANKS = "Gut, danke"
    HAPPY_RESPONSE = f"Es freut mich, dass es dir relativ gut zu gehen scheint! Dann will ich gar nicht weiter stören."
    MEDIOCRE_RESPONSE = "Deine Angaben sind mit einem Durchschnitt von {}/5 im mittleren Bereich, wobei nichts besonders problematisch erscheint. " \
                        "Wenn du dich nicht in Topform fühlst, lass es einfach etwas ruhiger angehen. Viel Erfolg bei der restlichen Arbeit."
    SOME_BAD_RESPONSE = "Deine Bewertung ergibt einen Durchschnitt von {}/5, und es lässt sich erkennen, dass du bestimmte Aspekte des Tages als anspruchsvoll empfunden hast."
    BAD_RESPONSE = "Der Durchschnitt von {}/5 deutet darauf hin, dass es dir allgemein nicht so gut zu gehen scheint."
    REMEDY_LOW_EXPECTATIONS = f"Ich würde dir empfehlen nicht allzu hohe Erwartungen an dich zu haben, und nicht " \
                              f"länger als nötig zu arbeiten. Nimm dir regelmäßig kurze Auszeiten, z.B. mit Hilfe des @pomodoro\_timer\_bot."
    REMEDEY_POMODORO = f"Um die Auszeiten nicht zu vergessen, kannst du es auch mit der Pomodoro-Methode probieren. Bspw. mithilfe von @pomodoro\_timer\_bot"
    REMEDY_TALK = f"Wenn du deine Situation ausführlicher besprechen möchtest, schreib mir einfach. Ansonsten ist das erstmal alles. Du schaffst das schon😌"
    REMEDY_GENERIC = "Okay, hier noch ein paar Ideen, wofür du die Pausen nutzen könntest: "

    STATE_NAMES = {
        "stress_state": "Stress",
        "mental_fatigue_state": "Mentale Ermüdung",
        "energy_state": "Schläfrigkeit",
        "motivation_state": "Unlust",
    }
    STATE_EXPERTS = {
        "stress_state": StressExpert,
        "mental_fatigue_state": MentalFatigueExpert,
        "energy_state": SleepinessExpert,
        "motivation_state": DemotivationExpert,
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

    def specify_expert_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        if value in self.STATE_EXPERTS.keys():
            expert = self.STATE_EXPERTS[value](self._cengine, self._key_base)
            responses = expert.run()
            responses.reverse()
            return responses
        else:
            return [GenericRemedyMessage(), Message(text=self.REMEDY_GENERIC)]

    def run(self):
        mood_states, most_severe_states, avg_mood, med_mood = self._create_mood_state_statistics()
        responses = [Message(text=self.THANKS), Message(text=self.short_evaluation(mood_states))]

        if not most_severe_states and med_mood < BAD_MOOD_CONSTANT:
            if med_mood <= GOOD_MOOD_CONSTANT:
                responses.append(Message(text=self.HAPPY_RESPONSE))
            else:
                responses.append(Message(text=self.MEDIOCRE_RESPONSE.format(med_mood)))

        elif most_severe_states:
            if len(most_severe_states) >= 2:
                self._cengine.update_state(GENERIC_REMEDY_STATE_KEY, True)
                responses.append(Message(text=self.BAD_RESPONSE.format(avg_mood)))
                responses.append(Message(text=self.REMEDY_LOW_EXPECTATIONS))
                answers = [(self.STATE_NAMES[key], key) for key in most_severe_states]
                responses.append(ExpertSpecificationQuestion(callback=self.specify_expert_callback, answers=answers))
            else:
                expert = self.STATE_EXPERTS[next(iter(most_severe_states))](self._cengine, self._key_base)
                responses.extend(expert.run())

        # TODO: Veränderungen zu vormittag / gestern einarbeiten

        responses.reverse()
        return responses
