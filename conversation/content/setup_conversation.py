from conversation.engine import Message, SingleAnswerMessage, update_state_single_answer_callback, AnswerableMessage, \
    MultiAnswerMessage


def create_setup_conversation(first_met=True):
    return [
        FirstMetMessage() if first_met else UpdateSetupMessage(),
        IntroductionMessage(),
        NameQuestion(),
        NameAnswerMessage(),
        WorkBeginQuestion(),
        MultiAnswerExampleMessage(),
        SetupWrapupMessage()
    ]


class FirstMetMessage(Message):
    PROMPTS = [
        "Hey! Freut mich dich kennenzulernen.",
        "Hi! Schön dich kennenzulernen.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class IntroductionMessage(Message):
    PROMPTS = [
        "Ich bin ein Bot, der mit dir erfasst, woran du tagtäglich arbeitest und in welcher Verfassung "
        "du dabei bist. Das kann dabei helfen, ein Gefühl für Stimmungslagen zu entwickeln, Probleme im Alltag"
        "besser als solche zu identifizieren und Zusammenhänge von Stimmungen und deren Ursachen besser zu erkennen. "
        "So gesehen eine kleine fortlaufende Retrospektive. "
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
        "Okay, nun zu dir. Wie heißt du?",
        "Jetzt zu dir. Wie möchtest du genannt werden?",
        "Nun zu dir. Bei welchem Namen soll ich dich nennen?",
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


def no_op_callback(key, value, cengine=None, is_multi_answer_finished=False):
    pass


class MultiAnswerExampleMessage(MultiAnswerMessage):
    PROMPTS = [
        "Manchmal stelle ich Fragen bei denen du zum einen Mehrere und zum Anderen eigene Antworten geben kannst. "
        "Eigene Antworten kannst du einfach per Chat senden. Wenn du alle gewünschten Antworten gewählt hast, "
        "klicke auf Fertig damit es weiter geht. Als Beispiel: Worauf freust du dich heute noch?",
    ]
    STATES = [
        ["Mittagessen", "Ein Treffen", "Das Abendprogramm"],
        ["Fertig"]
    ]

    def __init__(self):
        super().__init__(self.PROMPTS, "NO_OP", no_op_callback, self.STATES)


class SetupWrapupMessage(Message):
    PROMPTS = [
        "Gut danke, du weißt jetzt alles wichtige. Ich melde mich später wieder.",
        "Okay, dann weißt du nun alles wichtige und hörst später wieder von mir.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)
