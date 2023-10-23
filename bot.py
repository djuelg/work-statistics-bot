import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from conversation.content.morning_conversation import create_morning_conversation
from conversation.engine import ConversationEngine
from secrets import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

cengine = ConversationEngine()


async def send_next_messages(context, update):
    while cengine.queue:
        message = cengine.next_message()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message.consume())
        if message.requires_user_input():
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine.begin_conversation(create_morning_conversation())
    await send_next_messages(context, update)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(update.message.text)

    await send_next_messages(context, update)


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)

    application.run_polling()