from django.contrib import admin
from .models import TelegramUser, Chats, Orders


admin.site.register(TelegramUser)
admin.site.register(Chats)
admin.site.register(Orders)
