import logging
from datetime import datetime, timedelta
from typing import Dict

import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, PicklePersistence

from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import create_setup_conversation, WorkBeginQuestion
from conversation.engine import ConversationEngine, MultiAnswerMessage, SingleAnswerMessage
from secrets import BOT_TOKEN

DAYS_MON_FRI = (1, 2, 3, 4, 5)
TZ_DE = 'Europe/Berlin'
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


async def send_next_messages(context, chat_id):
    cengine = get_conversation_engine(context)
    while cengine.queue:
        message = cengine.next_message()
        reply_markup = None
        if isinstance(message, SingleAnswerMessage) or isinstance(message, MultiAnswerMessage):
            reply_markup = create_answer_options(message)

        await context.bot.send_message(
            chat_id=chat_id, text=message.content(cengine=cengine).text, reply_markup=reply_markup
        )

        message.mark_as_sent()
        if message.requires_user_input():
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.begin_new_conversation(create_setup_conversation())
    await send_next_messages(context, update.effective_chat.id)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Daten werden zurückgesetzt.'
    )
    del context.user_data[CENGINE]


def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = [f"{key}:  {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data[CENGINE].state
    facts = [f"{key}:  {value}" for key, value in user_data.items()]
    result = "\n".join(facts).join(["\n", "\n"])
    await update.message.reply_text(
        f'This is what you already told me: {result}'
    )


async def handle_text_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.message.text)


async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.callback_query.data)


async def general_callback_handler(update, context, user_input):
    cengine = get_conversation_engine(context)
    if cengine.is_waiting_for_user_input():
        if not isinstance(cengine.current_message, MultiAnswerMessage) or user_input != MULTI_ANSWER_FINISHED:
            cengine.handle_user_input(user_input)
        if not isinstance(cengine.current_message, MultiAnswerMessage) or user_input == MULTI_ANSWER_FINISHED:
            if isinstance(cengine.current_message, WorkBeginQuestion):
                await setup_jobqueue_callbacks(cengine, context, update)

            await send_next_messages(context, update.effective_chat.id)
    else:
        pass  # ignore unexpected button taps


async def setup_jobqueue_callbacks(cengine, context, update):
    work_begin_hour = int(cengine.state.get(WorkBeginQuestion.KEY))
    morning_time = datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=work_begin_hour, minute=7))  # (hour=14,minute=39,second=30))
    morning_time = pytz.timezone(TZ_DE).localize(morning_time)
    morning_job_name = f"{update.effective_chat.id}_morning_message"
    afternoon_time = morning_time + timedelta(hours=4, minutes=15)
    afternoon_job_name = f"{update.effective_chat.id}_afternoon_message"

    context.job_queue.run_daily(jobqueue_callback, morning_time,
                                chat_id=update.effective_chat.id, name=morning_job_name, days=DAYS_MON_FRI, data=context)
    context.job_queue.run_daily(jobqueue_callback, afternoon_time,
                                chat_id=update.effective_chat.id, name=afternoon_job_name, days=DAYS_MON_FRI, data=context)


async def jobqueue_callback(context: ContextTypes.user_data) -> None:
    passed_context = context.job.data

    cengine = get_conversation_engine(passed_context)
    if context.job.name == f"{context.job.chat_id}_morning_message":
        conversation = create_morning_conversation()
    elif context.job.name == f"{context.job.chat_id}_afternoon_message":
        conversation = create_morning_conversation()  # TODO replace with afternoon_conversation
        # TODO: Check ob wir hier die Daten der morning_conversation haben (weil passed_context alt sein könnte)
    else:
        return

    cengine.begin_new_conversation(conversation)  # TODO Don't always begin new conversation
    await send_next_messages(passed_context, context.job.chat_id)


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversation_bot.pkl", update_interval=10)
    application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    show_handler = CommandHandler('show', show_data)
    standard_response_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_callbacks)
    callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(show_handler)
    application.add_handler(standard_response_handler)
    application.add_handler(callback_handler)

    application.run_polling()