from .models import Sticker, Chat, Intermediate
from django.conf import settings


def dump():
    with open(settings.STANDARD_STICKERS) as file:
        chat = Chat(chat_id='standard', name='Standard')
        chat.save()
        for line in file:
            stick_id = line.strip()
            if stick_id:
                stick = Sticker(sticker_id=stick_id)
                stick.save()
                inter = Intermediate(chat=chat, sticker=stick)
                inter.save()