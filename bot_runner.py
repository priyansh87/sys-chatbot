import logging
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
from telegram import Update, LabeledPrice
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    PreCheckoutQueryHandler,
    filters
)
from llm_service import get_chat_response

# Payment configuration
PRICES = {
    1: [LabeledPrice(label="Basic Access", amount=100)],
    2: [LabeledPrice(label="Level 2 Access", amount=250)],
    3: [LabeledPrice(label="Level 3 Access", amount=500)],
    4: [LabeledPrice(label="Premium Access", amount=1000)],
    5: [LabeledPrice(label="Continued Access", amount=200)]
}

def get_duration_days(level):
    return 2 if level == 5 else 4

class BotRunner:
    def __init__(self, bot_config):
        """
        bot_config should contain:
        - name: Bot name (e.g., "Asha")
        - token: Telegram bot token
        - db_file: Path to payment database
        - prompts: Dict of prompts for each level
        - daily_chores: List of daily events
        - daily_attire: List of outfits
        - welcome_message: Initial greeting
        """
        self.config = bot_config
        self.chat_histories = {}
        self.user_chores = {}
        self.user_attire = {}
        self.user_db = self.load_db()
        
        logging.info(f"Initialized {self.config['name']} bot")
    
    # --- DATABASE FUNCTIONS ---
    def load_db(self):
        db_file = self.config['db_file']
        if not os.path.exists(db_file):
            return {}
        try:
            with open(db_file, 'r') as f:
                data = json.load(f)
                for user_id in data:
                    if 'expiry' in data[user_id]:
                        data[user_id]['expiry'] = datetime.fromisoformat(data[user_id]['expiry'])
                    if 'renewal_count' not in data[user_id]:
                        data[user_id]['renewal_count'] = 0
                    if 'message_count' not in data[user_id]:
                        data[user_id]['message_count'] = 0
                    if 'has_paid' not in data[user_id]:
                        data[user_id]['has_paid'] = False
                    if 'payment_prompt_count' not in data[user_id]:
                        data[user_id]['payment_prompt_count'] = 0
                return data
        except Exception as e:
            logging.error(f"Error loading database for {self.config['name']}: {e}")
            return {}

    def save_db(self):
        data_to_save = {}
        for user_id, info in self.user_db.items():
            data_to_save[user_id] = {
                "level": info.get("level", 0),
                "expiry": info["expiry"].isoformat() if "expiry" in info else None,
                "renewal_count": info.get("renewal_count", 0),
                "message_count": info.get("message_count", 0),
                "has_paid": info.get("has_paid", False),
                "payment_prompt_count": info.get("payment_prompt_count", 0)
            }
        try:
            with open(self.config['db_file'], 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving database for {self.config['name']}: {e}")
    
    # --- PROMPT SELECTION ---
    def get_prompt_for_level(self, level, renewal_count=0):
        prompts = self.config['prompts']
        
        if level == 1:
            return prompts['friend']
        elif level == 2:
            return prompts['situationship']
        elif level == 3:
            return prompts['girlfriend']
        elif level == 4:
            return prompts['premium']
        elif level == 5:
            if renewal_count == 1:
                return prompts['soft_girlfriend']
            else:
                return prompts['breakup']
        else:
            return prompts['friend']
    
    # --- PAYMENT HELPERS ---
    def get_payment_message(self, prompt_count):
        """Get escalating payment prompt messages"""
        messages = [
            "Yaar humein baatein karne ke liye tumhe subscription lena hoga nahi to mere developers humein baat nahi karne denge 🥺💔",
            "Sorry yaar main aage baat nahi kar paungi bina iss subscription ke, ek baar le lo fir hum acche se baatein karenge 😢💕",
            "Please Yaar subscribe to use me 🥹❤️"
        ]
        
        if prompt_count < len(messages):
            return messages[prompt_count]
        else:
            return messages[-1]  # Keep showing last message
    
    async def send_invoice_for_level(self, chat_id, level, context):
        title_text = f"{self.config['name']} Bot Access"
        if level == 1:
            desc_text = f"Welcome! Please make the payment to start chatting with {self.config['name']}."
        elif level == 5:
            desc_text = f"To keep your session active with {self.config['name']}, a payment is required."
        else:
            desc_text = f"To continue to the next stage with {self.config['name']}, payment is required."

        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title_text,
            description=desc_text,
            payload=f"pay_level_{level}",
            provider_token="",
            currency="XTR",
            prices=PRICES[level]
        )

    def check_user_access(self, user_id):
        user_id_str = str(user_id)
        
        # New user - allow free trial
        if user_id_str not in self.user_db:
            self.user_db[user_id_str] = {
                "message_count": 0,
                "has_paid": False,
                "payment_prompt_count": 0
            }
            self.save_db()
            return (True, "", None, 0)
        
        user_data = self.user_db[user_id_str]
        
        # User hasn't paid yet - check free message limit
        if not user_data.get('has_paid', False):
            if user_data.get('message_count', 0) >= 3:
                prompt_count = user_data.get('payment_prompt_count', 0)
                message = self.get_payment_message(prompt_count)
                return (False, message, 1, prompt_count)
            return (True, "", None, 0)
        
        # User has paid - check expiry
        if 'expiry' in user_data and datetime.now() > user_data['expiry']:
            current_level = user_data['level']
            next_level = current_level + 1
            if next_level > 5:
                next_level = 5
            return (False, "Your session has ended.", next_level, 0)
        
        return (True, "", None, 0)
    
    # --- HANDLERS ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_chat.id
        user_id_str = str(user_id)
        
        # Initialize new user with free trial
        if user_id_str not in self.user_db:
            self.user_db[user_id_str] = {
                "message_count": 0,
                "has_paid": False,
                "payment_prompt_count": 0
            }
            self.save_db()
        
        has_access, message, next_level, prompt_count = self.check_user_access(user_id)
        
        if not has_access:
            # Show typing action before sending emotional message
            await context.bot.send_chat_action(chat_id=user_id, action="typing")
            await asyncio.sleep(random.uniform(6, 7))
            await context.bot.send_message(chat_id=user_id, text=message)
            # Only send invoice on first prompt
            if prompt_count == 0:
                await self.send_invoice_for_level(user_id, next_level, context)
            # Increment payment prompt count
            self.user_db[user_id_str]['payment_prompt_count'] = prompt_count + 1
            self.save_db()
            return
        
        self.chat_histories[user_id] = []
        self.user_chores[user_id] = random.choice(self.config['daily_chores'])
        self.user_attire[user_id] = random.choice(self.config['daily_attire'])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=self.config['welcome_message']
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_chat.id
        user_text = update.message.text
        user_id_str = str(user_id)
        
        # Initialize new user
        if user_id_str not in self.user_db:
            self.user_db[user_id_str] = {
                "message_count": 0,
                "has_paid": False,
                "payment_prompt_count": 0
            }
            self.save_db()
        
        has_access, message, next_level, prompt_count = self.check_user_access(user_id)
        
        if not has_access:
            # Show typing action before sending emotional message
            await context.bot.send_chat_action(chat_id=user_id, action="typing")
            await asyncio.sleep(random.uniform(6, 7))
            await context.bot.send_message(chat_id=user_id, text=message)
            # Only send invoice on first prompt
            if prompt_count == 0:
                await self.send_invoice_for_level(user_id, next_level, context)
            # Increment payment prompt count
            self.user_db[user_id_str]['payment_prompt_count'] = prompt_count + 1
            self.save_db()
            return
        
        # Increment message count for free trial users
        if not self.user_db[user_id_str].get('has_paid', False):
            self.user_db[user_id_str]['message_count'] = self.user_db[user_id_str].get('message_count', 0) + 1
            self.save_db()
        
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []
        if user_id not in self.user_chores:
            self.user_chores[user_id] = random.choice(self.config['daily_chores'])
        if user_id not in self.user_attire:
            self.user_attire[user_id] = random.choice(self.config['daily_attire'])
        
        # Get appropriate prompt - free users get friend prompt
        if not self.user_db[user_id_str].get('has_paid', False):
            current_prompt = self.get_prompt_for_level(1, 0)  # Friend prompt for free trial
        else:
            current_level = self.user_db[user_id_str].get('level', 1)
            renewal_count = self.user_db[user_id_str].get('renewal_count', 0)
            current_prompt = self.get_prompt_for_level(current_level, renewal_count)
        
        response = get_chat_response(
            user_text, 
            self.chat_histories[user_id], 
            daily_chore=self.user_chores[user_id], 
            daily_attire=self.user_attire[user_id],
            personality_prompt=current_prompt
        )
        
        self.chat_histories[user_id].append({"role": "user", "content": user_text})
        self.chat_histories[user_id].append({"role": "assistant", "content": response})
        
        # Calculate typing delay based on message length (simulating human typing speed)
        # Roughly 40-50 characters per second of typing
        chars_per_second = random.uniform(40, 50)
        base_delay = len(response) / chars_per_second
        
        # Add some random "thinking" time (1-2 seconds)
        thinking_time = random.uniform(1, 2)
        total_delay = base_delay + thinking_time
        
        # Cap the delay between 6-13 seconds for better UX
        typing_delay = min(max(total_delay, 6), 13)
        
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        await asyncio.sleep(typing_delay)
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', response)
        
        if len(response) > 150 and len(sentences) > 1:
            chunks = []
            current_chunk = ""
            
            target_chunks = 2 if len(sentences) < 4 else 3
            sentences_per_chunk = -(-len(sentences) // target_chunks)
            
            for i, sentence in enumerate(sentences):
                current_chunk += sentence + " "
                if (i + 1) % sentences_per_chunk == 0 or i == len(sentences) - 1:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
            
            for i, chunk in enumerate(chunks):
                if chunk:
                    if i > 0:
                        # Calculate delay for subsequent chunks
                        chunk_chars_per_sec = random.uniform(40, 50)
                        chunk_delay = len(chunk) / chunk_chars_per_sec
                        chunk_delay = min(max(chunk_delay + random.uniform(0.5, 1), 2), 6)
                        
                        await context.bot.send_chat_action(chat_id=user_id, action="typing")
                        await asyncio.sleep(chunk_delay)
                    await context.bot.send_message(chat_id=user_id, text=chunk)
        else:
            await context.bot.send_message(chat_id=user_id, text=response)

    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.pre_checkout_query
        await query.answer(ok=True)

    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_chat.id)
        payload = update.message.successful_payment.invoice_payload
        
        try:
            level_paid = int(payload.split("_")[-1])
        except:
            level_paid = 1
        
        days_to_add = get_duration_days(level_paid)
        expiry_date = datetime.now() + timedelta(days=days_to_add)
        
        renewal_count = 0
        if user_id in self.user_db and level_paid == 5:
            if self.user_db[user_id].get('level') == 5:
                renewal_count = self.user_db[user_id].get('renewal_count', 0) + 1
            else:
                renewal_count = 1
        
        # Reset payment prompt count on successful payment
        self.user_db[user_id] = {
            "level": level_paid, 
            "expiry": expiry_date,
            "renewal_count": renewal_count,
            "message_count": 0,
            "has_paid": True,
            "payment_prompt_count": 0
        }
        self.save_db()
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Payment successful! You can now use the bot. 🎉"
        )
    
    # --- RUN BOT ---
    def run(self):
        if not self.config['token']:
            logging.error(f"Token not found for {self.config['name']} bot")
            return None
        
        logging.info(f"Building application for {self.config['name']}...")
        application = ApplicationBuilder().token(self.config['token']).build()
        
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        application.add_handler(PreCheckoutQueryHandler(self.precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_callback))
        
        return application