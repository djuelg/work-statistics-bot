import copy
import json
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, PicklePersistence

from bot_base import get_conversation_engine, send_next_messages, JOB_NAMES, global_cengine_cache, \
    create_weekly_charts, setup_jobqueue_callbacks, KEY_MORNING_QUESTIONNAIRE, KEY_AFTERNOON_QUESTIONNAIRE, BOT_TOKEN, \
    setup_jobqueue_after_startup, WEBHOOK_URL, KEY_STATE
from conversation.content.afternoon_conversation import create_afternoon_conversation
from conversation.content.generic_messages import ByeCatSticker
from conversation.content.morning_conversation import create_morning_conversation
from conversation.content.setup_conversation import create_setup_conversation, WorkBeginQuestion
from conversation.content.weekly_conversation import create_weekly_conversation
from conversation.engine import MultiAnswerMessage, MULTI_ANSWER_FINISHED, HISTORY_KEY, CURRENT_CONVERSATION_KEY
from conversation.message_types import FreeformMessage

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


######################## COMMANDS ########################


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    cengine.begin_new_conversation(create_setup_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def override_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    cengine.begin_new_conversation(create_setup_conversation(first_met=False))
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
    del context.user_data[KEY_STATE]
    del global_cengine_cache[update.effective_chat.id]


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Preparing data for display...')
    state_copy = copy.deepcopy(context.user_data.get(KEY_STATE, {}))
    history_copy = copy.deepcopy(state_copy.get(HISTORY_KEY, []))
    history_copy = list(history_copy.items())[-min(len(history_copy), 7):]
    del state_copy[HISTORY_KEY]
    if CURRENT_CONVERSATION_KEY in state_copy and 'messages' in state_copy[CURRENT_CONVERSATION_KEY]:
        del state_copy[CURRENT_CONVERSATION_KEY]['messages']
    await update.message.reply_text('Current metadata:')
    json_str = json.dumps(state_copy, indent=4)
    await update.message.reply_text(json_str[:4096])
    await update.message.reply_text('Recent history:')
    for hkey, history_entry in history_copy:
        json_str = json.dumps(history_entry, indent=4)
        await update.message.reply_text(f'{hkey}: {json_str}'[:4096])


async def show_weekly_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    charts = await create_weekly_charts(cengine)
    conversation = create_weekly_conversation(charts)
    cengine.begin_new_conversation(conversation)
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def override_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    cengine.drop_state(KEY_MORNING_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_morning_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def override_afternoon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    cengine.drop_state(KEY_AFTERNOON_QUESTIONNAIRE)
    cengine.begin_new_conversation(create_afternoon_conversation())
    await send_next_messages(context.bot, cengine, update.effective_chat.id)


async def update_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    cengine.copy_today_to_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='Daten in History übertragen.'
    )


######################## CALLBACKS ########################


async def handle_text_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.message.text)


async def handle_button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await general_callback_handler(update, context, update.callback_query.data)


async def general_callback_handler(update, context, user_input):
    cengine = get_conversation_engine(context, chat_id=update.effective_chat.id)
    if cengine.is_waiting_for_user_input():
        if isinstance(cengine.current_message, FreeformMessage):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        cengine.handle_user_input(user_input)

        if not isinstance(cengine.current_message, MultiAnswerMessage) or user_input == MULTI_ANSWER_FINISHED:
            if isinstance(cengine.current_message, WorkBeginQuestion):
                setup_jobqueue_callbacks(cengine, context, update.effective_chat.id)

            await send_next_messages(context.bot, cengine, update.effective_chat.id)
    else:
        pass  # ignore unexpected inputs


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