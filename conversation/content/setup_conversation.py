from conversation.engine import Message, SingleAnswerMessage, update_state_single_answer_callback, AnswerableMessage


def create_setup_conversation(first_met=True):
    return [
        FirstMetMessage() if first_met else UpdateSetupMessage(),
        NameQuestion(),
        NameAnswerMessage(),
        WorkBeginQuestion(),
        SetupWrapupMessage()
    ]


class FirstMetMessage(Message):
    PROMPTS = [
        "Hey! Freut mich dich kennenzulernen.",
        "Hi! Schön dich kennenzulernen.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class UpdateSetupMessage(Message):
    PROMPTS = [
        "Okay, lass uns nochmal durch deine Einstellungen gehen",
        "Gut, schauen wir uns deine Einstellungen nochmal an.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class NameQuestion(AnswerableMessage):
    CALLBACK_KEY = 'username'
    PROMPTS = [
        "Wie heißt du?",
        "Wie möchtest du genannt werden?",
        "Bei welchem Namen soll ich dich nennen?",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, update_state_single_answer_callback)


class NameAnswerMessage(Message):
    PROMPTS = [
        "Alles klar. Ist notiert! Unter der Woche werde ich mich ab jetzt 2-3 mal pro Tag melden, um herauszufinden wie es dir geht :)",
        "Okay, ist notiert! Unter der Woche werde ich mich ab jetzt 2-3 mal pro Tag melden, um herauszufinden wie es dir geht :)",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class WorkBeginQuestion(SingleAnswerMessage):
    CALLBACK_KEY = 'work_begin_time'
    PROMPTS = [
        "Wann fängst du normalerweise morgens an zu arbeiten?",
        "Wann beginnst du im Regelfall morgens mit der Arbeit?"
    ]
    STATES = [
        [("7:00 - 8:00 Uhr", 8), ("8:00 - 9:00 Uhr", 9)],
        [("9:00 - 10:00 Uhr", 10), ("10:00 - 11:00 Uhr", 11)]
    ]

    def __init__(self):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, update_state_single_answer_callback, self.STATES)


class SetupWrapupMessage(Message):
    PROMPTS = [
        "Gut danke, dann melde ich mich später.",
        "Vielen Dank, dann hörst du später wieder von mir.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
