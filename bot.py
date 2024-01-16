import json
import logging
import os
from datetime import datetime, timedelta

import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, PicklePersistence, Application

from conversation.content.afternoon_conversation import create_afternoon_conversation
from conversation.content.generic_messages import ByeCatSticker
from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import create_setup_conversation, WorkBeginQuestion
from conversation.content.weekly_conversation import create_weekly_conversation
from conversation.engine import ConversationEngine, MultiAnswerMessage, SingleAnswerMessage, AnswerableMessage, \
    MULTI_ANSWER_FINISHED, StickerMessage, HISTORY_KEY, ImageMessage, ImageGroupMessage
from statistics.chart_generator import ChartGenerator

DAYS_MON_FRI = (1, 2, 3, 4, 5)
DAYS_SUN = (0,)
TZ_DE = 'Europe/Berlin'
CENGINE ='conversation_engine'

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
if not BOT_TOKEN:
    from chatbot_secrets import BOT_TOKEN

KEY_AFTERNOON_QUESTIONNAIRE = 'daily_questionnaire.afternoon'
KEY_MORNING_QUESTIONNAIRE = 'daily_questionnaire.morning'

MORNING_JOB = "{}_morning_message"
AFTERNOON_JOB = "{}_afternoon_message"
EVENING_JOB = "{}_evening_message"
WEEKLY_JOB = "{}_weekly_message"
JOB_NAMES = [MORNING_JOB, AFTERNOON_JOB, EVENING_JOB, WEEKLY_JOB]

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


def create_answer_options(message, cengine=None):
    buttons_1d, buttons_2d = [], []
    for row in message.content(cengine=cengine).predefined_answers:
        if isinstance(row, list):
            buttons_2d.append([create_button(button_text) for button_text in row])
        else:
            buttons_1d.append(create_button(row))
    return InlineKeyboardMarkup([buttons_1d] if buttons_1d else buttons_2d)


async def send_next_messages(bot, cengine, chat_id):
    while cengine.queue:
        message = cengine.next_message()
        reply_markup = None
        if isinstance(message, SingleAnswerMessage) or isinstance(message, MultiAnswerMessage):
            reply_markup = create_answer_options(message, cengine=cengine)

        if isinstance(message, StickerMessage):
            await bot.send_sticker(chat_id=chat_id, sticker=message.sticker_id)
        elif isinstance(message, ImageMessage):
            await bot.send_photo(chat_id, message.image)
        elif isinstance(message, ImageGroupMessage):
            media_group = [InputMediaPhoto(image) for image in message.media_group]
            await bot.send_media_group(chat_id, media_group)
        else:
            await bot.send_message(
                chat_id=chat_id, text=message.content(cengine=cengine).text, reply_markup=reply_markup,
                parse_mode='markdown', disable_web_page_preview=True  # TODO: ggf. switch to MarkdownV2
            )

        message.mark_as_sent()
        if isinstance(message, AnswerableMessage):
            break


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.begin_new_conversation(create_setup_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=ByeCatSticker.ID)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Schade, dass du gehst. Falls du den Bot wieder nutzen möchtest, kannst du das mit `/start` tun. Deine Daten werden jedoch nun zurückgesetzt.'
    )

    current_jobs = [job for job_name in JOB_NAMES for job in
                    context.job_queue.get_jobs_by_name(job_name.format(update.effective_chat.id))]
    for job in current_jobs:
        job.schedule_removal()
    del context.user_data[CENGINE]


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    json_str = json.dumps(context.user_data[CENGINE].state, indent=4)
    await update.message.reply_text(
        f'This is what you already told me: \n{json_str}'
    )


async def show_weekly_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cengine = get_conversation_engine(context)
    charts = await create_weekly_charts(cengine)
    conversation = create_weekly_conversation(charts)
    cengine.begin_new_conversation(conversation)
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


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
                setup_jobqueue_callbacks(cengine, context, update.effective_chat.id)

            await send_next_messages(context.bot, cengine, update.effective_chat.id)
    else:
        pass  # ignore unexpected button taps


def setup_jobqueue_callbacks(cengine, context, chat_id, job_queue=None, application=None):
    work_begin_hour = int(cengine.get_state(WorkBeginQuestion.CALLBACK_KEY))
    morning_time = datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=work_begin_hour, minute=7))
    # morning_time = datetime.now() + timedelta(seconds=10)  # debug override
    morning_time = pytz.timezone(TZ_DE).localize(morning_time)
    morning_job_name = MORNING_JOB.format(chat_id)

    afternoon_time = morning_time + timedelta(hours=4, minutes=15)
    # afternoon_time = morning_time + timedelta(seconds=30) # debug override
    afternoon_job_name = AFTERNOON_JOB.format(chat_id)

    evening_time = morning_time.replace(hour=19, minute=37)
    # evening_time = morning_time + timedelta(seconds=50) # debug override
    evening_job_name = EVENING_JOB.format(chat_id)

    weekly_job_name = WEEKLY_JOB.format(chat_id)

    job_data = (application, context, cengine)
    job_queue = job_queue or context.job_queue
    job_queue.run_daily(jobqueue_callback, morning_time, chat_id=chat_id, name=morning_job_name,
                        days=DAYS_MON_FRI, data=job_data, job_kwargs={'id': morning_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, afternoon_time, chat_id=chat_id, name=afternoon_job_name,
                        days=DAYS_MON_FRI, data=job_data, job_kwargs={'id': afternoon_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, evening_time, chat_id=chat_id, name=evening_job_name,
                        data=job_data, job_kwargs={'id': evening_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, morning_time, chat_id=chat_id, name=weekly_job_name,
                        days=DAYS_SUN, data=job_data, job_kwargs={'id': weekly_job_name, 'replace_existing': True})


async def jobqueue_callback(context: ContextTypes.user_data) -> None:
    application, passed_context, cengine = context.job.data

    if context.job.name == MORNING_JOB.format(context.job.chat_id):
        conversation = create_morning_conversation()
    elif context.job.name == AFTERNOON_JOB.format(context.job.chat_id):
        conversation = create_afternoon_conversation()
    elif context.job.name == EVENING_JOB.format(context.job.chat_id):
        cengine.copy_today_to_history()
        conversation = []  # TODO Later create evening statistics, if day has data. Maybe reflect here on history?
    elif context.job.name == WEEKLY_JOB.format(context.job.chat_id):
        charts = await create_weekly_charts(cengine)
        conversation = create_weekly_conversation(charts)
    else:
        return

    cengine.begin_new_conversation(conversation)  # TODO Don't always begin new conversation (?)
    bot = application.bot if application else passed_context.bot
    await send_next_messages(bot, cengine, context.job.chat_id)


async def create_weekly_charts(cengine):
    history = cengine.get_state(HISTORY_KEY)
    try:
        chart_generator = ChartGenerator(history)
        start_date = str((datetime.now() - timedelta(days=7)).date())
        end_date = str(datetime.now().date())
        line_chart_buffer = chart_generator.generate_line_chart(start_date=start_date, end_date=end_date)
        tasks_chart_buffer, mood_chart_buffer = chart_generator.generate_bar_charts(start_date=start_date, end_date=end_date)
        return [line_chart_buffer, tasks_chart_buffer, mood_chart_buffer]
    except:
        return None


async def override_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.begin_new_conversation(create_setup_conversation(first_met=False))
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def override_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.drop_state(KEY_MORNING_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_morning_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def override_afternoon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.drop_state(KEY_AFTERNOON_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_afternoon_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def update_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context)
    cengine.copy_today_to_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Daten in History übertragen.'
    )


async def setup_jobqueue_after_startup(application: Application) -> None:
    context = application.context_types.context
    for chat_id, user_data in application.user_data.items():
        if 'conversation_engine' in user_data and 'history' in user_data['conversation_engine'].state:
            cengine = user_data['conversation_engine']
            setup_jobqueue_callbacks(cengine, context, chat_id, job_queue=application.job_queue, application=application)


# origin: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot
if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversation_bot.pkl", update_interval=10)
    application = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence)\
        .post_init(setup_jobqueue_after_startup).build()

    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop_and_delete', stop)
    show_handler = CommandHandler('show', show_data)
    show_weekly_handler = CommandHandler('show_weekly', show_weekly_statistics)
    override_setup_handler = CommandHandler('override_setup', override_setup)
    override_morning_handler = CommandHandler('override_morning', override_morning)
    override_afternoon_handler = CommandHandler('override_afternoon', override_afternoon)
    update_history_handler = CommandHandler('update_history', update_history)
    text_callback_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_callbacks)
    button_callback_handler = CallbackQueryHandler(handle_button_callbacks)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(show_handler)
    application.add_handler(show_weekly_handler)
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