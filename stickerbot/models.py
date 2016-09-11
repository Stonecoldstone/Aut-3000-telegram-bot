from django.db import models


class Sticker(models.Model):
    sticker_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.sticker_id


class Chat(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    stickers = models.ManyToManyField(Sticker, through='Intermediate')
    probability = models.FloatField(default=0.04)
    binding_word = models.TextField(default='', blank=True, null=True)
    lang = models.CharField(max_length=100, default='english')

    def __str__(self):
        return self.name


class Intermediate(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)
    word = models.TextField(blank=True, default='', null=True)

    def __str__(self):
        return '{}: ({} {})'.format(self.chat.name, self.word, self.sticker.sticker_id)

