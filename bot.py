import openai
import redis
import time
import json
from textblob import TextBlob
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 🔑 API Keys
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8052771146:AAFQ_P-n9zOYdQqgU8uNsRMOlPx_GXrUy2Y"

# 🔗 OpenAI API Setup
openai.api_key = OPENAI_API_KEY

# 🔥 Redis Setup for Context Memory
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 🎭 Personality Responses
PERSONALITIES = {
    "casual": "Tum ek dost ho jo mazak masti karta hai, halka phulka aur friendly tone mein baat karta hai.",
    "serious": "Tum ek samajhdar aur insightful insaan ho jo hamesha logical aur thoughtful jawab deta hai.",
    "sarcastic": "Tum thoda sarcastic ho aur har baat pe halka phulka taunt ya masti karte ho.",
    "flirty": "Tum thoda fun aur playful ho, thodi masti aur lighthearted tareeke se baat karte ho."
}

# 🧠 Function to Detect Message Tone
def detect_mood(message):
    blob = TextBlob(message)
    polarity = blob.sentiment.polarity  # -1 (negative) to +1 (positive)
    
    if "😂" in message or "🤣" in message or any(word in message.lower() for word in ["lol", "haha", "masti", "mazaak"]):
        return "casual"
    elif "😡" in message or "😭" in message or any(word in message.lower() for word in ["gussa", "dukhi", "sad", "depressed"]):
        return "serious"
    elif "😉" in message or "😘" in message or any(word in message.lower() for word in ["cute", "sweet", "jaan", "baby"]):
        return "flirty"
    elif polarity < -0.3:
        return "sarcastic"
    elif polarity > 0.3:
        return "casual"
    else:
        return "serious"

# ✨ Function to Generate Realistic Replies
def chat_with_gpt(user_id, user_message):
    # 🧠 Detect User Mood
    mood = detect_mood(user_message)
    
    # 🔥 Fetch Previous Chat History
    chat_history = redis_client.get(f"chat:{user_id}")
    
    if chat_history:
        chat_history = json.loads(chat_history)
    else:
        chat_history = [{"role": "system", "content": PERSONALITIES[mood]}]

    # 👤 Add User Message to Context
    chat_history.append({"role": "user", "content": user_message})

    # 🤖 Generate AI Response
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_history
    )
    
    bot_reply = response["choices"][0]["message"]["content"]

    # 💾 Store Updated Chat History
    chat_history.append({"role": "assistant", "content": bot_reply})
    redis_client.set(f"chat:{user_id}", json.dumps(chat_history))

    return bot_reply

# 🔄 Reset Chat Memory
def reset_chat(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    redis_client.delete(f"chat:{user_id}")
    update.message.reply_text("Maine purani baatein bhool gayi, ab naye tareeke se shuru kar sakte hain!")

# 💬 Handle Messages & Simulate Typing
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_message = update.message.text

    # ⏳ Typing Simulation
    update.message.reply_chat_action("typing")
    time.sleep(min(len(user_message) * 0.1, 3))  # Delay based on message length

    # 🔥 Generate AI Response
    bot_reply = chat_with_gpt(user_id, user_message)
    update.message.reply_text(bot_reply)

# 🏃‍♂️ Main Function to Run the Bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # 🔧 Commands
    dp.add_handler(CommandHandler("reset", reset_chat))

    # 💬 Messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # 🚀 Start Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
