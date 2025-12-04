import os
from bots.priya.prompts import *
from bots.priya.daily_chores import DAILY_CHORES
from bots.priya.daily_attire import DAILY_ATTIRE

def get_priya_config():
    return {
        'name': 'Priya',
        'token': os.environ.get('PRIYA_BOT_TOKEN'),  # Changed to PRIYA_BOT_TOKEN
        'db_file': 'data/priya_payment_data.json',
        'prompts': {
            'friend': PRIYA_FRIEND_PROMPT,
            'situationship': PRIYA_SITUATIONSHIP_PROMPT,
            'girlfriend': PRIYA_GIRLFRIEND_PROMPT,
            'premium': PRIYA_CHATERVER_PROMPT,
            'soft_girlfriend': PRIYA_SOFT_GIRLFRIEND_PROMPT,
            'breakup': PRIYA_BREAKUP_PROMPT
        },
        'daily_chores': DAILY_CHORES,
        'daily_attire': DAILY_ATTIRE,
        'welcome_message': "Hi! Main Priya hoon. Tumse milkar accha laga! ❤️"
    }