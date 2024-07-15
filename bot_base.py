import calendar
import locale
import os
import pickle
from datetime import datetime, timedelta

import pytz
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, Application

from conversation.content.afternoon_conversation import create_afternoon_conversation
from conversation.content.generic_messages import FREEFORM_CLIENT_DESCRIPTION
from conversation.content.weekly_conversation import create_weekly_conversation
from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import WorkBeginQuestion
from conversation.content.monthly_conversation import create_monthly_conversation
from conversation.engine import ConversationEngine, HISTORY_KEY
from conversation.message_types import SingleAnswerMessage, MultiAnswerMessage, StickerMessage, ImageMessage, \
    ImageGroupMessage, GeneratedMessage
from freeform_chat.gpt_freeform_client import FreeformClient
from statistics.chart_generator import ChartGenerator, CumulatedDataGenerator

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
OPENAI_TOKEN = os.environ.get("OPENAI_TOKEN", None)
if not BOT_TOKEN:
    from chatbot_secrets import BOT_TOKEN
    BOT_TOKEN = BOT_TOKEN
if not OPENAI_TOKEN:
    from chatbot_secrets import OPENAI_TOKEN

DAYS_MON_FRI = (1, 2, 3, 4, 5)
DAYS_SUN = (0,)
TZ_DE = 'Europe/Berlin'

KEY_USERDATA = 'user_data'
KEY_STATE = 'state'
KEY_AFTERNOON_QUESTIONNAIRE = 'daily_questionnaire.afternoon'
KEY_MORNING_QUESTIONNAIRE = 'daily_questionnaire.morning'

MORNING_JOB = "{}_morning_message"
AFTERNOON_JOB = "{}_afternoon_message"
EVENING_JOB = "{}_evening_message"
WEEKLY_JOB = "{}_weekly_message"
MONTHLY_JOB = "{}_monthly_message"
JOB_NAMES = [MORNING_JOB, AFTERNOON_JOB, EVENING_JOB, WEEKLY_JOB, MONTHLY_JOB]

global_cengine_cache = {}  # Global cache that holds pairs of (chat_id -> cengine)


######################## MESSAGING ########################


def get_conversation_engine(context, chat_id=None):
    cengine = global_cengine_cache.get(chat_id, None)
    if cengine:
        if context.user_data and context.user_data.get(KEY_STATE, None) != cengine.state:
            context.user_data[KEY_STATE] = cengine.state
        return cengine

    state = context.user_data.get(KEY_STATE, {})
    freeform_client = FreeformClient(OPENAI_TOKEN, FREEFORM_CLIENT_DESCRIPTION)
    cengine = ConversationEngine(state=state, freeform_client=freeform_client)
    context.user_data[KEY_STATE] = cengine.state
    global_cengine_cache[chat_id] = cengine
    return cengine


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
            if isinstance(message, GeneratedMessage):
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            message_text = message.content(cengine=cengine).text
            if message_text:
                await bot.send_message(
                    chat_id=chat_id, text=message_text, reply_markup=reply_markup,
                    parse_mode='markdown', disable_web_page_preview=True  # TODO: ggf. switch to MarkdownV2
                )

        message.mark_as_sent()
        if cengine.is_waiting_for_user_input():
            break


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


######################## JOB-QUEUE ########################


def migrate_user_data(application):
    KEY_CENGINE = 'conversation_engine'
    for chat_id, user_data in application.user_data.items():
        try:
            cengine = user_data.get(KEY_CENGINE, None)
            if cengine:
                print(f"Migrating user_data for {chat_id}")
                user_data[KEY_STATE] = cengine.state
                del application.user_data[chat_id][KEY_CENGINE]
                del application.persistence.user_data[chat_id][KEY_CENGINE]
        except Exception as e:
            print(f"Migrating failed for {chat_id}")
            print(e)


async def setup_jobqueue_after_startup(application: Application) -> None:
    migrate_user_data(application)

    context = application.context_types.context
    for chat_id, user_data in application.user_data.items():
        if KEY_STATE in user_data and 'history' in user_data[KEY_STATE]:
            cengine = ConversationEngine(state=user_data[KEY_STATE],
                                         freeform_client=FreeformClient(OPENAI_TOKEN, FREEFORM_CLIENT_DESCRIPTION))
            setup_jobqueue_callbacks(cengine, context, chat_id, job_queue=application.job_queue,
                                     application=application)


def setup_jobqueue_callbacks(cengine, context, chat_id, job_queue=None, application=None):
    work_begin_hour = int(cengine.get_state(WorkBeginQuestion.CALLBACK_KEY))
    morning_time = datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=work_begin_hour, minute=7))
    # morning_time = datetime.now() + timedelta(seconds=10)  # debug override
    morning_time = pytz.timezone(TZ_DE).localize(morning_time)
    morning_job_name = MORNING_JOB.format(chat_id)

    afternoon_time = morning_time + timedelta(hours=4, minutes=45)
    # afternoon_time = morning_time + timedelta(seconds=30) # debug override
    afternoon_job_name = AFTERNOON_JOB.format(chat_id)

    evening_time = morning_time.replace(hour=23, minute=37)
    # evening_time = morning_time + timedelta(seconds=50) # debug override
    evening_job_name = EVENING_JOB.format(chat_id)

    weekly_job_name = WEEKLY_JOB.format(chat_id)
    monthly_time = morning_time.replace(hour=20, minute=00)
    monthly_job_name = MONTHLY_JOB.format(chat_id)

    job_data = (application, context)
    job_queue = job_queue or context.job_queue
    job_queue.run_daily(jobqueue_callback, morning_time, chat_id=chat_id, name=morning_job_name,
                        days=DAYS_MON_FRI, data=job_data, job_kwargs={'id': morning_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, afternoon_time, chat_id=chat_id, name=afternoon_job_name,
                        days=DAYS_MON_FRI, data=job_data,
                        job_kwargs={'id': afternoon_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, evening_time, chat_id=chat_id, name=evening_job_name,
                        data=job_data, job_kwargs={'id': evening_job_name, 'replace_existing': True})
    job_queue.run_daily(jobqueue_callback, morning_time, chat_id=chat_id, name=weekly_job_name,
                        days=DAYS_SUN, data=job_data, job_kwargs={'id': weekly_job_name, 'replace_existing': True})
    job_queue.run_monthly(jobqueue_callback, day=-1, when=monthly_time, chat_id=chat_id, name=monthly_job_name,
                          data=job_data, job_kwargs={'id': monthly_job_name, 'replace_existing': True})


async def jobqueue_callback(context: ContextTypes.user_data) -> None:
    application, passed_context = context.job.data
    if context.job.chat_id in global_cengine_cache:
        cengine = global_cengine_cache[context.job.chat_id]
    else:
        state = get_cengine_state_from_persistence(context.job.chat_id)
        cengine = ConversationEngine(state=state,
                                     freeform_client=FreeformClient(OPENAI_TOKEN, FREEFORM_CLIENT_DESCRIPTION))
        global_cengine_cache[context.job.chat_id] = cengine

    if not cengine:
        del global_cengine_cache[context.job.chat_id]
        return
    elif context.job.name == MORNING_JOB.format(context.job.chat_id):
        cengine.drop_state(KEY_MORNING_QUESTIONNAIRE)
        conversation = create_morning_conversation()
    elif context.job.name == AFTERNOON_JOB.format(context.job.chat_id):
        cengine.drop_state(KEY_AFTERNOON_QUESTIONNAIRE)
        conversation = create_afternoon_conversation()
    elif context.job.name == EVENING_JOB.format(context.job.chat_id):
        cengine.copy_today_to_history()
        conversation = []
    elif context.job.name == WEEKLY_JOB.format(context.job.chat_id):
        history = cengine.get_state(HISTORY_KEY)
        data_generator = CumulatedDataGenerator(history)
        stats = await create_weekly_statistics(data_generator)
        charts = await create_weekly_charts(data_generator)
        conversation = create_weekly_conversation(stats, charts)
    elif context.job.name == MONTHLY_JOB.format(context.job.chat_id):
        history = cengine.get_state(HISTORY_KEY)
        data_generator = CumulatedDataGenerator(history)
        stats = await create_monthly_statistics(data_generator)
        charts = await create_monthly_charts(data_generator)
        conversation = create_monthly_conversation(stats, charts)
    else:
        return

    cengine.begin_new_conversation(conversation)
    bot = application.bot if application else passed_context.bot
    await send_next_messages(bot, cengine, context.job.chat_id)


async def create_weekly_charts(data_generator):
    try:
        chart_generator = ChartGenerator(data_generator)
        start_date = str((datetime.now() - timedelta(days=7)).date())
        end_date = str(datetime.now().date())
        cal_week = (datetime.now() - timedelta(days=7)).isocalendar()[1]
        line_chart_buffer = chart_generator.generate_line_chart(title=f'\nZusammenfassung KW {cal_week}\n',
            start_date=start_date, end_date=end_date)
        tasks_chart_buffer, mood_chart_buffer = chart_generator.generate_bar_charts(start_date=start_date, end_date=end_date)
        return [line_chart_buffer, tasks_chart_buffer, mood_chart_buffer]
    except Exception as e:
        print(e)
        return None


async def create_weekly_statistics(data_generator: CumulatedDataGenerator):
    try:
        start_date = str((datetime.now() - timedelta(days=7)).date())
        end_date = str(datetime.now().date())
        return data_generator.calculate_metadata(start_date, end_date)
    except Exception as e:
        print(e)
        return None


async def create_monthly_charts(data_generator: CumulatedDataGenerator):
    try:
        chart_generator = ChartGenerator(data_generator)
        current_date = datetime.now()
        _, num_days = calendar.monthrange(current_date.year, current_date.month)
        start_date = str(datetime(current_date.year, current_date.month, 1).date())
        end_date = str(datetime(current_date.year, current_date.month, num_days).date())
        locale.setlocale(locale.LC_TIME, "de_DE.utf8")
        month_name = current_date.strftime("%B")
        line_chart_buffer = chart_generator.generate_line_chart(title=f'\nZusammenfassung {month_name}\n',
            start_date=start_date, end_date=end_date, compact=True)
        tasks_chart_buffer, mood_chart_buffer = chart_generator.generate_bar_charts(start_date=start_date, end_date=end_date)
        return [line_chart_buffer, tasks_chart_buffer, mood_chart_buffer]
    except Exception as e:
        print(e)
        return None


async def create_monthly_statistics(data_generator: CumulatedDataGenerator):
    try:
        current_date = datetime.now()
        _, num_days = calendar.monthrange(current_date.year, current_date.month)
        start_date = str(datetime(current_date.year, current_date.month, 1).date())
        end_date = str(datetime(current_date.year, current_date.month, num_days).date())
        return data_generator.calculate_metadata(start_date, end_date)
    except Exception as e:
        print(e)
        return None


######################## PERSISTENCE ########################


def override_cengine_state_in_persistence(chat_id, state, pickle_file_path='conversation_bot.pkl'):
    try:
        with open(pickle_file_path, 'rb') as file:
            persistence_data = pickle.load(file)

        persistence_data.setdefault(KEY_USERDATA, {}).setdefault(chat_id, {})[KEY_STATE] = state

        with open(pickle_file_path, 'wb') as file:
            pickle.dump(persistence_data, file)

    except (FileNotFoundError, pickle.UnpicklingError, KeyError):
        pass


def get_cengine_state_from_persistence(chat_id, pickle_file_path='conversation_bot.pkl'):
    try:
        with open(pickle_file_path, 'rb') as file:
            conversations = pickle.load(file).get(KEY_USERDATA, {})
            return conversations.get(chat_id, {}).get(KEY_STATE)
    except (FileNotFoundError, pickle.UnpicklingError, KeyError):
        return None
