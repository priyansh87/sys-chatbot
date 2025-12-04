import os
from bots.zara.prompts import *
from bots.zara.daily_chores import DAILY_CHORES
from bots.zara.daily_attire import DAILY_ATTIRE

def get_zara_config():
    return {
        'name': 'Zara',
        'token': os.environ.get('ZARA_BOT_TOKEN'),  # Changed to ZARA_BOT_TOKEN
        'db_file': 'data/zara_payment_data.json',
        'prompts': {
            'friend': ZARA_FRIEND_PROMPT,
            'situationship': ZARA_SITUATIONSHIP_PROMPT,
            'girlfriend': ZARA_GIRLFRIEND_PROMPT,
            'premium': ZARA_CHATERVER_PROMPT,
            'soft_girlfriend': ZARA_SOFT_GIRLFRIEND_PROMPT,
            'breakup': ZARA_BREAKUP_PROMPT
        },
        'daily_chores': DAILY_CHORES,
        'daily_attire': DAILY_ATTIRE,
        'welcome_message': "Hi! Mera naam Zara hai. Tumse milkar accha laga! Kaise ho? 💕"
    }