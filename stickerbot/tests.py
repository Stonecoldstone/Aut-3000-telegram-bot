from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from .views import Bot
from unittest import TestCase as UnitTestCase
from .api import Update
import json
import time
from .models import Chat, Sticker, Intermediate
import string
from .languages import LANG
from pprint import pprint
from django.core.exceptions import ObjectDoesNotExist


class TestOverall(TestCase):
    fixtures = ['testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.url = reverse('stickerbot:bot')
        cls.ct = 'application/json'

    def setUp(self):
        cur_time = int(time.time())
        self.text_msg = {'message': {'chat': {'id': 1,
                                             'title': 'autismw',
                                             'type': 'supergroup'},
                                    'date': cur_time,
                                    'from': {'first_name': 'Stone',
                                             'id': 134152189,
                                             'last_name': 'Cold'},
                                    'message_id': 16,
                                    'text': 'hi'},
                        'update_id': 724981070}
        self.sticker_msg = {'message': {'chat': {'first_name': 'Stone',
                                                'id': 1,
                                                'last_name': 'Cold',
                                                'type': 'private'},
                                       'date': cur_time,
                                       'from': {'first_name': 'Stone',
                                                'id': 134152189,
                                                'last_name': 'Cold'},
                                       'message_id': 9905,
                                       'sticker': {'emoji': '😔',
                                                   'file_id': 'BQADAgADFwAD0lqIAW6NhqV3Oc1XAg',
                                                   'file_size': 24614,
                                                   'height': 416,
                                                   'thumb': {'file_id': 'AAQCABO2wlkqAATpfShxvr1lQi8TAAIC',
                                                             'file_size': 4764,
                                                             'height': 104,
                                                             'width': 128},
                                                   'width': 512}},
                           'update_id': 724981690}
        self.chat_id = 1

    def test_empty_response_if_update_is_not_msg(self):
        # test junk data and broken json
        data = [
            json.dumps({'I': {'Like': 'turtles'}}),
            'I like turtles'
        ]
        for d in data:
            resp = self.client.post(self.url, d, content_type=self.ct)
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(resp.json())

    def test_empty_resp_if_msg_is_old(self):
        data = self.text_msg
        data['message']['date'] -= 301
        boolean = time.time() - data['message']['date'] > 300
        self.assertTrue(boolean)
        resp = self.client.post(self.url, data, content_type=self.ct)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json())

    def test_chat_saved_to_db(self):
        chat = self.text_msg['message']['chat']
        chat_id = str(chat['id'])
        request = self.factory.post(self.url, json.dumps(self.text_msg),
                                    content_type=self.ct)
        Bot.as_view()(request)
        try:
            chat_inst = Chat.objects.get(chat_id=chat_id)
        except:
            self.fail('Chat row wasn\'t created')
        self.assertEqual(chat_inst.name, chat['title'])
        # test default settings:
        self.assertEqual(chat_inst.binding_word, '')

    def test_stickers_saved_to_right_chat(self):
        chats = {1: set(), 2: set()}
        iterator = zip(string.ascii_lowercase[:10], string.ascii_lowercase[5:15])
        for i, j in iterator:
            chats[1].add(i)
            chats[2].add(j)
        for chat, stickers in chats.items():
            self.sticker_msg['message']['chat']['id'] = chat
            for sticker in stickers:
                self.sticker_msg['message']['sticker']['file_id'] = sticker
                request = self.factory.post(self.url, json.dumps(self.sticker_msg),
                                            content_type=self.ct)
                Bot.as_view()(request)
        for chat, stickers in chats.items():
            query = Sticker.objects.filter(chat__chat_id=str(chat))\
                .values_list('sticker_id', flat=True)
            self.assertEqual(set(query), stickers)

    def test_random_choice_do_not_confuse_stickers(self):
        chats = {1: ['a', 'b', 'c'], 2: ['d', 'e', 'f']}
        for chat, stickers in chats.items():
            self.sticker_msg['message']['chat']['id'] = chat
            for sticker in stickers:
                self.sticker_msg['message']['sticker']['file_id'] = sticker
                request = self.factory.post(self.url, json.dumps(self.sticker_msg),
                                            content_type=self.ct)
                Bot.as_view()(request)
        self.text_msg['message']['text'] = '/pshh'
        chat_results = {1: [], 2: []}
        for chat, stickers in chats.items():
            self.text_msg['message']['chat']['id'] = chat
            for i in range(250):
                resp = self.client.post(self.url, json.dumps(self.text_msg), content_type=self.ct)
                stick_id = resp.json()['sticker']
                chat_results[chat].append(stick_id)
        for sticker in chats[1]:
            self.assertNotIn(sticker, chat_results[2])
        for sticker in chats[2]:
            self.assertNotIn(sticker, chat_results[1])

    def test_set_chance(self):
        request = self.factory.post(self.url, json.dumps(self.text_msg), content_type=self.ct)
        Bot.as_view()(request)
        #chat_id = self.text_msg['message']['chat']['id']
        chat = Chat.objects.get(chat_id=self.chat_id)
        # default = 0.04
        self.assertEqual(chat.probability, 0.04)
        msg = '/set_chance {}'
        values = [0.1, 1, 25, 35.402, 50]
        for v in values:
            self.text_msg['message']['text'] = msg.format(v)
            resp = self.client.post(self.url, json.dumps(self.text_msg),
                                    content_type=self.ct)
            chat.refresh_from_db()
            self.assertEqual(chat.probability, v / 100)
            message = LANG[chat.lang]['set_chance_success'].format(v)
            self.assertEqual(message, resp.json()['text'])

    def test_init_bind_success(self):
        data = self.text_msg
        #chat_id = str(data['message']['chat']['id'])
        # test that empty bind fails
        data['message']['text'] = '/bind'
        resp = self.client.post(self.url, json.dumps(data), content_type=self.ct)
        chat = Chat.objects.get(chat_id=self.chat_id)
        lang = LANG[chat.lang]
        msg = lang['bind_empty']
        self.assertEqual(resp.json()['text'], msg)
        self.assertFalse(chat.binding_word)
        # test with data
        data['message']['text'] = '/bind foo'
        resp = self.client.post(self.url, json.dumps(data), content_type=self.ct)
        chat.refresh_from_db()
        msg = LANG[chat.lang]['bind_init']
        self.assertEqual(resp.json()['text'], msg)
        self.assertEqual(chat.binding_word, 'foo')

    def test_response_when_stickers_not_exist(self):
        stickers = Sticker.objects.all().exists()
        self.assertFalse(stickers)
        self.text_msg['message']['text'] = '/pshh'
        resp = self.client.post(self.url, json.dumps(self.text_msg), content_type=self.ct)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json())

















