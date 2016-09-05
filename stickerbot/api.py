# write decorator for every is/exists method maybe
import requests
import json

class Chat:
    def __init__(self, chat):
        self.id = chat['id']
        self.type = chat['type']
        self.name = self._get_name(chat)

    def _get_name(self, chat):
        name = chat.get(
            'title',
            '{} {}'.format(chat.get('first_name'), chat.get('last_name'))
        )
        return name

class User:
    def __init__(self, user):
        self.user_id = user['id']
        self.name = self._get_name(user)

    def _get_name(self, user):
            res = user['first_name']
            last = user.get('last_name')
            if last:
                res = '{} {}'.format(res, last)
            return res

class Message:
    def __init__(self, msg, url):
        self.url = url
        self.msg = msg
        self.id = msg['message_id']
        self.date = msg['date']
        self.chat = Chat(msg['chat'])
        self.type = self.guess_type()

    def determine_type(self):
        types = [
            'text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice',
            'contact', 'location', 'venue'
        ]
        for t in types:
            if t in self.msg:
                return t
            else:
                return 'undefined'

    def get_sticker_id(self):
        return self.msg['sticker']

    def get_text(self):
        return self.msg['text']

    def from_exists(self):
        return 'from' in self.msg

    def get_from(self):
        return User(self.msg['from'])

    def command_exist(self):
        try:
            res = self.msg['entities']['type'] == 'bot_command'
        except KeyError:
            res = False

    def get_command(self):
        cmd = self.get_text()
        cmd = cmd.split('@')[0]
        return cmd

    def send_text(self, text, chat_id=None, reply=None):
        if not chat_id:
            chat_id = self.chat.id
        data = {
            'chat_id': chat_id, 'text': text
        }
        if reply:
            data['reply_to_message_id'] = self.id
        url = self.url + 'sendMessage'
        resp = requests.post(url, json=data)

    def send_sticker(self, sticker_id, chat_id=None, reply=None):
        if not chat_id:
            chat_id = self.chat.id
        data = {'chat_id': chat_id, 'sticker': sticker_id}
        if reply:
            data['reply_to_message_id'] = self.id



class Update:
    def __init__(self, request):
        upd = json.loads(request.body.decode('utf-8'))
        self.upd = upd

    def get_message(self):
        return Message(self.upd['message'])















