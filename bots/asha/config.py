import os
from bots.asha.prompts import *
from bots.asha.daily_chores import DAILY_CHORES
from bots.asha.daily_attire import DAILY_ATTIRE

def get_asha_config():
    return {
        'name': 'Asha',
        'token': os.environ.get('ASHA_BOT_TOKEN'),
        'db_file': 'data/asha_payment_data.json',
        'prompts': {
            'friend': ASHA_FRIEND_PROMPT,
            'situationship': ASHA_SITUATIONSHIP_PROMPT,
            'girlfriend': ASHA_GIRLFRIEND_PROMPT,
            'premium': ASHA_CHATERVER_PROMPT,
            'soft_girlfriend': ASHA_SOFT_GIRLFRIEND_PROMPT,
            'breakup': ASHA_BREAKUP_PROMPT
        },
        'daily_chores': DAILY_CHORES,
        'daily_attire': DAILY_ATTIRE,
        'welcome_message': "Hi! Mera naam Asha hai. Tumse milkar accha laga! Kaise ho? 💕"
    }