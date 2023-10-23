import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from conversation.content.morning_conversation import create_morning_conversation
from conversation.engine import ConversationEngine, PredefinedAnswersMessage
from secrets import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

cengine = ConversationEngine()

# TODO: Use example of PicklePersistence, and maybe ConversationHandler:
# https://docs.python-telegram-bot.org/en/v20.6/examples.persistentconversationbot.html


async def send_next_messages(context, update):
    while cengine.queue:
        message = cengine.next_message()
        content = message.consume()
        button_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(button_text, callback_data=button_text) for button_text in content.predefined_answers]]
        ) if isinstance(message, PredefinedAnswersMessage) else None

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=content.text, reply_markup=button_markup
        )

        if message.requires_user_input():
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine.begin_conversation(create_morning_conversation())
    await send_next_messages(context, update)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.message.text)

    await send_next_messages(context, update)


async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.callback_query.data)
    await send_next_messages(context, update)

# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(callback_handler)

    application.run_polling()