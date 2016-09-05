from django.http import HttpResponse
from django.views.generic.base import View
import random
from .models import Chat, Sticker, Intermediate
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.conf import settings
from itertools import chain
import json


class Bot(View):
    http_method_names = ['post']

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        self.msg = data.get('message')
        if not self.msg:
            return HttpResponse('')
        self.url = 'https://api.telegram.org/bot{}/'.format(settings.BOT_TICKET)
        self.rand_gen = random.SystemRandom()
        #########
        chat = self.msg['chat']
        chat_id = str(chat['id'])
        chat_name = chat.get('first_name', chat.get('title'))
        try:
            self.chat = Chat.objects.get(chat_id=chat_id)
        except ObjectDoesNotExist:
            self.chat = Chat(chat_id=chat_id, name=chat_name)
            self.chat.save()
        reply = self.msg['message_id']
        methods_map = {
            '/burst': (self.burst, ()), '/pshh': (self.send_sticker, (reply,)),
        }
        command = self.return_command()
        method, args = methods_map.get(command, ('', ''))
        if method:
            method(*args)
        else:
            if self.rand_gen.random() <= self.chat.probability:
                self.send_sticker(reply)
            self.posted_sticker()
        return HttpResponse('')

    def send_sticker(self, reply):
        sticker_id = self.get_random()
        data = {
            'chat_id': self.chat.chat_id, 'sticker': sticker_id,
            'reply_to_message_id': reply
        }
        # if reply:
        #     data['reply_to_message_id'] = reply
        url = self.url + 'sendSticker'
        print(self.url)
        #headers = {'content-type': 'application/json'}
        resp = requests.post(url, json=data)
        print(resp.status_code)

    def posted_sticker(self):
        sticker = self.msg.get('sticker')
        if sticker:
            new_sticker_id = sticker['file_id']
            try:
                sticker = Sticker.objects.get(sticker_id=new_sticker_id)
                in_chat = self.chat.stickers.filter(sticker_id=sticker.id).exists()
            except ObjectDoesNotExist:
                sticker = Sticker.objects.create(sticker_id=new_sticker_id)
                in_chat = False
            if not in_chat:
                intermediate = Intermediate(chat=self.chat, sticker=sticker)
                intermediate.save()

    # change this
    def return_command(self):
        ent = self.msg.get('entities')
        command = False
        if ent:
            ent_type = ent[0]['type']
            if ent_type == 'bot_command':
                command = self.msg['text']
                command = command.lower()
                command = command.split('@')[0]
        return command

    def burst(self):
        exclude = []
        num = self.chat.burst
        url = self.url + 'sendSticker'
        for i in range(num):
            sticker_id = self.get_random(exclude=exclude)
            data = {'chat_id': self.chat.chat_id, 'sticker': sticker_id}
            requests.post(url, data=data)
            exclude.append(sticker_id)

    def get_random(self, exclude=None):
        count = self.chat.stickers.count()
        stnd_stickers = iter(())
        if count <= 25:
            stnd_stickers = Sticker.objects.filter(chat__chat_id='standard')
        if exclude:
            stnd_stickers = stnd_stickers.exclude(sticker_id__in=exclude)
            stickers = self.chat.stickers.exclude(sticker_id__in=exclude)
        else:
            stickers = self.chat.stickers
        stick_list = list(chain(stickers.iterator(), stnd_stickers.iterator()))
        rand_sticker = random.choice(stick_list)
        sticker_id = rand_sticker.sticker_id
        return sticker_id

#random example
# class PaintingManager(models.Manager):
#     def random(self):
#         count = self.aggregate(count=Count('id'))['count']
#         random_index = randint(0, count - 1)
#         return self.all()[random_index]


