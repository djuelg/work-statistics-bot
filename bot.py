import logging
from typing import Dict

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, PicklePersistence

from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import create_setup_conversation
from conversation.engine import ConversationEngine, MultiAnswerMessage, SingleAnswerMessage
from secrets import BOT_TOKEN

CENGINE ='conversation_engine'
MULTI_ANSWER_FINISHED = 'Fertig'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_conversation_engine(context):
    cengine = context.user_data.get(CENGINE, None)
    if cengine is None:
        cengine = ConversationEngine()
        context.user_data[CENGINE] = cengine
    return cengine


def create_button(data):
    content = (data[0], data[1]) if isinstance(data, tuple) else (data, data)
    return InlineKeyboardButton(content[0], callback_data=content[1])


def create_answer_options(message):
    buttons_1d, buttons_2d = [], []
    for row in message.content().predefined_answers:
        if isinstance(row, list):
            buttons_2d.append([create_button(button_text) for button_text in row])
        else:
            buttons_1d.append(create_button(row))
    return InlineKeyboardMarkup([buttons_1d] if buttons_1d else buttons_2d)


async def send_next_messages(context, update):
    cengine = get_conversation_engine(context)
    while cengine.queue:
        message = cengine.next_message()
        reply_markup = None
        if isinstance(message, SingleAnswerMessage) or isinstance(message, MultiAnswerMessage):
            reply_markup = create_answer_options(message)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=message.content(cengine=cengine).text, reply_markup=reply_markup
        )

        message.mark_as_sent()
        if message.requires_user_input():
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.begin_conversation(create_setup_conversation())
    await send_next_messages(context, update)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Daten werden zurückgesetzt.'
    )
    del context.user_data[CENGINE]


def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = [f"{key}:  {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"This is what you already told me: {facts_to_str(context.user_data[CENGINE].state)}"
    )


async def standard_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.message.text)
        await send_next_messages(context, update)
    else:
        pass  # ignore unexpected messages


async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    if cengine.is_waiting_for_user_input():
        if not isinstance(cengine.current_message, MultiAnswerMessage) or update.callback_query.data != MULTI_ANSWER_FINISHED:
            cengine.handle_user_input(update.callback_query.data)
        if not isinstance(cengine.current_message, MultiAnswerMessage) or update.callback_query.data == MULTI_ANSWER_FINISHED:
            await send_next_messages(context, update)
    else:
        pass  # ignore unexpected button taps


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversation_bot.pkl")
    application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    show_handler = CommandHandler('show', show_data)
    standard_response_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), standard_response_callback)
    callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(show_handler)
    application.add_handler(standard_response_handler)
    application.add_handler(callback_handler)

    application.run_polling()