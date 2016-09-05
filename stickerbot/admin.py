from django.contrib import admin
from .models import Chat, Sticker, Intermediate

# Register your models here.

class MembershipInline(admin.StackedInline):
    model = Chat.stickers.through

class StickerAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]


class ChatAdmin(admin.ModelAdmin):
    #filter_horizontal = ('user_permissions', 'groups', 'ope')
    #list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')
    inlines = [MembershipInline]

admin.site.register(Chat, ChatAdmin)
admin.site.register(Sticker, StickerAdmin)
#admin.site.register(Intermediate)