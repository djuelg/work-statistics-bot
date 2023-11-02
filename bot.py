import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from conversation.content.morning_conversation import create_morning_conversation
from conversation.engine import ConversationEngine, AnswerableMessage, MultiAnswerMessage
from secrets import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

cengine = ConversationEngine()

# TODO: Use example of PicklePersistence, and maybe ConversationHandler:
# https://docs.python-telegram-bot.org/en/v20.6/examples.persistentconversationbot.html


def create_answer_options(message):
    buttons_1d, buttons_2d = [], []
    for row in message.content.predefined_answers:
        if isinstance(row, list):
            buttons_2d.append([InlineKeyboardButton(button_text, callback_data=button_text) for button_text in row])
        else:
            buttons_1d.append(InlineKeyboardButton(row, callback_data=row))
    return InlineKeyboardMarkup([buttons_1d] if buttons_1d else buttons_2d)


async def send_next_messages(context, update):
    while cengine.queue:
        message = cengine.next_message()
        reply_markup = None
        if isinstance(message, AnswerableMessage):
            reply_markup = create_answer_options(message)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=message.content.text, reply_markup=reply_markup
        )

        message.mark_as_sent()
        if message.requires_user_input():
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine.begin_conversation(create_morning_conversation())
    await send_next_messages(context, update)


async def standard_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.message.text)
        await send_next_messages(context, update)
    else:
        pass  # ignore unexpected messages



async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.callback_query.data)
        if not isinstance(cengine.current_message, MultiAnswerMessage) or update.callback_query.data == 'Fertig':  # TODO Refactor plain Fertig string
            await send_next_messages(context, update)
    else:
        pass  # ignore unexpected button taps


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    standard_response_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), standard_response_callback)
    callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(standard_response_handler)
    application.add_handler(callback_handler)

    application.run_polling()