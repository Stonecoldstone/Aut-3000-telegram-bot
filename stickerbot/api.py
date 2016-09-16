# write decorator for every is/exists method maybe
import json
from json.decoder import JSONDecodeError


class Chat:
    def __init__(self, chat):
        self.id = str(chat['id'])
        self.type = chat['type']
        self.name = self._get_name(chat)

    def _get_name(self, chat):
        name = chat.get(
            'title',
            '{} {}'.format(chat.get('first_name'), chat.get('last_name', ''))
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
    def __init__(self, msg):
        self.msg = msg
        self.id = msg['message_id']
        self.date = msg['date']
        self.chat = Chat(msg['chat'])
        self.type = self.determine_type()

    def determine_type(self):
        types = [
            'text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice',
            'contact', 'location', 'venue', 'left_chat_member', 'new_chat_member'
        ]
        for t in types:
            if t in self.msg:
                return t
        return 'undefined'

    def get_sticker_id(self):
        return self.msg['sticker']['file_id']

    def get_new_member_username(self):
        return self.msg['new_chat_member']['username']

    def get_left_member_username(self):
        return self.msg['left_chat_member']['username']

    def get_text(self):
        return self.msg['text']

    def from_exists(self):
        return 'from' in self.msg

    def get_from(self):
        return User(self.msg['from'])

    def is_command(self):
        if self.type == 'text' and self.get_text().startswith('/'):
            return True
        else:
            return False

    def get_command(self):
        text = self.get_text().lower()
        text = text.split(' ')
        cmd = text[0]
        cmd = cmd.split('@')[0]
        args = text[1:]
        return cmd, args

    def text_response(self, text, chat_id=None, reply=False,
                      markdown=None, reply_markup=None):
        if not chat_id:
            chat_id = self.chat.id
        data = {'method': 'sendMessage', 'chat_id': chat_id, 'text': text}
        if reply:
            data['reply_to_message_id'] = self.id
        if markdown:
            data['parse_mode'] = markdown
        if reply_markup:
            data['reply_markup'] = reply_markup
        return data

    def get_sticker_resp(self, sticker_id, chat_id=None, reply=True):
        if not chat_id:
            chat_id = self.chat.id
        data = {'method': 'sendSticker', 'chat_id': chat_id, 'sticker': sticker_id}
        if reply:
            data['reply_to_message_id'] = self.id
        return data


class Update:
    def __init__(self, request):
        try:
            upd = json.loads(request.body.decode('utf-8'))
        except JSONDecodeError:
            upd = {}
        self.upd = upd
        self.type = self.determine_type()

    def determine_type(self):
        types = ['message', 'callback_query']
        for t in types:
            if t in self.upd:
                return t
        return 'undefined'

    #
    # def message_exists(self):
    #     return 'message' in self.upd

    def get_message(self):
        return Message(self.upd['message'])

    def get_callback_query(self):
        return CallbackQuery(self.upd['callback_query'])


class CallbackQuery:
    def __init__(self, query):
        self.query = query
        self.user = User(query['from'])
        self.data = query['data']
        self.id = query['id']

    def is_message(self):
        return 'message' in self.query

    def get_message(self):
        return Message(self.query['message'])

    def change_inline_msg(self, text, markdown=None, reply_markup=None):
        message = self.get_message()
        data = {
            'method': 'editMessageText', 'text': text,
            'chat_id': message.chat.id,
            'message_id': message.id
            #'chat_id': chat_id,
            #'inline_message_id': self.id,
        }
        if markdown:
            data['parse_mode'] = markdown
        if reply_markup:
            data['reply_markup'] = reply_markup
        return data





