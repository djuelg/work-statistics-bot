from conversation.engine import Message, SingleAnswerMessage, MultiAnswerMessage, update_state_multi_answer_callback, update_state_single_answer_callback


class QuestionnaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns durch ein paar Aussagen deinen aktuellen Blick auf die Welt einordnen. Bewerte diese bitte auf "
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class StressQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich gestresst. "
        "Dieser kann sich z.B. ausdrücken durch Empfindungen wie Unruhe oder leichte Reizbarkeit",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key):
        self.KEY = key
        super().__init__(self.PROMPTS, update_state_single_answer_callback, self.STATES)


class SleepinessQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich körperlich ermüdet. "
        "Dies kann z.B. durch schlechten Schlaf entstehen und zu Kraftlosigkeit oder Unkonzentriertheit führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key):
        self.KEY = key
        super().__init__(self.PROMPTS, update_state_single_answer_callback, self.STATES)


class MentalFatigueQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich geistig ermüdet. "
        "Dies kann z.B. durch anhaltende geistige Arbeiten entstehen und zu Konzentrationsproblemen,"
        "  Motivationslosigkeit und Unlust führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self, key):
        self.KEY = key
        super().__init__(self.PROMPTS, update_state_single_answer_callback, self.STATES)


class MoodQuestion(MultiAnswerMessage):
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

    def __init__(self, key):
        self.KEY = key
        super().__init__(self.PROMPTS, update_state_multi_answer_callback, self.STATES)


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