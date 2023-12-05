import copy
import random
from collections import deque
from datetime import datetime


CURRENT_CONVERSATION_KEY = "current_conversation"
DAILY_QUESTIONNAIRE_KEY = 'daily_questionnaire'
HISTORY_KEY = 'history'
MULTI_ANSWER_FINISHED = 'Fertig'


class MessageStateException(Exception):
    def __init__(self, message):
        self.message = message


class MessageContent:
    def __init__(self, text=None, predefined_answers=None):
        self.text = text if not isinstance(text, list) else random.choice(text)
        self.predefined_answers = predefined_answers


class Message:
    def __init__(self, text):
        self._sent = False
        self._content = MessageContent(text=text)

    def content(self, cengine=None):
        return self._content

    def mark_as_sent(self):
        if not self.has_been_sent():
            self._sent = True
        else:
            raise MessageStateException("Message has already been consumed")

    def has_been_sent(self):
        return self._sent


class AnswerableMessage(Message):

    def __init__(self, text, callback_key, callback, predefined_answers=None):
        self.callback_key = callback_key
        self._callback = callback
        super(AnswerableMessage, self).__init__(text)
        self._content = MessageContent(text=text, predefined_answers=predefined_answers)

    def handle_user_input(self, response, cengine=None, is_multi_answer_finished=False):
        if not self.callback_key:
            raise MessageStateException("callback_key not set")
        return self._callback(self.callback_key, response,
                              cengine=cengine, is_multi_answer_finished=is_multi_answer_finished)


class SingleAnswerMessage(AnswerableMessage):
    def __init__(self, text, callback_key, callback, answers):
        super(SingleAnswerMessage, self).__init__(text, callback_key, callback, predefined_answers=answers)


class MultiAnswerMessage(AnswerableMessage):
    def __init__(self, text, callback_key, callback, answers):
        super(MultiAnswerMessage, self).__init__(text, callback_key, callback, predefined_answers=answers)


def update_state_single_answer_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if not is_multi_answer_finished:
        value = float(value) if value.isnumeric() else value
        cengine.update_state(key, value)


def update_state_multi_answer_callback(key, value, cengine=None, is_multi_answer_finished=False):
    if not is_multi_answer_finished:
        value = float(value) if value.isnumeric() else value
        cengine.append_state(key, value)


class ConversationEngine:
    def __init__(self, queue=None):
        self.state = dict()
        self.queue = deque(queue) if queue is not None else deque()
        self.current_message = None

    def begin_new_conversation(self, conversation):
        self.queue.clear()
        self.drop_state(CURRENT_CONVERSATION_KEY)
        self.queue.extend(conversation)

    def next_message(self):
        self.current_message = self.queue.popleft()
        return self.current_message

    def is_waiting_for_user_input(self):
        return self.current_message.has_been_sent() and isinstance(self.current_message, AnswerableMessage)

    def handle_user_input(self, text):
        is_multi_answer_finished = isinstance(self.current_message, MultiAnswerMessage) and text == MULTI_ANSWER_FINISHED
        answers = self.current_message.handle_user_input(text,
                                                         cengine=self, is_multi_answer_finished=is_multi_answer_finished)
        if answers:
            self.queue.extendleft(answers)

    def copy_today_to_history(self):
        datetime.today().date()
        date_key = str(datetime.today().date())
        today_data = copy.deepcopy(self.get_state(DAILY_QUESTIONNAIRE_KEY))
        self.update_state(HISTORY_KEY, {date_key: today_data})

    def get_state(self, key):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys:
            state = state.get(key, {})
        return state

    def update_state(self, key, value):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys[:-1]:
            state = state.setdefault(key, {})
        state[nested_keys[-1]] = value

    def append_state(self, key, value):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys[:-1]:
            state = state.setdefault(key, {})

        if nested_keys[-1] not in state:
            state[nested_keys[-1]] = []
        state[nested_keys[-1]].append(value)

    def drop_state(self, key):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys[:-1]:
            state = state.setdefault(key, {})
        if nested_keys[-1] in state:
            del state[nested_keys[-1]]