import copy
import random
from collections import deque

from conversation.message_types import AnswerableMessage, FreeformMessage, MultiAnswerMessage, Message, NoOpMessage, \
    WordlessMessage
from freeform_chat.freeform_client_base import ROLE_ASSISTANT, ROLE_USER

KEY_GROUPING_RECENTLY = 'recently_used'
CURRENT_CONVERSATION_KEY = "current_conversation"
CONVERSATION_MESSAGES_KEY = f"{CURRENT_CONVERSATION_KEY}.messages"
CONVERSATION_REMEDY_KEY = f"{CURRENT_CONVERSATION_KEY}.remedy_messages"
DAILY_QUESTIONNAIRE_KEY = 'daily_questionnaire'
HISTORY_KEY = 'history'
MULTI_ANSWER_FINISHED = 'Fertig'


# TODO: Remove as soon as ptb user_data does not rely on cengine anymore (after migration)
class MessageContent:
    def __init__(self, text=None, predefined_answers=None):
        self.text = text if not isinstance(text, list) else random.choice(text)
        self.predefined_answers = predefined_answers


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
    recent_six = recent_items[:min(6, len(recent_items))]
    recent_six.reverse()

    if recent_six:
        predefined_answers.insert(0, recent_six[:3])
        if len(recent_six) > 3:
            predefined_answers.insert(0, recent_six[3:])
    return predefined_answers


class ConversationEngine:
    def __init__(self, queue=None, state=None, current_message=None, freeform_client=None):
        self.queue = deque(queue) if queue is not None else deque()
        self.state = state or dict()
        self.current_message = current_message or NoOpMessage()
        self.freeform_client = freeform_client

    def begin_new_conversation(self, conversation):
        self.queue.clear()
        self.drop_state(CURRENT_CONVERSATION_KEY)
        self.queue.extend(conversation)

    def next_message(self):
        self.current_message = self.queue.popleft()
        self.save_conversation_messages(ROLE_ASSISTANT, self.current_message)
        return self.current_message

    def is_waiting_for_user_input(self):
        return self.current_message and self.current_message.has_been_sent() and (
             isinstance(self.current_message, AnswerableMessage) or
             isinstance(self.current_message, FreeformMessage)
        )

    def handle_user_input(self, text):
        self.save_conversation_messages(ROLE_USER, Message(text=text))
        if isinstance(self.current_message, FreeformMessage):
            last_messages = self.get_state(CONVERSATION_MESSAGES_KEY)
            answers = self.freeform_client.generate_responses(last_messages, context_descriptions=self.current_message.context_descriptions, is_oneshot=(not self.current_message.has_freeform_chaining))
            if self.current_message.has_freeform_chaining:
                answers = [FreeformMessage(text=ans) for ans in answers]
            else:
                answers = [Message(text=ans) for ans in answers]
        else:
            is_multi_answer_finished = isinstance(self.current_message, MultiAnswerMessage) and text == MULTI_ANSWER_FINISHED
            answers = self.current_message.handle_user_input(text, cengine=self, is_multi_answer_finished=is_multi_answer_finished)

        if answers:
            self.queue.extendleft(answers)

    def update_history_with_questionnaire(self, on_date):
        daily_questionnaire = self.get_state(DAILY_QUESTIONNAIRE_KEY)
        if daily_questionnaire:
            date_key = f'{HISTORY_KEY}.{on_date}'
            current_data = copy.deepcopy(daily_questionnaire)
            self.update_state(date_key, current_data)
        self.drop_state(DAILY_QUESTIONNAIRE_KEY)

    def update_recently_used_values(self, key, value, recent_size=20):
        recent_key = f'{KEY_GROUPING_RECENTLY}.{key.split(".")[-1]}'
        recent_items = self.get_state(recent_key) or []
        recent_items.insert(0, value)
        recent_items = list(dict.fromkeys(recent_items).keys())[:min(recent_size, len(recent_items))]
        self.update_state(recent_key, recent_items)

    def save_conversation_messages(self, role, current_message, conversation_key=CONVERSATION_MESSAGES_KEY):
        from conversation.content.questionaire_conversation import MotivationQuestion, MentalFatigueQuestion, \
            StressQuestion, EnergyQuestion
        if not str(current_message) or str(current_message) == 'Fertig':
            return
        if len(str(current_message)) == 1 and str(current_message).isnumeric():
            return
        if isinstance(current_message, WordlessMessage) or \
                isinstance(current_message, MotivationQuestion) or \
                isinstance(current_message, EnergyQuestion) or \
                isinstance(current_message, StressQuestion) or \
                isinstance(current_message, MentalFatigueQuestion):
            return
        self.append_state(conversation_key, (role, str(current_message)))

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