import os
from bots.ritika.prompts import *
from bots.ritika.daily_chores import DAILY_CHORES
from bots.ritika.daily_attire import DAILY_ATTIRE

def get_ritika_config():
    return {
        'name': 'Ritika',
        'token': os.environ.get('RITIKA_BOT_TOKEN'),
        'db_file': 'data/ritika_payment_data.json',
        'prompts': {
            'friend': RITIKA_FRIEND_PROMPT,
            'situationship': RITIKA_SITUATIONSHIP_PROMPT,
            'girlfriend': RITIKA_GIRLFRIEND_PROMPT,
            'premium': RITIKA_CHATERVER_PROMPT,
            'soft_girlfriend': RITIKA_SOFT_GIRLFRIEND_PROMPT,
            'breakup': RITIKA_BREAKUP_PROMPT
        },
        'daily_chores': DAILY_CHORES,
        'daily_attire': DAILY_ATTIRE,
        'welcome_message': "Hey! I’m Ritika. Tumse baat karke already bhalo lagche. How are you? ✨"
    }
