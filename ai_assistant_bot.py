import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters, ContextTypes
 
TOKEN = "8787766144:AAGSvn5zSVotJluruT2iCNTzTlidfwr9jWk"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
 
logging.basicConfig(level=logging.INFO)
 
FREE_LIMIT = 5
user_data = {}
 
PLANS = {
    "basic": {"name": "Basic", "stars": 250, "messages": 200},
    "pro": {"name": "Pro", "stars": 500, "messages": 1000},
    "unlimited": {"name": "Unlimited", "stars": 1000, "messages": 999999}
}
 
TEXTS = {
    "en": {
        "welcome": """🤖 *Welcome to AI Assistant Pro!*
 
Your personal AI assistant powered by advanced AI.
 
✨ *What I can do:*
• 💬 Answer any question
• 📝 Write texts, posts, essays
• 🌍 Translate to any language
• 💡 Generate ideas & strategies
• 📊 Analyze and summarize
 
🎁 *You get 5 FREE messages to try!*
 
Just send me any message! 👇""",
        "trial_left": "🎁 Free messages left: {}",
        "trial_over": "⚠️ *Free trial is over!*\n\nChoose a subscription plan:",
        "plans": """💎 *Choose your plan:*
 
🥉 *Basic — 250 ⭐*
• 200 messages/month
 
🥈 *Pro — 500 ⭐*
• 1,000 messages/month
 
🥇 *Unlimited — 1000 ⭐*
• Unlimited messages""",
        "thinking": "🤔 Thinking...",
        "error": "❌ Something went wrong. Try again.",
        "activated": "🎉 Subscription activated! Enjoy AI assistance!",
        "paying": "💫 Processing payment...",
    },
    "ru": {
        "welcome": """🤖 *Добро пожаловать в AI Assistant Pro!*
 
Ваш персональный ИИ-ассистент.
 
✨ *Что я умею:*
• 💬 Отвечать на любые вопросы
• 📝 Писать тексты и посты
• 🌍 Переводить на любой язык
• 💡 Генерировать идеи
• 📊 Анализировать информацию
 
🎁 *5 БЕСПЛАТНЫХ сообщений для пробы!*
 
Просто напишите мне! 👇""",
        "trial_left": "🎁 Бесплатных сообщений: {}",
        "trial_over": "⚠️ *Бесплатный период закончился!*\n\nВыберите план подписки:",
        "plans": """💎 *Выберите план:*
 
🥉 *Basic — 250 ⭐*
• 200 сообщений/месяц
 
🥈 *Pro — 500 ⭐*
• 1,000 сообщений/месяц
 
🥇 *Unlimited — 1000 ⭐*
• Безлимитные сообщения""",
        "thinking": "🤔 Думаю...",
        "error": "❌ Что-то пошло не так. Попробуйте снова.",
        "activated": "🎉 Подписка активирована! Пользуйтесь ИИ без ограничений!",
        "paying": "💫 Обрабатываю платёж...",
    }
}
 
user_langs = {}
user_states = {}
 
def get_lang(user_id):
    return user_langs.get(user_id, 'en')
 
def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"messages": 0, "subscribed": False}
    return user_data[user_id]
 
async def ask_claude(message: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "⚠️ AI service not configured yet. Please contact support."
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": message}]
            },
            timeout=30
        )
        data = response.json()
        return data["content"][0]["text"]
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("💎 Subscribe with ⭐", callback_data="plans"),
         InlineKeyboardButton("💬 Start Chat", callback_data="chat")]
    ]
    lang = get_lang(user_id)
    await update.message.reply_text(
        TEXTS[lang]["welcome"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
 
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
 
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user_langs[user_id] = lang
        keyboard = [
            [InlineKeyboardButton("💎 Subscribe with ⭐", callback_data="plans"),
             InlineKeyboardButton("💬 Start Chat", callback_data="chat")]
        ]
        await query.message.reply_text(
            TEXTS[lang]["welcome"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
 
    elif data == "plans":
        lang = get_lang(user_id)
        keyboard = [
            [InlineKeyboardButton("🥉 Basic — 250 ⭐", callback_data="buy_basic")],
            [InlineKeyboardButton("🥈 Pro — 500 ⭐", callback_data="buy_pro")],
            [InlineKeyboardButton("🥇 Unlimited — 1000 ⭐", callback_data="buy_unlimited")]
        ]
        await query.message.reply_text(
            TEXTS[lang]["plans"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
 
    elif data.startswith("buy_"):
        plan_key = data.split("_")[1]
        plan = PLANS[plan_key]
        lang = get_lang(user_id)
        # Send Stars invoice
        await context.bot.send_invoice(
            chat_id=user_id,
            title=f"AI Assistant Pro — {plan['name']}",
            description=f"{plan['messages']} messages per month",
            payload=f"sub_{plan_key}",
            currency="XTR",
            prices=[LabeledPrice(label=plan["name"], amount=plan["stars"])]
        )
 
    elif data == "chat":
        lang = get_lang(user_id)
        user = get_user(user_id)
        left = FREE_LIMIT - user["messages"]
        if user["subscribed"]:
            await query.message.reply_text("✅ Send me any message!")
        elif left > 0:
            await query.message.reply_text(f"{TEXTS[lang]['trial_left'].format(left)}\n\nSend me any message! 👇")
        else:
            keyboard = [[InlineKeyboardButton("💎 Subscribe with ⭐", callback_data="plans")]]
            await query.message.reply_text(
                TEXTS[lang]["trial_over"],
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
 
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)
 
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    user = get_user(user_id)
    user["subscribed"] = True
    await update.message.reply_text(TEXTS[lang]["activated"])
 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    user = get_user(user_id)
    text = update.message.text
 
    if not user["subscribed"] and user["messages"] >= FREE_LIMIT:
        keyboard = [[InlineKeyboardButton("💎 Subscribe with ⭐", callback_data="plans")]]
        await update.message.reply_text(
            TEXTS[lang]["trial_over"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
 
    thinking = await update.message.reply_text(TEXTS[lang]["thinking"])
    try:
        response = await ask_claude(text)
        user["messages"] += 1
        extra = ""
        if not user["subscribed"]:
            left = FREE_LIMIT - user["messages"]
            if left > 0:
                extra = f"\n\n🎁 {TEXTS[lang]['trial_left'].format(left)}"
            else:
                extra = "\n\n⚠️ Last free message! Subscribe to continue ⭐"
        await thinking.edit_text(response + extra)
 
        if not user["subscribed"] and user["messages"] >= FREE_LIMIT:
            keyboard = [[InlineKeyboardButton("💎 Subscribe with ⭐", callback_data="plans")]]
            await update.message.reply_text(
                TEXTS[lang]["trial_over"],
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        await thinking.edit_text(TEXTS[lang]["error"])
 
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ AI Assistant Pro with Stars payments running!")
    app.run_polling()
 
if __name__ == "__main__":
    main()
