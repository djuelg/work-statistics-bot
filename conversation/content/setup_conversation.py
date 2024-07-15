import copy

from conversation.content.generic_messages import ThumbsUpCatSticker
from conversation.engine import update_state_multi_answer_callback, update_state_single_answer_callback, \
    CURRENT_CONVERSATION_KEY
from conversation.message_types import SingleAnswerMessage, MultiAnswerMessage, Message, AnswerableMessage


def create_setup_conversation(first_met=True):
    conversation_flow = [
        FirstMetMessage() if first_met else UpdateSetupMessage(),
        IntroductionMessage(),
        NameQuestion(),
        NameAnswerMessage(),
        WorkBeginQuestion()]

    if first_met:
        conversation_flow += [MultiAnswerIntroductionMessage(),
        EnergyRemediesQuestion(),
        EnergyRemediesReaction(),
        StressRemediesQuestion(),
        MentalFatigueRemediesQuestion(),
        MotivationRemediesQuestion()]
    else:
        conversation_flow += [ReworkRemediesQuestion()]

    conversation_flow += [
        SetupWrapupMessage(),
        ThumbsUpCatSticker(),
    ]
    return conversation_flow


class FirstMetMessage(Message):
    PROMPTS = [
        "Hey! Freut mich dich kennenzulernen.",
        "Hi! Schön dich kennenzulernen.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class IntroductionMessage(Message):
    PROMPTS = [
        "Ich bin ein Bot, der mit dir erfasst, woran du tagtäglich arbeitest und in welcher Verfassung du dabei bist. Denn psychische Belastungen, wie etwa Stress, oder geistige Erschöpfung, sollten nicht einfach hingenommen, sondern im Arbeitsalltag berücksichtigt werden. \n"
        "Indem ich mich regelmäßig bei dir melde, versuche ich kleine Momente des Innehaltens zu schaffen: Der Mensch unterliegt wechselnder Energiereserven und Konzentrationsfähigkeit. Dies zu berücksichtigen und empathisch mit sich selbst zu sein, kann dabei helfen, mit Belastungen im Alltag besser umzugehen und ein Gefühl für die eigenen Stimmungslagen zu entwickeln."
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


class ReworkRemediesQuestion(SingleAnswerMessage):
    CALLBACK_KEY = f'{CURRENT_CONVERSATION_KEY}.rework_remedies'
    PROMPTS = [
        "Möchtest du gemeinsam überlegen, was dir persönlich in schwierigen Phasen kurzfristig helfen könnte?"]
    STATES = [["Ja gerne"], ["Nein, danke"]]

    def __init__(self, callback=None):
        callback = callback if callback else self._rework_remedies_callback
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, self.STATES)

    def _rework_remedies_callback(self, key, value, cengine=None, is_multi_answer_finished=False):
        cengine.drop_state("remedies")
        if value == "Ja gerne":
            conversation_flow = [ EnergyRemediesQuestion(), EnergyRemediesReaction(), StressRemediesQuestion(),
                     MentalFatigueRemediesQuestion(), MotivationRemediesQuestion()]
            conversation_flow.reverse()
            return conversation_flow


class MultiAnswerIntroductionMessage(Message):
    PROMPTS = [
        "Manchmal stelle ich Fragen bei denen du zum einen _mehrere_ und zum Anderen _eigene_ Antworten geben kannst. "
        "Eigene Antworten kannst du einfach per Chat senden. Wenn du alle gewünschten Antworten gewählt hast, "
        "klicke auf Fertig damit es weiter geht. Folgendes würde ich gerne wissen:",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)


class EnergyRemediesQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'remedies.energy_remedies'
    PROMPTS = ["Wenn du an einem Tag überdurchschnittlich müde bist, was würde dir helfen produktiv damit umzugehen? Überlege erst selbst bevor du die Beispiele nutzt."]
    STATES = [
        ["Meditation", "Spazieren gehen", "Sport treiben"],
        ["Musik hören", "Zeit in der Natur", "Yoga"],
        ["Tiefes Atmen", "Kurzer Schlaf", "Etwas essen"],
        ["Lesen", "Kunst", "Mit jemandem sprechen"],
        ["Pomodoros", "Stehend arbeiten", "Kalt duschen"],
        ["Fertig"]
    ]

    def __init__(self, callback=update_state_multi_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, copy.deepcopy(self.STATES))


class EnergyRemediesReaction(Message):
    CALLBACK_KEY = 'remedies.energy_remedies'

    def __init__(self):
        super().__init__("")

    def content(self, cengine=None):
        energy_remedies_items = cengine.get_state(self.CALLBACK_KEY)
        energy_remedies_items = energy_remedies_items or ["Keine"]
        self._content.text = f"Du hast angegeben, dass dir folgende Dinge helfen, wenn du an einem Tag überdurchschnittlich müde bist: _{', '.join(energy_remedies_items)}_. " \
                             f"Diese Informationen helfen mir dir in Zukunft gezielte Vorschläge machen zu können. Wir sind gleich fertig, aber drei Fragen habe ich noch:"
        return self._content


class StressRemediesQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'remedies.stress_remedies'
    PROMPTS = ["Wenn du an einem Tag besonders gestresst bist, was würde dir helfen produktiv damit umzugehen? Überlege erst selbst bevor du die Beispiele nutzt."]
    STATES = [
        ["Meditation", "Spazieren gehen", "Sport treiben"],
        ["Musik hören", "Zeit in der Natur", "Yoga"],
        ["Tiefes Atmen", "Kurzer Schlaf", "Etwas essen"],
        ["Lesen", "Kunst", "Mit jemandem sprechen"],
        ["Pomodoros", "Stehend arbeiten", "Kalt duschen"],
        ["Fertig"]
    ]

    def __init__(self, callback=update_state_multi_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, copy.deepcopy(self.STATES))


class MentalFatigueRemediesQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'remedies.mental_fatigue_remedies'
    PROMPTS = ["Wenn du an einem Tag schnell mental ermüdest, was würde dir helfen produktiv damit umzugehen? Überlege erst selbst bevor du die Beispiele nutzt."]
    STATES = [
        ["Meditation", "Spazieren gehen", "Sport treiben"],
        ["Musik hören", "Zeit in der Natur", "Yoga"],
        ["Tiefes Atmen", "Kurzer Schlaf", "Etwas essen"],
        ["Lesen", "Kunst", "Mit jemandem sprechen"],
        ["Pomodoros", "Stehend arbeiten", "Kalt duschen"],
        ["Fertig"]
    ]

    def __init__(self, callback=update_state_multi_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, copy.deepcopy(self.STATES))


class MotivationRemediesQuestion(MultiAnswerMessage):
    CALLBACK_KEY = 'remedies.motivation_remedies'
    PROMPTS = ["Wenn du an einem Tag sehr motivationslos bist, was würde dir helfen produktiv damit umzugehen? Überlege erst selbst bevor du die Beispiele nutzt."]
    STATES = [
        ["Meditation", "Spazieren gehen", "Sport treiben"],
        ["Musik hören", "Zeit in der Natur", "Yoga"],
        ["Tiefes Atmen", "Kurzer Schlaf", "Etwas essen"],
        ["Lesen", "Kunst", "Mit jemandem sprechen"],
        ["Pomodoros", "Stehend arbeiten", "Kalt duschen"],
        ["Fertig"]
    ]

    def __init__(self, callback=update_state_multi_answer_callback):
        super().__init__(self.PROMPTS, self.CALLBACK_KEY, callback, copy.deepcopy(self.STATES))


class SetupWrapupMessage(Message):
    PROMPTS = [
        "Gut danke, ich weißt jetzt alles wichtige. Ich melde mich später wieder bei dir.",
        "Okay, dann weiß ich nun alles wichtige und du hörst später wieder von mir.",
    ]

    def __init__(self):
        super().__init__(self.PROMPTS)

