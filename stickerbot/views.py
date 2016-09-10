import time
import random
from operator import itemgetter
from django.http import JsonResponse
from django.views.generic.base import View
from .models import Chat, Sticker, Intermediate
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from .api import Update
from pprint import pprint
from .languages import LANG


class Bot(View):
    http_method_names = ['post']

    def post(self, request):
        upd = Update(request)
        # with open('data_for_tests.txt', 'a') as file:
        #     pprint(upd.upd, stream=file)

        # bot processes only message objects:
        # ignores any junk data, edited messages etc.
        if not upd.message_exists():
            return JsonResponse({})
        self.msg = upd.get_message()
        chat_id = self.msg.chat.id
        try:
            self.chat = Chat.objects.get(chat_id=chat_id)
        except ObjectDoesNotExist:
            chat_name = self.msg.chat.name
            self.chat = Chat(chat_id=chat_id, name=chat_name)
            self.chat.save()
        # do not reply to message if it's old but save any posted stickers
        if (time.time() - self.msg.date) > 300:
            if self.msg.type == 'sticker':
                self.save_sticker()
            return JsonResponse({})
        self.lang = LANG[self.chat.lang]
        self.rand_gen = random.SystemRandom()
        if self.chat.binding_word:
            if self.msg.type == 'sticker':
                sticker_obj = self.save_sticker()
                data = self.create_word_binding(sticker_obj)
            else:
                data = self.msg.text_response(self.lang['not_sticker'],
                                              reply=True)
            self.chat.binding_word = ''
            self.chat.save()
            return JsonResponse(data)
        methods_map = {
            '/pshh': self.send_random, '/set_chance': self.set_chance,
            '/bind': self.initialize_bind, '/unbind': self.unbind,
            '/stats': self.stats,

        }
        command, args = False, ()
        if self.msg.is_command():
            command, args = self.msg.get_command()
        method = methods_map.get(command, self.handle_not_cmd)
        data = method(*args)
        return JsonResponse(data)

    # formatting could be added
    def stats(self, *args):
        count = self.chat.stickers.distinct().count()
        binds = self.chat.intermediate_set.exclude(word='').values_list('word', flat=True)
        binds = ', '.join(sorted(binds))
        text = self.lang['stats'].format(count, binds)
        return self.msg.text_response(text, markdown='HTML')

    def set_chance(self, *args):
        low, high = 0, 50
        try:
            str_num = args[0]
            num = float(str_num)
        except(IndexError, ValueError):
            text = self.lang['set_chance_junk'].format(low, high)
        else:
            if low <= num <= high:
                prob = num / 100
                self.chat.probability = prob
                self.chat.save()
                text = self.lang['set_chance_success'].format(str_num)
            else:
                text = self.lang['set_chance_limit'].format(low, high)
        return self.msg.text_response(text)

    def handle_not_cmd(self, *args):
        rand_bool = True
        data = {}
        mtype = self.msg.type
        if mtype == 'left_chat_member' and \
                        self.msg.get_left_member_username() == settings.BOT_USERNAME:
            self.chat.delete()
            data = {}
            rand_bool = False
        elif mtype == 'text':
            text = self.msg.get_text().lower()
            words = self.chat.intermediate_set.exclude(word='')
            words = words.values_list('word', 'sticker__sticker_id')
            matches = []
            for word, sticker in words:
                ind = text.find(word)
                if ind != -1:
                    matches.append((word, sticker, ind))
            if matches:
                matches.sort(key=lambda x: len(x[0]), reverse=True)
                matches.sort(key=itemgetter(2))
                stick_id = matches[0][1]
                data = self.msg.get_sticker_resp(stick_id, reply=settings.REPLY)
                rand_bool = False
        if rand_bool:
            if self.rand_gen.random() <= self.chat.probability:
                data = self.send_random()
        if mtype == 'sticker':
            self.save_sticker()
        return data

    def send_random(self, *args):
        sticker_id = self.get_random_sticker()
        if sticker_id:
            data = self.msg.get_sticker_resp(sticker_id, reply=settings.REPLY)
        else:
            data = {}
        return data

    def save_sticker(self):
        sticker_id = self.msg.get_sticker_id()
        try:
            sticker = Sticker.objects.get(sticker_id=sticker_id)
        except ObjectDoesNotExist:
            sticker = Sticker.objects.create(sticker_id=sticker_id)
        in_chat = self.chat.stickers.filter(sticker_id=sticker_id).exists()
        if not in_chat:
            Intermediate.objects.create(chat=self.chat, sticker=sticker)
        return sticker

    def create_word_binding(self, sticker):
        binding = self.chat.binding_word.lower()
        query = Intermediate.objects.filter(chat=self.chat, word=binding)
        if query.exists():
            query.update(sticker=sticker)
        else:
            Intermediate.objects.create(chat=self.chat, sticker=sticker, word=binding)
        text = self.lang['bind_success']
        return self.msg.text_response(text)

    def get_random_sticker(self):
        count = self.chat.stickers.distinct().count()
        if count <= 25:
            query_args = ('standard', self.chat.chat_id)
        else:
            query_args = (self.chat.chat_id,)
        stickers = Sticker.objects.filter(chat__chat_id__in=query_args).distinct()
        stickers = stickers.values_list('sticker_id', flat=True)
        try:
            rand_sticker_id = random.choice(stickers)
        except IndexError:
            rand_sticker_id = ''
        return rand_sticker_id

    def initialize_bind(self, *args):
        if args:
            word = ' '.join(args)
            self.chat.binding_word = word
            self.chat.save()
            text = self.lang['bind_init']
        else:
            text = self.lang['bind_empty']
        return self.msg.text_response(text)

    def unbind(self, *args):
        if args:
            word = ' '.join(args)
            res = Intermediate.objects.filter(chat=self.chat, word=word).delete()
            text = self.lang['unbind_success']
            if not res[0]:
                text = self.lang['unbind_junk'].format(word)
        else:
            text = self.lang['unbind_empty']
        return self.msg.text_response(text)