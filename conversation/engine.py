import copy
import random
from collections import deque
from datetime import datetime


KEY_GROUPING_RECENTLY = 'recently_used'
CURRENT_CONVERSATION_KEY = "current_conversation"
CONVERSATION_MESSAGES_KEY = f"{CURRENT_CONVERSATION_KEY}.messages"
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

    def __repr__(self):
        return self._content.text


class StickerMessage(Message):
    def __init__(self, sticker_id):
        self.sticker_id = sticker_id
        super(StickerMessage, self).__init__("")


class ImageMessage(Message):
    def __init__(self, image):
        self.image = image
        super(ImageMessage, self).__init__("")


class ImageGroupMessage(Message):
    def __init__(self, media_group):
        self.media_group = media_group
        super(ImageGroupMessage, self).__init__("")


class FreeformMessage(Message):
    def __init__(self, text):
        super(FreeformMessage, self).__init__(text)


class AnswerableMessage(Message):

    def __init__(self, text, callback_key, callback, predefined_answers=None):
        super(AnswerableMessage, self).__init__(text)
        self.callback_key = callback_key
        self._callback = callback
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


def update_state_multi_answer_callback(key, value, cengine=None, remove_duplicates=True, is_multi_answer_finished=False):
    if not is_multi_answer_finished:
        value = float(value) if value.isnumeric() else value
        cengine.append_state(key, value, remove_duplicates=remove_duplicates)
        cengine.update_recently_used_values(key, value)


def extend_predefined_with_recent_items(question_key, cengine, predefined_answers):
    recent_key = f'{KEY_GROUPING_RECENTLY}.{question_key.split(".")[-1]}'
    recent_items = cengine.get_state(recent_key) or []
    flattened_answers = [item for sublist in predefined_answers for item in sublist]
    recent_items = [item for item in recent_items if item not in flattened_answers]
    recent_three = recent_items[:min(3, len(recent_items))]
    if recent_three:
        predefined_answers.insert(0, recent_three)
    return predefined_answers


class FreeformClientBase:
    ROLE_ASSISTANT = 'assistant'
    ROLE_USER = 'user'

    def generate_responses(self, messages):
        pass


class ConversationEngine:
    def __init__(self, queue=None, state=None, current_message=None, freeform_client=None):
        self.queue = deque(queue) if queue is not None else deque()
        self.state = state or dict()
        self.current_message = current_message
        self.freeform_client = freeform_client

    def begin_new_conversation(self, conversation):
        self.queue.clear()
        self.drop_state(CURRENT_CONVERSATION_KEY)
        self.queue.extend(conversation)

    def next_message(self):
        self.current_message = self.queue.popleft()
        if str(self.current_message):
            self._save_conversation_messages(FreeformClientBase.ROLE_ASSISTANT, str(self.current_message))
        return self.current_message

    def is_waiting_for_user_input(self):
        return (self.current_message.has_been_sent() and isinstance(self.current_message, AnswerableMessage)) \
            or (self.current_message.has_been_sent() and isinstance(self.current_message, FreeformMessage))

    def handle_user_input(self, text):
        self._save_conversation_messages(FreeformClientBase.ROLE_USER, text)
        if isinstance(self.current_message, FreeformMessage):
            last_messages = self.get_state(CONVERSATION_MESSAGES_KEY)
            answers = self.freeform_client.generate_responses(last_messages)
            answers = [FreeformMessage(text=ans) for ans in answers]
        else:
            is_multi_answer_finished = isinstance(self.current_message, MultiAnswerMessage) and text == MULTI_ANSWER_FINISHED
            answers = self.current_message.handle_user_input(text, cengine=self, is_multi_answer_finished=is_multi_answer_finished)

        if answers:
            self.queue.extendleft(answers)

    def copy_today_to_history(self):
        daily_questionnaire = self.get_state(DAILY_QUESTIONNAIRE_KEY)
        if daily_questionnaire:
            date_key = f'{HISTORY_KEY}.{datetime.today().date()}'
            today_data = copy.deepcopy(daily_questionnaire)
            self.update_state(date_key, today_data)
        self.drop_state(DAILY_QUESTIONNAIRE_KEY)

    def update_recently_used_values(self, key, value, recent_size=10):
        recent_key = f'{KEY_GROUPING_RECENTLY}.{key.split(".")[-1]}'
        recent_items = self.get_state(recent_key) or []
        recent_items.insert(0, value)
        recent_items = list(set(recent_items))[:min(recent_size, len(recent_items))]
        self.update_state(recent_key, recent_items)

    def _save_conversation_messages(self, role, current_message):
        self.append_state(CONVERSATION_MESSAGES_KEY, (role, current_message))

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

    def append_state(self, key, value, remove_duplicates=True):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys[:-1]:
            state = state.setdefault(key, {})

        if nested_keys[-1] not in state:
            state[nested_keys[-1]] = []
        if not remove_duplicates or value not in state[nested_keys[-1]]:
            state[nested_keys[-1]].append(value)

    def drop_state(self, key):
        nested_keys = key.split('.')
        state = self.state
        for key in nested_keys[:-1]:
            state = state.setdefault(key, {})
        if nested_keys[-1] in state:
            del state[nested_keys[-1]]