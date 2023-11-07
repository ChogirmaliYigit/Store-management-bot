from django.contrib import admin
from .models import TelegramUser, Chats, Orders, Admin


admin.site.register(TelegramUser)
admin.site.register(Chats)
admin.site.register(Orders)
admin.site.register(Admin)
