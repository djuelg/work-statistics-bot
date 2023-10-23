import random
from collections import deque
from pprint import pprint


class ConversationItem:
    def next(self):
        pass

class Conversation(ConversationItem):
    def __init__(self, queue=None, global_state=None):
        self.global_state = global_state if global_state else dict()
        self.queue = deque(queue) if queue is not None else deque()

    def has_next(self):
        return len(self.queue) > 0

    def next(self):
        item = self.queue.popleft()

        if isinstance(item, Prompt):
            item.display()
        elif isinstance(item, UserInput):
            response = item.next()
            response.display()
        elif isinstance(item, Conversation):
            while item.has_next():
                item.next()


class Prompt(ConversationItem):
    def __init__(self, prompts,global_state=None):
        self.prompts = prompts
        self.global_state = global_state if global_state else dict()

    def next(self):
        return random.choice(self.prompts)

    def display(self):
        print(self.next())

class MorningPrompt(Prompt):
    PROMPTS = [
        "Good morning!",
        "Hello there!",
        "Top of the morning to you!",
        # Add more greetings here
    ]

    def __init__(self):
        super(MorningPrompt, self).__init__(self.PROMPTS)

class GoodWeatherPrompt(Prompt):
    def __init__(self):
        super().__init__(["I'm glad you're enjoying the weather!"])

class BadWeatherPrompt(Prompt):
    def __init__(self):
        super().__init__(["Sorry to hear that.", "OME chillout"])

class GoodbyePrompt(Prompt):
    def __init__(self):
        super().__init__(["Goodbye! Have a great day!"])

class UserInput(ConversationItem):
    def __init__(self, global_state=None, prompt='', callback=None):
        self.global_state = global_state if global_state else dict()
        self.prompt = prompt
        self.callback = callback

    def next(self):
        response = input(self.prompt)
        if self.callback:
            result = self.callback.handle_user_input(response)
            return result

    def display(self):
        self.next()

class WeatherUserInput(UserInput):
    def __init__(self):
        super().__init__(prompt='How is the weather today? ', callback=WeatherExpert())

class WeatherExpert:
    def handle_response(self, response):
        if "good" in response.lower():
            return GoodWeatherPrompt()
        else:
            return BadWeatherPrompt()


class HomeOfficeUserInput(UserInput):
    def __init__(self, global_state):
        self.global_state = global_state
        super().__init__(prompt='Do you work from home? ', callback=HomeOfficeExpert(global_state=self.global_state))


class OkPrompt(Prompt):
    def __init__(self):
        super().__init__(["Okay", "Noted"])


class HomeOfficeExpert:
    def __init__(self, global_state) -> None:
        self.global_state = global_state
        super().__init__()

    def handle_response(self, response):
        if "yes" in response.lower():
            self.global_state['work_location'] = 'home'
        else:
            self.global_state['work_location'] = 'outside'
        return OkPrompt()


class SilencePrompt(Prompt):
    def __init__(self):
        super().__init__([''])


class TodaysWorkExpert:
    def __init__(self, global_state) -> None:
        self.global_state = global_state
        super().__init__()

    def handle_response(self, response):
        if any(['nothing' in response, 'chill' in response, 'off-day' in response]):
            self.global_state['todays_work'] = 'NOTHING'
            return OkPrompt()
        elif 'work' in response:
            self.global_state['todays_work'] = 'WORK'
            return HomeOfficeUserInput(global_state=self.global_state)
        elif 'study' in response:
            self.global_state['todays_work'] = 'STUDY'
            return HomeOfficeUserInput(global_state=self.global_state)


class TodaysWorkUserInput(UserInput):
    def __init__(self, global_state):
        self.global_state = global_state
        super().__init__(prompt='What do you plan on doing this workday? ', callback=TodaysWorkExpert(global_state=self.global_state))



class MorningConversation(Conversation):

    def __init__(self):
        global_state=dict()
        queue = [
            MorningPrompt(),
            TodaysWorkUserInput(global_state=global_state), #  TODO Hiervon wird NICHT das OkPrompt geschrieben, nur das äußere UserInput
            # QuestionaireConversation(global_state=self.global_state),
            # MorningKickoffPrompt(global_state=self.global_state)
            GoodbyePrompt()
        ]
        super().__init__(queue=queue, global_state=global_state)


if __name__ == "__main__":

    conversation1 = MorningConversation()

    conversation = Conversation(queue=[
        MorningPrompt(),
        WeatherUserInput(),
        GoodbyePrompt()])

    while conversation1.has_next():
        conversation1.next()
    pprint(conversation1.global_state)


