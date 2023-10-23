from conversation.engine import Message


def create_morning_conversation():
    return [
        MorningMessage(),
        WeatherQuestion(),  # TODO Hiervon wird NICHT das OkPrompt geschrieben, nur das äußere UserInput
        # QuestionaireConversation(global_state=self.global_state),
        # MorningKickoffPrompt(global_state=self.global_state)
        GoodbyeMessage()
    ]


class MorningMessage(Message):
    PROMPTS = [
        "Good morning!",
        "Hello there!",
        "Top of the morning to you!",
        # Add more greetings here
    ]

    def __init__(self):
        super(MorningMessage, self).__init__(self.PROMPTS[0])


class GoodbyeMessage(Message):
    def __init__(self):
        super(GoodbyeMessage, self).__init__("Goodbye!")


def weather_expert_callback(response):
    if "good" in response.lower():
        return [Message("I'm glad you're enjoying the weather!")]
    else:
        return [Message("Sorry to hear that.")]


class WeatherExpert:

    def handle_response(self, response):
        if "good" in response.lower():
            return Message("I'm glad you're enjoying the weather!")
        else:
            return Message("Sorry to hear that.")


class WeatherQuestion(Message):
    PROMPTS = [
        "How is the weather today?",
    ]

    def __init__(self):
        super(WeatherQuestion, self).__init__(self.PROMPTS[0], callback=weather_expert_callback)
