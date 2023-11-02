from conversation.engine import Message, SingleAnswerMessage, MultiAnswerMessage


def create_morning_conversation():
    return [
        MorningMessage(),
        QuestionaireIntroductionMessage(),
        StressStateQuestion(),
        SleepinessQuestion(),
        MentalFatigueQuestion(),
        MoodQuestion(),
        QuestionaireEvaluationMessage(),
        GoodbyeMessage()
    ]


class MorningMessage(Message):
    PROMPTS = [
        "Guten Morgen!",
        "Hey!",
        "Hallo, ich wünsche einen guten Morgen.",
        # Add more greetings here
    ]

    def __init__(self):
        super().__init__(self.PROMPTS[0])


class QuestionaireIntroductionMessage(Message):
    PROMPTS = [
        "Lass uns durch ein paar Aussagen deinen aktuellen Blick auf die Welt einordnen. Bewerte diese bitte auf "
        "einer Skala von '1 - trifft gar nicht zu' bis '5 - trifft vollkommen zu'.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS[0])


class StressStateQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich gestresst. "
        "Dieser kann sich z.B. ausdrücken durch Empfindungen wie Unruhe oder leichte Reizbarkeit",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self):
        super().__init__(self.PROMPTS[0], update_state_callback, self.STATES)



class SleepinessQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich körperlich ermüdet. "
        "Dies kann z.B. durch schlechten Schlaf entstehen und zu Kraftlosigkeit oder Unkonzentriertheit führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self):
        super().__init__(self.PROMPTS[0], update_state_callback, self.STATES)


class MentalFatigueQuestion(SingleAnswerMessage):
    PROMPTS = [
        "Ich fühle mich geistig ermüdet. "
        "Dies kann z.B. durch anhaltende geistige Arbeiten entstehen und zu Konzentrationsproblemen,  Motivationslosigkeit und Unlust führen.",
    ]
    STATES = ["1", "2", "3", "4", "5"]

    def __init__(self):
        super().__init__(self.PROMPTS[0], update_state_callback, self.STATES)


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
    ]

    def __init__(self):
        super().__init__(self.PROMPTS[0], update_state_callback, self.STATES)


def update_state_callback(response):
    pass # TODO return/save state information

class QuestionaireEvaluationMessage(Message):
    PROMPTS = [
        "Alles klar, danke für deine Zeit! Ich kümmere mich nun um die Auswertung deiner Aussagen.",
    ] # TODO: Nutzen des State um etwas passendes zu antworten

    def __init__(self):
        super().__init__(self.PROMPTS[0])


class GoodbyeMessage(Message):
    PROMPTS = [
        "Mach's gut!",
        "Bis später!",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS[0])


def weather_expert_callback(response):
    if "sunny" in response.lower():
        return [Message("I'm glad you're enjoying the weather!")]
    else:
        return [Message("Sorry to hear that.")]


class WeatherExpert:

    def handle_response(self, response):
        if "sunny" in response.lower():
            return Message("I'm glad you're enjoying the weather!")
        else:
            return Message("Sorry to hear that.")


class WeatherQuestion(SingleAnswerMessage):
    PROMPTS = [
        "How is the weather today?",
    ]
    WEATHER_CONDITIONS = ["sunny", "cloudy", "rainy"]

    def __init__(self):
        super(WeatherQuestion, self).__init__(self.PROMPTS[0], weather_expert_callback, self.WEATHER_CONDITIONS)
