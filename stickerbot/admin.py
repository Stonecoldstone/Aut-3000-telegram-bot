from django.contrib import admin
from .models import Chat, Sticker, Intermediate

# Register your models here.

class MembershipInline(admin.StackedInline):
    model = Chat.stickers.through

class StickerAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]


class ChatAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]

admin.site.register(Chat, ChatAdmin)
admin.site.register(Sticker, StickerAdmin)
admin.site.register(Intermediate)