import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from secret import TG_API_KEY
from calc import calculate

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


start_buttons = [['Начать', 'Отказаться']]
start_markup = ReplyKeyboardMarkup(start_buttons, one_time_keyboard=True)

risk_buttons = [['Высокий 10%', 'Средний 7.5%'], ['Низкий 5%', 'Депозит под 1%']]
risk_markup = ReplyKeyboardMarkup(risk_buttons, one_time_keyboard=True)

go_buttons = [['Рассчитать']]
go_markup = ReplyKeyboardMarkup(go_buttons, one_time_keyboard=True)

finish_buttons = [
    ['Возраст начала', 'Возраст ухода с работы'],
    ['Начальные инвестиции', 'Ежегодные инвестиции'],
    ['Ежегодные траты на пенсии', 'Риск инвестиций'],
    ['Пересчитать'],
    ['Закончить']
]
finish_markup = ReplyKeyboardMarkup(finish_buttons, one_time_keyboard=True)


async def start(update: Update, context):
    if os.path.exists('sessions_log'):
        with open('sessions_log', 'r') as sessions:
            users_qty = len(sessions.readlines())
    else:
        users_qty = 0
    logger.info('Starting session for user %s: %s', users_qty, update.message.from_user)
    with open('sessions_log', 'a') as sessions:
        sessions.write(f'{str(users_qty)}: {str(update.message.from_user)}\n')
    await update.message.reply_text(
        'Этот бот создан совместными усилиями '
        '[Николая Сащеко](https://t.me/+eufDqPUVkj1kNGVi) и [Евгения Окулика](https://t.me/+l-5jHNJY2ClhNTIy)\n\n'
        'Привет\\. Давай посчитаем сколько тебе нужно на то, чтобы не работать и когда ты сможешь к этому прийти',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=start_markup
    )
    return 'choose'


async def start_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'С какого возраста начинаешь копить?'
    )
    context.user_data['category'] = 'age_start'
    return 'text'


async def bye(update: Update, context):
    await update.message.reply_text(
        'Ок\\. Если хочешь начать заново, введи команду /start\n\n'
        'Этот бот создан совместными усилиями '
        '[Евгения Окулика](https://t.me/+l-5jHNJY2ClhNTIy) и [Николая Сащеко](https://t.me/+eufDqPUVkj1kNGVi)',
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    logger.info('Stopping session on user %s', update.message.from_user)
    return ConversationHandler.END


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if 'upd' in context.user_data['category']:
        await apply_change(update, context)
    elif context.user_data['category'] == 'age_start':
        await update.message.reply_text(
            f'Отлично. Начинаем копить с {user_text}\n\n'
            'С какого возраста хочешь перестать работать?'
        )
        try:
            context.user_data['age_start'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s entered start age', update.message.from_user)
        context.user_data['category'] = 'age_finish'
        return 'text'
    elif context.user_data['category'] == 'age_finish':
        await update.message.reply_text(
            f"Отлично. Вот что мы имеем:\n"
            f"Начинаем копить с {context.user_data['age_start']}\n"
            f"Перестаем копить в {user_text}\n\n"
            'Какую сумму в USD можешь инвестировать сразу?'
        )
        try:
            context.user_data['age_finish'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s entered finish age', update.message.from_user)
        context.user_data['category'] = 'invest_start'
        return 'text'
    elif context.user_data['category'] == 'invest_start':
        await update.message.reply_text(
            f"Отлично. Вот что мы имеем:\n"
            f"Начинаем копить с {context.user_data['age_start']}\n"
            f"Перестаем копить в {context.user_data['age_finish']}\n"
            f"Сразу откладываем ${user_text}\n\n"
            'Сколько будешь откладывать в год?'
        )
        try:
            context.user_data['invest_start'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s entered invest start', update.message.from_user)
        context.user_data['category'] = 'annual_invest'
        return 'text'
    elif context.user_data['category'] == 'annual_invest':
        await update.message.reply_text(
            f"Отлично. Вот что мы имеем:\n"
            f"Начинаем копить с {context.user_data['age_start']}\n"
            f"Перестаем копить в {context.user_data['age_finish']}\n"
            f"Сразу откладываем ${context.user_data['invest_start']}\n"
            f"Каждый год откладываем ${user_text}\n\n"
            'Сколько ты тратишь в год сейчас? '
            'Исходим из того, что твои расходы не должны сильно измениться в старости, '
            'чтобы не чувствовать дискомфорта.'
        )
        try:
            context.user_data['annual_invest'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', context.user_data['annual_invest'], context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s entered annual invest', update.message.from_user)
        context.user_data['category'] = 'retire_expense'
        return 'text'
    elif context.user_data['category'] == 'retire_expense':
        await update.message.reply_text(
            f"Отлично. Вот что мы имеем:\n"
            f"Начинаем копить с {context.user_data['age_start']}\n"
            f"Перестаем копить в {context.user_data['age_finish']}\n"
            f"Сразу откладываем ${context.user_data['invest_start']}\n"
            f"Каждый год откладываем ${context.user_data['annual_invest']}\n"
            f"Ежегодные траты на пенсии: ${user_text}\n\n"
            'Выбери уровень риска твоих инвестиций',
            reply_markup=risk_markup
        )
        try:
            context.user_data['retire_expense'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s entered retired expenses', update.message.from_user)
        context.user_data['category'] = 'risk_level'
        return 'choose'
    elif context.user_data['category'] == 'risk_level':
        await update.message.reply_text(
            f"Отлично. Вот что мы имеем:\n"
            f"Начинаем копить с {context.user_data['age_start']}\n"
            f"Перестаем копить в {context.user_data['age_finish']}\n"
            f"Сразу откладываем ${context.user_data['invest_start']}\n"
            f"Каждый год откладываем ${context.user_data['annual_invest']}\n"
            f"Ежегодные траты на пенсии: ${context.user_data['retire_expense']}\n"
            f"Уровень риска: {user_text}",
            # reply_markup=go_markup
        )
        logger.info('%s entered risk level', update.message.from_user)
        context.user_data['risk_level'] = user_text
        await go(update, context)


async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_age = context.user_data['age_start']
    retire_age = context.user_data['age_finish']
    invest_start = context.user_data['invest_start']
    annual_invest = context.user_data['annual_invest']
    annual_retired_expenses = context.user_data['retire_expense']
    risk_level = context.user_data['risk_level']
    result = calculate(
        start_age, retire_age, invest_start, annual_invest, annual_retired_expenses, risk_level
    )
    result.insert(0, '<pre>')
    result.append('</pre>')
    reply = '\n'.join(result)
    try:
        await update.message.reply_html(reply)
    except BadRequest:
        await update.message.reply_html(
            'Данных слишком много - телеграм не может отобразить такое длинное сообщение\n\n'
            'Попробуйте изменить возраст начала и окончания и пересчитать.'
        )
        logger.exception(
            'Слишком большой результат. Возраст старта %s , возраст окончания %s',
            context.user_data['age_start'], context.user_data['age_finish']
        )
    logger.info('Data calculated successfully for user %s', update.message.from_user)
    await update.message.reply_text(
        'Подсчет выполнен на основании этих данных:\n'
        f"Начинаем копить с {context.user_data['age_start']}\n"
        f"Перестаем копить в {context.user_data['age_finish']}\n"
        f"Сразу откладываем ${context.user_data['invest_start']}\n"
        f"Каждый год откладываем ${context.user_data['annual_invest']}\n"
        f"Ежегодные траты на пенсии: ${context.user_data['retire_expense']}\n"
        f"Уровень риска: {context.user_data['risk_level']}\n\n"
        '*Теперь ты можешь изменить параметры и пересчитать или завершить этот диалог*',
        # parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=finish_markup
    )
    return 'choose'


async def change_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info('User %s decided to play with parameters', update.message.from_user)
    if update.message.text == 'Возраст начала':
        text = 'С какого возраста начинаешь копить?'
        context.user_data['category'] = 'age_start_upd'
    elif update.message.text == 'Возраст ухода с работы':
        text = 'С какого возраста хочешь перестать работать?'
        context.user_data['category'] = 'age_finish_upd'
    elif update.message.text == 'Начальные инвестиции':
        text = 'Какую сумму в USD можешь инвестировать сразу?'
        context.user_data['category'] = 'invest_start_upd'
    elif update.message.text == 'Ежегодные инвестиции':
        text = 'Сколько будешь откладывать в год?'
        context.user_data['category'] = 'annual_invest_upd'
    elif update.message.text == 'Ежегодные траты на пенсии':
        text = 'Сколько ты тратишь в год сейчас? Исходим из того, что твои расходы не должны сильно измениться в старости, чтобы не чувствовать дискомфорта.'
        context.user_data['category'] = 'retire_expense_upd'
    elif update.message.text == 'Риск инвестиций':
        text = 'Выбери уровень риска твоих инвестиций'
        await update.message.reply_text(
            text,
            reply_markup=risk_markup
        )
        context.user_data['category'] = 'risk_level_upd'
        return 'choose'
    else:
        text = ''

    await update.message.reply_text(
        text
    )
    return 'text'


async def apply_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if context.user_data['category'] == 'age_start_upd':
        try:
            context.user_data['age_start'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s updated start age', update.message.from_user)
    elif context.user_data['category'] == 'age_finish_upd':
        try:
            context.user_data['age_finish'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s updated finish age', update.message.from_user)
    elif context.user_data['category'] == 'invest_start_upd':
        try:
            context.user_data['invest_start'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s updated invest start', update.message.from_user)
    elif context.user_data['category'] == 'annual_invest_upd':
        try:
            context.user_data['annual_invest'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s updated annual invest', update.message.from_user)
    elif context.user_data['category'] == 'retire_expense_upd':
        try:
            context.user_data['retire_expense'] = int(user_text)
        except ValueError:
            logger.error('Somebody entered %s as %s', user_text, context.user_data['category'])
            await update.message.reply_text(
                f'А ты, видимо, тестер\n'
                'Можешь начать с начала /start'
            )
            context.user_data.clear()
            return ConversationHandler.END
        logger.info('%s updated retired expenses', update.message.from_user)
    elif context.user_data['category'] == 'risk_level_upd':
        context.user_data['risk_level'] = user_text
        logger.info('%s updated risk level', update.message.from_user)

    del context.user_data['category']
    await update.message.reply_text(
        'Сейчас данные такие:\n'
        f"Начинаем копить с {context.user_data['age_start']}\n"
        f"Перестаем копить в {context.user_data['age_finish']}\n"
        f"Сразу откладываем ${context.user_data['invest_start']}\n"
        f"Каждый год откладываем ${context.user_data['annual_invest']}\n"
        f"Ежегодные траты на пенсии: ${context.user_data['retire_expense']}\n"
        f"Уровень риска: {context.user_data['risk_level']}\n\n"
        '*Ты можешь изменить другие параметры и пересчитать или завершить этот диалог*',
        # parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=finish_markup
    )
    return 'choose'


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        'choose': [
            MessageHandler(filters.Regex('^Начать$'), start_calc),
            MessageHandler(filters.Regex('^(Рассчитать|Пересчитать)$'), go),
            MessageHandler(filters.Regex('^(Высокий 10%|Низкий 5%|Средний 7.5%|Депозит под 1%)$'), info),
            MessageHandler(
                filters.Regex(
                    '^(Возраст начала|Возраст ухода с работы|Начальные инвестиции|Ежегодные инвестиции|Ежегодные траты на пенсии|Риск инвестиций)$'
                ), change_params
            )
        ],
        'text': [
            MessageHandler(
                filters.Regex(
                    '^(Возраст начала|Возраст ухода с работы|Начальные инвестиции|Ежегодные инвестиции|Ежегодные траты на пенсии|Риск инвестиций)$'
                ), change_params
            ),
            MessageHandler(
                filters.TEXT & ~(
                        filters.COMMAND | filters.Regex("^(Отказаться|Закончить|Пересчитать)$")
                ), info
            ),
            MessageHandler(filters.Regex('^(Рассчитать|Пересчитать)$'), go)
        ],
        ConversationHandler.TIMEOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bye)]
    },
    fallbacks=[
        MessageHandler(filters.Regex('^(Отказаться|Закончить)$'), bye),
    ],
    conversation_timeout=900
)


application = Application.builder().token(TG_API_KEY).build()
application.add_handler(conv_handler)
application.run_polling(allowed_updates=Update.ALL_TYPES)
