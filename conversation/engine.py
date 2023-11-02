from collections import deque


class MessageStateException(Exception):
    def __init__(self, message):
        self.message = message


class MessageContent:
    def __init__(self, text=None, predefined_answers=None):
        self.text = text
        self.predefined_answers = predefined_answers


class Message:
    def __init__(self, text, callback=None):
        self._callback = callback
        self._sent = False
        self.content = MessageContent(text=text)

    def mark_as_sent(self):
        if not self.has_been_sent():
            self._sent = True
        else:
            raise MessageStateException("Message has already been consumed")

    def has_been_sent(self):
        return self._sent

    def requires_user_input(self):
        return self._callback is not None and callable(self._callback)

    def handle_user_input(self, response):
        return self._callback(response)


class AnswerableMessage(Message):
    def __init__(self, text, callback):
        super(AnswerableMessage, self).__init__(text, callback)


class SingleAnswerMessage(AnswerableMessage):
    def __init__(self, text, callback, answers):
        super(SingleAnswerMessage, self).__init__(text, callback)
        self.content = MessageContent(text=text, predefined_answers=answers)

    def mark_as_sent(self):
        super(SingleAnswerMessage, self).mark_as_sent()
        return self.content


class MultiAnswerMessage(SingleAnswerMessage):
    def __init__(self, text, callback, answers):
        super(MultiAnswerMessage, self).__init__(text, callback, answers)
        self.content.predefined_answers.append(["Fertig"])


class ConversationState:
    def __init__(self, state_dict=None):
        self.entries = state_dict if state_dict else dict()


class ConversationEngine:
    def __init__(self, queue=None):
        self.state = ConversationState()
        self.queue = deque(queue) if queue is not None else deque()
        self.current_message = None

    def begin_conversation(self, conversation, state=ConversationState()):
        self.state = state
        self.queue.clear()
        self.queue.extend(conversation)

    def next_message(self):
        self.current_message = self.queue.popleft()
        return self.current_message

    def is_waiting_for_user_input(self):
        return self.current_message.has_been_sent() and self.current_message.requires_user_input()

    def handle_user_input(self, text):
        answers = self.current_message.handle_user_input(text)
        if answers:
            self.queue.extendleft(answers)
