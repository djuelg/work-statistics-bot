import json
import logging
import os
from datetime import datetime, timedelta

import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, PicklePersistence

from conversation.content.afternoon_conversation import create_afternoon_conversation
from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import create_setup_conversation, WorkBeginQuestion
from conversation.engine import ConversationEngine, MultiAnswerMessage, SingleAnswerMessage, AnswerableMessage, \
    MULTI_ANSWER_FINISHED

DAYS_MON_FRI = (1, 2, 3, 4, 5)
TZ_DE = 'Europe/Berlin'
CENGINE ='conversation_engine'

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
if not BOT_TOKEN:
    from secrets import BOT_TOKEN

KEY_AFTERNOON_QUESTIONNAIRE = 'daily_questionnaire.afternoon'
KEY_MORNING_QUESTIONNAIRE = 'daily_questionnaire.morning'


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
            chat_id=chat_id, text=message.content(cengine=cengine).text, reply_markup=reply_markup,
            parse_mode='markdown'
        )

        message.mark_as_sent()
        if isinstance(message, AnswerableMessage):
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


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    json_str = json.dumps(context.user_data[CENGINE].state, indent=4)
    await update.message.reply_text(
        f'This is what you already told me: \n{json_str}'
    )


async def handle_text_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.message.text)


async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.callback_query.data)


async def general_callback_handler(update, context, user_input):
    cengine = get_conversation_engine(context)
    if cengine.is_waiting_for_user_input():
        cengine.handle_user_input(user_input)

        if not isinstance(cengine.current_message, MultiAnswerMessage) or user_input == MULTI_ANSWER_FINISHED:
            if isinstance(cengine.current_message, WorkBeginQuestion):
                await setup_jobqueue_callbacks(cengine, context, update)

            await send_next_messages(context, update.effective_chat.id)
    else:
        pass  # ignore unexpected button taps


async def setup_jobqueue_callbacks(cengine, context, update):
    work_begin_hour = int(cengine.get_state(WorkBeginQuestion.CALLBACK_KEY))
    morning_time = datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=work_begin_hour, minute=7))
    # morning_time = datetime.now() + timedelta(seconds=20)  # debug override
    morning_time = pytz.timezone(TZ_DE).localize(morning_time)
    morning_job_name = f"{update.effective_chat.id}_morning_message"

    afternoon_time = morning_time + timedelta(hours=4, minutes=15)
    # afternoon_time = morning_time + timedelta(seconds=30) # debug override
    afternoon_job_name = f"{update.effective_chat.id}_afternoon_message"

    evening_time = morning_time.replace(hour=19, minute=37)
    # evening_time = morning_time + timedelta(seconds=50) # debug override
    evening_job_name = f"{update.effective_chat.id}_evening_message"

    context.job_queue.run_daily(jobqueue_callback, morning_time,
                                chat_id=update.effective_chat.id, name=morning_job_name, days=DAYS_MON_FRI, data=context)
    context.job_queue.run_daily(jobqueue_callback, afternoon_time,
                                chat_id=update.effective_chat.id, name=afternoon_job_name, days=DAYS_MON_FRI, data=context)
    context.job_queue.run_daily(jobqueue_callback, evening_time,
                                chat_id=update.effective_chat.id, name=evening_job_name, days=DAYS_MON_FRI, data=context)


async def jobqueue_callback(context: ContextTypes.user_data) -> None:
    passed_context = context.job.data

    cengine = get_conversation_engine(passed_context)
    if context.job.name == f"{context.job.chat_id}_morning_message":
        conversation = create_morning_conversation()
    elif context.job.name == f"{context.job.chat_id}_afternoon_message":
        conversation = create_afternoon_conversation()
    elif context.job.name == f"{context.job.chat_id}_evening_message":
        cengine.copy_today_to_history()
        conversation = []  # TODO Later create evening statistics
    else:
        return

    cengine.begin_new_conversation(conversation)  # TODO Don't always begin new conversation (?)
    await send_next_messages(passed_context, context.job.chat_id)


async def override_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.begin_new_conversation(create_setup_conversation(first_met=False))
    await send_next_messages(context, update.effective_chat.id)


async def override_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.drop_state(KEY_MORNING_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_morning_conversation())
    await send_next_messages(context, update.effective_chat.id)


async def override_afternoon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.drop_state(KEY_AFTERNOON_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_afternoon_conversation())
    await send_next_messages(context, update.effective_chat.id)


async def update_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.copy_today_to_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Daten in History übertragen.'
    )


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversation_bot.pkl", update_interval=10)
    application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop_and_delete', stop)
    show_handler = CommandHandler('show', show_data)
    override_setup_handler = CommandHandler('override_setup', override_setup)
    override_morning_handler = CommandHandler('override_morning', override_morning)
    override_afternoon_handler = CommandHandler('override_afternoon', override_afternoon)
    update_history_handler = CommandHandler('update_history', update_history)
    text_callback_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_callbacks)
    button_callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(show_handler)
    application.add_handler(override_setup_handler)
    application.add_handler(override_morning_handler)
    application.add_handler(override_afternoon_handler)
    application.add_handler(update_history_handler)
    application.add_handler(text_callback_handler)
    application.add_handler(button_callback_handler)

    if WEBHOOK_URL:
        application.run_webhook(listen="0.0.0.0", webhook_url=WEBHOOK_URL)
    else:
        application.run_polling()