import subprocess
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .models import Sticker, Chat, Intermediate



def dump(filename):
    with open(filename) as file:
        try:
            chat = Chat.objects.get(chat_id='standard')
            proceed = input('Standard chat already exists. Stickers will be saved to it. Continue?(y/n)')
            if proceed.lower().startswith('n'):
                return 0
        except ObjectDoesNotExist:
            chat = Chat(chat_id='standard', name='Standard')
            chat.save()
        sticks_saved = 0
        for line in file:
            stick_id = line.strip()
            if stick_id:
                query = chat.stickers.filter(sticker_id=stick_id)
                if query.exists():
                    print('Sticker with id=\'{}\' already exists.'.format(stick_id))
                else:
                    result = Sticker.objects.get_or_create(sticker_id=stick_id)
                    Intermediate.objects.create(chat=chat, sticker=result[0])
                    sticks_saved += 1
        return sticks_saved


def webhook(url, switch=True):
    if switch:
        data = 'url={}'.format(url)
    else:
        data = 'url='
    url = 'https://api.telegram.org/bot{}/setWebhook'.format(settings.BOT_TICKET)
    args = ['curl', '-F', data, url]
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = popen.communicate()
    return res[0]