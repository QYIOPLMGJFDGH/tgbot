from telethon import TelegramClient, events, Button
import sqlite3

# अपने SQL डेटाबेस का URL यहाँ डालें
DATABASE_URL = "postgres://kfcdtwea:jxgqtvc1ji7lSMjAhUp0QbxrE8Ut0t7N@fanny.db.elephantsql.com/kfcdtwea"

# Telethon Client Configuration
API_ID = 16457832  # अपना API ID डालें
API_HASH = "3030874d0befdb5d05597deacc3e83ab"  # अपना API HASH डालें
BOT_TOKEN = "8052771146:AAFQ_P-n9zOYdQqgU8uNsRMOlPx_GXrUy2Y"  # अपना बॉट टोकन डालें

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# SQL Database Connection
conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
cursor = conn.cursor()

# वेलकम मैसेज और बटन टेबल बनाना
cursor.execute("""
CREATE TABLE IF NOT EXISTS welcome_messages (
    chat_id INTEGER PRIMARY KEY,
    message TEXT,
    buttons TEXT
)
""")
conn.commit()

# /setwelcome कमांड हैंडलर
@client.on(events.NewMessage(pattern='/setwelcome'))
async def set_welcome(event):
    chat_id = event.chat_id

    await event.respond("Please send your welcome message. You can use:\n\n{name} - User's Name\n{username} - Username\n{chatname} - Group Name")
    
    response = await client.wait_for(events.NewMessage(from_users=event.sender_id, chats=chat_id))
    welcome_text = response.text

    await event.respond("Do you want to add buttons? (yes/no)")
    response = await client.wait_for(events.NewMessage(from_users=event.sender_id, chats=chat_id))

    buttons = []
    if response.text.lower() == "yes":
        await event.respond("Please send your buttons in format:\nText - URL\nSend one button per message. Send 'done' when finished.")
        
        while True:
            btn_response = await client.wait_for(events.NewMessage(from_users=event.sender_id, chats=chat_id))
            if btn_response.text.lower() == "done":
                break
            try:
                text, url = btn_response.text.split(" - ", 1)
                buttons.append((text, url))
            except ValueError:
                await event.respond("Invalid format. Please use: Text - URL")

    # बटन डेटा को SQL में स्टोर करने के लिए फॉर्मेट करना
    button_data = "|".join(f"{text}~{url}" for text, url in buttons)

    cursor.execute("INSERT OR REPLACE INTO welcome_messages (chat_id, message, buttons) VALUES (?, ?, ?)", (chat_id, welcome_text, button_data))
    conn.commit()

    await event.respond("Welcome message and buttons set successfully!")

# New Member Join Handler
@client.on(events.ChatAction)
async def welcome_new_member(event):
    if event.user_joined or event.user_added:
        chat_id = event.chat_id
        user = await event.get_user()
        chat = await event.get_chat()

        # SQL से वेलकम मैसेज और बटन लाना
        cursor.execute("SELECT message, buttons FROM welcome_messages WHERE chat_id = ?", (chat_id,))
        data = cursor.fetchone()

        if data:
            message, button_data = data
            formatted_message = message.format(name=user.first_name, username=f"@{user.username}" if user.username else "N/A", chatname=chat.title)

            # बटन बनाने की प्रक्रिया
            buttons = []
            if button_data:
                for btn in button_data.split("|"):
                    text, url = btn.split("~", 1)
                    buttons.append([Button.url(text, url)])

            # वेलकम मैसेज भेजना
            await client.send_message(chat_id, formatted_message, buttons=buttons if buttons else None)

client.run_until_disconnected()
