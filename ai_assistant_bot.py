import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8787766144:AAGSvn5zSVotJluruT2iCNTzTlidfwr9jWk"
USDT_WALLET = "0x50E668eD4bb31F785404304E858205d0B93a4De3"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

logging.basicConfig(level=logging.INFO)

# Free trial messages
FREE_LIMIT = 5

# Store user data in memory
user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "messages": 0,
            "subscribed": False,
            "lang": "en"
        }
    return user_data[user_id]

PLANS = {
    "basic": {"name": "Basic", "price": 5, "messages": 200},
    "pro": {"name": "Pro", "price": 10, "messages": 1000},
    "unlimited": {"name": "Unlimited", "price": 20, "messages": 999999}
}

TEXTS = {
    "en": {
        "welcome": """🤖 *Welcome to AI Assistant Pro!*

I'm your personal AI assistant powered by advanced AI.

✨ *What I can do:*
• 💬 Answer any question
• 📝 Write texts, posts, essays
• 🌍 Translate to any language  
• 💡 Generate ideas & strategies
• 📊 Analyze and summarize
• 🎯 Help with business & marketing

🎁 *You get 5 FREE messages to try!*

Just send me any message to start! 👇""",
        "trial_left": "🎁 Free messages left: {}",
        "trial_over": """⚠️ *Your free trial is over!*

You've used all 5 free messages.

💎 *Choose a subscription plan to continue:*""",
        "plans": """💎 *Choose your plan:*

🥉 *Basic — $5/month*
• 200 messages per month
• All AI features

🥈 *Pro — $10/month*  
• 1,000 messages per month
• Priority responses

🥇 *Unlimited — $20/month*
• Unlimited messages
• Fastest responses
• VIP support""",
        "payment": """💳 *Payment Instructions*

Plan: *{plan}* — *${price}/month*

Send USDT to this address:
`{wallet}`

🌐 Network: ERC20 (Ethereum)

After payment, send me the transaction ID and I'll activate your subscription! ✅""",
        "thinking": "🤔 Thinking...",
        "error": "❌ Something went wrong. Please try again.",
        "subscribed": "✅ You have an active subscription!",
        "send_tx": "After sending USDT, send me your transaction ID here to activate subscription.",
        "activated": "🎉 Your subscription has been activated! Enjoy unlimited AI assistance!",
    },
    "ru": {
        "welcome": """🤖 *Добро пожаловать в AI Assistant Pro!*

Я ваш персональный ИИ-ассистент на базе передового ИИ.

✨ *Что я умею:*
• 💬 Отвечать на любые вопросы
• 📝 Писать тексты, посты, эссе
• 🌍 Переводить на любой язык
• 💡 Генерировать идеи и стратегии
• 📊 Анализировать и резюмировать
• 🎯 Помогать с бизнесом и маркетингом

🎁 *Вы получаете 5 БЕСПЛАТНЫХ сообщений для пробы!*

Просто отправьте мне любое сообщение! 👇""",
        "trial_left": "🎁 Бесплатных сообщений осталось: {}",
        "trial_over": """⚠️ *Бесплатный период закончился!*

Вы использовали все 5 бесплатных сообщений.

💎 *Выберите план подписки:*""",
        "plans": """💎 *Выберите план:*

🥉 *Basic — $5/месяц*
• 200 сообщений в месяц
• Все функции ИИ

🥈 *Pro — $10/месяц*
• 1,000 сообщений в месяц
• Приоритетные ответы

🥇 *Unlimited — $20/месяц*
• Безлимитные сообщения
• Самые быстрые ответы
• VIP поддержка""",
        "payment": """💳 *Инструкция по оплате*

План: *{plan}* — *${price}/месяц*

Отправьте USDT на этот адрес:
`{wallet}`

🌐 Сеть: ERC20 (Ethereum)

После оплаты отправьте мне ID транзакции и я активирую подписку! ✅""",
        "thinking": "🤔 Думаю...",
        "error": "❌ Что-то пошло не так. Попробуйте снова.",
        "subscribed": "✅ У вас активная подписка!",
        "send_tx": "После отправки USDT, пришлите мне ID транзакции для активации подписки.",
        "activated": "🎉 Ваша подписка активирована! Пользуйтесь ИИ без ограничений!",
    }
}

async def ask_claude(message: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "AI service is not configured yet. Please contact support."
    
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
    user = get_user(user_id)
    lang = user["lang"]
    t = TEXTS[lang]
    
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("💎 Subscribe", callback_data="plans"),
         InlineKeyboardButton("💬 Start Chat", callback_data="chat")]
    ]
    await update.message.reply_text(
        t["welcome"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    data = query.data

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user["lang"] = lang
        t = TEXTS[lang]
        keyboard = [
            [InlineKeyboardButton("💎 Subscribe", callback_data="plans"),
             InlineKeyboardButton("💬 Start Chat", callback_data="chat")]
        ]
        await query.message.reply_text(t["welcome"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "plans" or data == "subscribe":
        lang = user["lang"]
        t = TEXTS[lang]
        keyboard = [
            [InlineKeyboardButton("🥉 Basic — $5/mo", callback_data="pay_basic")],
            [InlineKeyboardButton("🥈 Pro — $10/mo", callback_data="pay_pro")],
            [InlineKeyboardButton("🥇 Unlimited — $20/mo", callback_data="pay_unlimited")]
        ]
        await query.message.reply_text(t["plans"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("pay_"):
        plan_key = data.split("_")[1]
        plan = PLANS[plan_key]
        lang = user["lang"]
        t = TEXTS[lang]
        text = t["payment"].format(
            plan=plan["name"],
            price=plan["price"],
            wallet=USDT_WALLET
        )
        keyboard = [[InlineKeyboardButton("✅ I've paid", callback_data=f"paid_{plan_key}")]]
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("paid_"):
        lang = user["lang"]
        t = TEXTS[lang]
        user["waiting_tx"] = data.split("_")[1]
        await query.message.reply_text(t["send_tx"])

    elif data == "chat":
        lang = user["lang"]
        t = TEXTS[lang]
        left = FREE_LIMIT - user["messages"]
        if user["subscribed"]:
            await query.message.reply_text("✅ Send me any message and I'll answer!")
        elif left > 0:
            await query.message.reply_text(f"{t['trial_left'].format(left)}\n\nSend me any message! 👇")
        else:
            keyboard = [[InlineKeyboardButton("💎 Subscribe Now", callback_data="plans")]]
            await query.message.reply_text(t["trial_over"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user["lang"]
    t = TEXTS[lang]
    text = update.message.text

    # Check if waiting for transaction ID
    if user.get("waiting_tx"):
        plan_key = user.pop("waiting_tx")
        plan = PLANS[plan_key]
        user["subscribed"] = True
        user["plan"] = plan_key
        await update.message.reply_text(t["activated"])
        return

    # Check limits
    if not user["subscribed"] and user["messages"] >= FREE_LIMIT:
        keyboard = [[InlineKeyboardButton("💎 Subscribe Now", callback_data="plans")]]
        await update.message.reply_text(t["trial_over"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Send thinking message
    thinking_msg = await update.message.reply_text(t["thinking"])

    try:
        response = await ask_claude(text)
        user["messages"] += 1
        
        # Add trial counter for free users
        extra = ""
        if not user["subscribed"]:
            left = FREE_LIMIT - user["messages"]
            if left > 0:
                extra = f"\n\n🎁 {t['trial_left'].format(left)}"
            else:
                extra = "\n\n⚠️ This was your last free message! Subscribe to continue."

        await thinking_msg.edit_text(response + extra)
        
        # Show subscribe button when trial ends
        if not user["subscribed"] and user["messages"] >= FREE_LIMIT:
            keyboard = [[InlineKeyboardButton("💎 Subscribe Now", callback_data="plans")]]
            await update.message.reply_text(
                t["trial_over"],
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        await thinking_msg.edit_text(t["error"])

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ AI Assistant Pro Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
