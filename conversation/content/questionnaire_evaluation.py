import random

from conversation.content.generic_messages import WhatElseMessage, MEDITATION_LINK, remedy_callback, \
    GenericRemedyMessage, FREEFORM_CLIENT_DESCRIPTIONS_REMEDY
from conversation.engine import update_state_single_answer_callback, CONVERSATION_REMEDY_KEY
from conversation.message_types import Message, FreeformMessage, SingleAnswerMessage, GeneratedMessage
from freeform_chat.freeform_client_base import ROLE_USER
from freeform_chat.gpt_freeform_client import GPT4_MODEL

STATE_NAMES = {
    "stress_state": "Stress",
    "mental_fatigue_state": "Mentale Ermüdung",
    "energy_state": "Schläfrigkeit",
    "motivation_state": "Unlust",
}

SEVERENESS_MAPPINGS = {
    1: "gar keine",
    2: "fast keine",
    3: "ein wenig",
    4: "einige",
    5: "sehr starke"
}

GENERIC_REMEDY_STATE_KEY = "current_conversation.is_generic_remedy_shown"
KEY_GROUPING_AFTERNOON = 'afternoon'
KEY_GROUPING_MORNING = 'morning'

BAD_MOOD_CONSTANT = 3.5
GOOD_MOOD_CONSTANT = 2


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
    REMEDY_PAUSES_2 = "Die Pomodoro Methode kann helfen, diese nicht zu vergessen. Bspw. mithilfe meine guten Kollegen @pomodoro\_cat\_bot."
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
    REMEDEY_POMODORO = "Um sie nicht zu vergessen empfehle ich dir die Pomodoro Methode und dafür meinen guten Kollegen @pomodoro\_cat\_bot zu nutzen."

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
    REMEDY_PAUSES_2 = "Es kann auch helfen viele kurze Pausen zu machen, wie bei der Pomodoro Methode. Dafür kannst du dich an meinen guten Kollegen @pomodoro\_cat\_bot wenden."
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


class StartProblemEvaluationQuestion(SingleAnswerMessage):
    PROBLEM_EVALUATION_KEY = 'daily_questionnaire.remedy.start_problem_evaluation'
    PROMPTS = ["Meist lohnt es sich kurz darüber nachzudenken, wie man mit der jetzigen Situation produktiv umgehen kann. "
               "Möchtest du eine geführte Reflektion über {} machen?"]
    ANSWER_YES = f'ANSWER_YES'
    ANSWER_NO_TIME = f'ANSWER_NO_TIME'
    ANSWER_NO_MOTIVATION = f'ANSWER_NO_MOTIVATION'
    STATES = [
        [("Ja, lass uns kurz darüber reden", ANSWER_YES)],
        [("Nein, es geht zeitlich gerade schlecht", ANSWER_NO_TIME)],
        [("Nein, keine Lust", ANSWER_NO_MOTIVATION)]
    ]

    def __init__(self, problem_keys, all_mood_states, callback=None, key_base=None):
        self.problem_keys = problem_keys
        self.all_mood_states = all_mood_states
        self.key_base = key_base

        callback = callback if callback else self._problem_evaluation_callback
        super().__init__(self.PROMPTS, self.PROBLEM_EVALUATION_KEY, callback, self.STATES)

    def content(self, cengine=None):
        problem_names = [STATE_NAMES[key] for key in self.problem_keys]
        if len(problem_names) == 1:
            self._content.text = self.PROMPTS[0].format(problem_names[0])
        else:
            self._content.text = self.PROMPTS[0].format(
                ", ".join(problem_names[:-1]) + " und " + problem_names[-1])

        return self._content

    def _problem_evaluation_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        update_state_single_answer_callback(key, value, cengine, is_multi_answer_finished)
        ONE_SENTENCE_REMEDIES = {
            "Stress": "Kümmere dich wenn du gestresst bist nur um die wirklich wichtigen Dinge und versuche es zu akzeptieren, falls du nicht alles schaffst.",
            "Mentale Ermüdung": "Mentale Ermüdung baut sich durch anhaltende geistige Anstrengungen über den Tag auf und wird nur durch Entspannung abgebaut.",
            "Schläfrigkeit": "Sich im Laufe des Tages müde oder energielos zu fühlen kann vorkommen, geht aber meist mit der Zeit vorüber.",
            "Unlust": "Für manche Aufgaben keine intrinsische Motivation zu haben ist normal. Versuche das zu akzeptieren und belohne dich für das Erledigte anderweitig."
        }
        if value == StartProblemEvaluationQuestion.ANSWER_YES:
            responses = [
                ProblemExplanationQuestion(),
                ProblemOriginQuestion(self.all_mood_states, self.key_base),
                ProblemLongevityQuestion(),
                ShortTermReliefQuestion(self.problem_keys, self.all_mood_states, self.key_base),
                WhatElseMessage(text="Hast du noch Fragen?")
            ]
            responses.reverse()
            return responses
        else:
            responses = [Message(text="Okay kein Problem, versuch aber dich nicht zu überfordern und nicht zu lange zu machen. Bedenke folgendes:")]
            for idx, key in enumerate(self.problem_keys):
                responses.append(Message(text=f"{idx + 1}. {ONE_SENTENCE_REMEDIES[STATE_NAMES[key]]}"))
            responses.append(Message(text=f"{len(self.problem_keys)+1}. Wenn du nicht so leistungsfähig bist ist das in Ordnung. Dein Körper versucht dir zu vermitteln, Erholungspausen einzulegen und wenn möglich eher leichte Aufgaben durchzuführen. Tu ihm den Gefallen :)"))
            responses.reverse()
            return responses


class ProblemExplanationQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.problem_explanation'
    PROMPTS = ["Okay, dann beschreibe zunächst was du gerade für ein Problem hast:"]

    def __init__(self, callback=update_state_single_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, [])


class ProblemOriginQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.problem_origin'
    PROMPTS = ["Verstehe. Hast du eine Idee warum du dieses Problem haben könntest? Welche Ursachen spielen eine Rolle?"]

    def __init__(self, all_mood_states, key_base, callback=None):
        self.all_mood_states = all_mood_states
        self.key_base = key_base

        callback = callback if callback else self._generated_remedy_response_callback
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, [])

    def _generated_remedy_response_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        update_state_single_answer_callback(key, value, cengine=cengine, is_multi_answer_finished=is_multi_answer_finished)

        questionnaire_result = "So sieht mein mentaler Zustand aus: \n"
        for key in self.all_mood_states.keys():
            questionnaire_result += f"{STATE_NAMES[key]} bereitet mir gerade {SEVERENESS_MAPPINGS[self.all_mood_states[key]]} Probleme. "
        feelings = cengine.get_state(f"{self.key_base}.mood_state")
        questionnaire_result += f"Folgende Stimmungen sind dominant: {', '.join(feelings)}."
        cengine.save_conversation_messages(ROLE_USER, questionnaire_result, conversation_key=CONVERSATION_REMEDY_KEY)

        problem_description = "Ich habe folgendes Problem: "
        problem_description += cengine.get_state(ProblemExplanationQuestion.CALLBACK_KEY).strip() + " "
        problem_description += cengine.get_state(ProblemOriginQuestion.CALLBACK_KEY).strip()
        cengine.save_conversation_messages(ROLE_USER, problem_description, conversation_key=CONVERSATION_REMEDY_KEY)

        instruction = "Bitte gib mir eine kurze prägnante Einordnung meiner Situation. Versuche Schritt für Schritt auf meinen mentalen Zustand und meine Stimmungen" \
                      "einzugehen und diese mit den Problemen zu verknüpfen. " \
                      "Erkläre zunächst inwiefern mich die negativen Teile meines mentalen Zustandes und die negativen Stimmungen psychologisch beeinflussen können. " \
                      "Gehe darauf ein, wie diese mit meinem beschriebenen Problem in Zusammenhang stehen können. " \
                      "Überlege dann, ob ich aus den positiven Teilen meines mentalen Zustandes und den positiven Stimmungen etwas hilfreiches ziehen kann. " \
                      "Beschränke deine Antwort auf ein bis maximal zwei Absätze. "
        cengine.save_conversation_messages(ROLE_USER, instruction, conversation_key=CONVERSATION_REMEDY_KEY)

        responses = [GeneratedMessage(FREEFORM_CLIENT_DESCRIPTIONS_REMEDY, CONVERSATION_REMEDY_KEY, model=GPT4_MODEL)]
        if value == "Ich möchte nichts davon tun":
            responses.append(Message(text="Okay, das ist in Ordnung. Lass uns deine Angaben zusammenfassen:"))
        else:
            responses.append(Message(text="Okay, lass uns zusammenfassen:"))
        return responses


class ProblemLongevityQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.problem_longevity'
    PROMPTS = [
        "Wie präsent ist das Problem in deinem Leben? Hattest du es schon öfter in der Vergangenheit? Ist es längerfristiger Natur?"]
    STATES = [["Es ist ein Einzelfall"], ["Es ist vereinzelt schon aufgetreten"], ["Es ist ein längerfristiges Problem"]]

    def __init__(self, callback=None):
        callback = callback if callback else self._problem_evaluation_callback
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, self.STATES)

    def _problem_evaluation_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        update_state_single_answer_callback(key, value, cengine, is_multi_answer_finished)
        if value != "Es ist ein Einzelfall":
            return [ProblemOccurrenceQuestion()]


class ProblemOccurrenceQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.problem_occurrence'
    PROMPTS = ["Welche Zeiten oder Situationen fallen dir ein, in denen das Problem schon mal aufgetreten ist?"]

    def __init__(self, callback=None):
        callback = callback if callback else self._generated_remedy_response_callback
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, [])

    def _generated_remedy_response_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        update_state_single_answer_callback(key, value, cengine=cengine, is_multi_answer_finished=is_multi_answer_finished)

        occurence = "Das Problem ist leider kein Einzelfall. Es ist in folgenden Situationen schon mal aufgetreten: "
        occurence += value
        cengine.save_conversation_messages(ROLE_USER, occurence, conversation_key=CONVERSATION_REMEDY_KEY)

        instruction = ("Bitte gib mir eine kurze prägnante Einordnung, wie mit dem Problem längerfristig umgegangen werden kann. "
                      "Beschränke deine Antwort auf ein bis maximal zwei Absätze. ")
        cengine.save_conversation_messages(ROLE_USER, instruction, conversation_key=CONVERSATION_REMEDY_KEY)
        return [GeneratedMessage(FREEFORM_CLIENT_DESCRIPTIONS_REMEDY, CONVERSATION_REMEDY_KEY, model=GPT4_MODEL)]


class ShortTermReliefQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'daily_questionnaire.remedy.selected_relief'
    PROMPTS = ["Gibt es unter den folgenden Dingen etwas, dass du _jetzt_ umsetzen kannst um kurzfristige Abhilfe zu schaffen?"]
    REMEDY_KEY_MAPPING = {
        "stress_state": "remedies.stress_remedies",
        "mental_fatigue_state": "remedies.mental_fatigue_remedies",
        "energy_state": "remedies.energy_remedies",
        "motivation_state": "remedies.motivation_remedies"
    }

    def __init__(self, problem_keys, all_mood_states, key_base, callback=None):
        self.problem_keys = problem_keys
        self.all_mood_states = all_mood_states
        self.key_base = key_base

        callback = callback if callback else self._generated_remedy_response_callback
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, [])

    def _generated_remedy_response_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        update_state_single_answer_callback(key, value, cengine=cengine,
                                            is_multi_answer_finished=is_multi_answer_finished)

        occurence = "Ich habe überlegt, dass mir folgendes kurzfristige Abhilfe schaffen könnte: "
        occurence += value
        cengine.save_conversation_messages(ROLE_USER, occurence,
                                           conversation_key=CONVERSATION_REMEDY_KEY)

        instruction = ("Ordne kurz ein, ob dies psychologisch gesehen ein guter erster Schritt ist und warum oder warum nicht. "
                       "Beschränke deine Antwort auf einen einzelnen Absatz. ")
        cengine.save_conversation_messages(ROLE_USER, instruction,
                                           conversation_key=CONVERSATION_REMEDY_KEY)
        return [GeneratedMessage(FREEFORM_CLIENT_DESCRIPTIONS_REMEDY, CONVERSATION_REMEDY_KEY, model=GPT4_MODEL)]

    def content(self, cengine=None):
        problem_relief_options = []
        for key in self.problem_keys:
            current_options = cengine.get_state(self.REMEDY_KEY_MAPPING[key])
            problem_relief_options.extend(
                [option for option in current_options if option not in problem_relief_options])

        if not problem_relief_options:
            self._content.predefined_answers = [
                ["Meditation", "Spazieren gehen", "Sport treiben"],
                ["Musik hören", "Zeit in der Natur", "Yoga"],
                ["Tiefes Atmen", "Kurzer Schlaf", "Etwas essen"],
                ["Lesen", "Kunst", "Mit jemandem sprechen"],
                ["Pomodoros", "Stehend arbeiten", "Kalt duschen"],
                ["Ich möchte nichts davon tun"]
            ]
            text_choice = self.PROMPTS if not isinstance(self.PROMPTS, list) else random.choice(self.PROMPTS)
            self._content.text = f"{text_choice} (Mit dem Befehl /override\_setup kannst du diese Liste anpassen)"
        else:
            problem_relief_options = [problem_relief_options[i:i + 3] for i in range(0, len(problem_relief_options), 3)]
            self._content.predefined_answers = [*problem_relief_options, ["Ich möchte nichts davon tun"]]
        return self._content


class QuestionnaireEvaluationExpert(GenericExpert):
    THANKS = "Gut, danke"
    HAPPY_RESPONSE = f"Es freut mich, dass es dir relativ gut zu gehen scheint! Dann will ich gar nicht weiter stören."
    MEDIOCRE_RESPONSE = "Deine Angaben sind mit einem Durchschnitt von {}/5 im mittleren Bereich, wobei nichts besonders problematisch erscheint. " \
                        "Wenn du dich nicht in Topform fühlst, lass es einfach etwas ruhiger angehen. Viel Erfolg bei der restlichen Arbeit."
    SOME_BAD_RESPONSE = "Deine Bewertung ergibt einen Durchschnitt von {}/5, und es lässt sich erkennen, dass du bestimmte Aspekte des Tages als anspruchsvoll empfunden hast."
    BAD_RESPONSE = "Der Durchschnitt von {}/5 deutet darauf hin, dass es dir allgemein nicht so gut zu gehen scheint."
    REMEDY_LOW_EXPECTATIONS = f"Ich würde dir empfehlen nicht allzu hohe Erwartungen an dich zu haben, und nicht " \
                              f"länger als nötig zu arbeiten. Nimm dir regelmäßig kurze Auszeiten, z.B. mit Hilfe meines guten Kollegen @pomodoro\_cat\_bot."
    REMEDEY_POMODORO = f"Um die Auszeiten nicht zu vergessen, kannst du es auch mit der Pomodoro-Methode probieren. Bspw. mithilfe meines guten Kollegen @pomodoro\_cat\_bot"
    REMEDY_TALK = f"Wenn du deine Situation ausführlicher besprechen möchtest, schreib mir einfach. Ansonsten ist das erstmal alles. Du schaffst das schon😌"
    REMEDY_GENERIC = "Okay, hier noch ein paar Ideen, wofür du die Pausen nutzen könntest: "

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
            answer += f"{STATE_NAMES[key]}: *{int(value)}*/5 \n"
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
            else:
                responses.append(Message(text=self.SOME_BAD_RESPONSE.format(avg_mood)))
            responses.append(StartProblemEvaluationQuestion(most_severe_states.keys(), mood_states, key_base=self._key_base))

        # TODO: Veränderungen zu vormittag / gestern einarbeiten

        responses.reverse()
        return responses
