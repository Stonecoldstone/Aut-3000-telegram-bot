from django.db import models

# Create your models here.


class Sticker(models.Model):
    sticker_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.sticker_id


class Chat(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    stickers = models.ManyToManyField(Sticker, through='Intermediate')
    burst = models.IntegerField(default=5)
    probability = models.FloatField(default=0.07)

    def __str__(self):
        return self.name


class Intermediate(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)
    word = models.CharField(max_length=100, blank=True, null=True, default='')

    def __str__(self):
        return '{}: {}'.format(self.chat.name, self.sticker.sticker_id)

