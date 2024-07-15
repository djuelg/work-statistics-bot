import random

from freeform_chat.freeform_client_base import ROLE_ASSISTANT


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


class WordlessMessage(Message):
    def __init__(self):
        super(WordlessMessage, self).__init__("")


class NoOpMessage(WordlessMessage):
    def __init__(self):
        self._sent = True
        super(NoOpMessage, self).__init__()


class StickerMessage(WordlessMessage):
    def __init__(self, sticker_id):
        self.sticker_id = sticker_id
        super(StickerMessage, self).__init__()


class ImageMessage(WordlessMessage):
    def __init__(self, image):
        self.image = image
        super(ImageMessage, self).__init__()


class ImageGroupMessage(WordlessMessage):
    def __init__(self, media_group):
        self.media_group = media_group
        super(ImageGroupMessage, self).__init__()


class FreeformMessage(Message):
    def __init__(self, text, has_freeform_chaining=True, context_descriptions=""):
        self.has_freeform_chaining = has_freeform_chaining
        self.context_descriptions = context_descriptions
        super(FreeformMessage, self).__init__(text)


class GeneratedMessage(Message):
    def __init__(self, context_descriptions, conversation_messages_key, last_messages=None, model=None):
        self.context_descriptions = context_descriptions
        self.conversation_messages_key = conversation_messages_key
        self.last_messages = last_messages
        self.model = model
        super().__init__("")

    def content(self, cengine=None):
        last_messages = self.last_messages or cengine.get_state(self.conversation_messages_key)
        answers = cengine.freeform_client.generate_responses(
            last_messages,
            context_descriptions=self.context_descriptions,
            is_oneshot=True,
            max_tokens=600,
            model=self.model
        )
        answers = [answer for sublist in answers for answer in sublist.split("\n\n")]
        self._content.text = "\n\n".join(answers)

        cengine.save_conversation_messages(ROLE_ASSISTANT, self._content.text, conversation_key=self.conversation_messages_key)
        return self._content


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
