from django.db import models


class TelegramUser(models.Model):
    full_name = models.CharField(max_length=400)
    username = models.CharField(max_length=500, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "users"


class Orders(models.Model):
    area = models.CharField(max_length=100)
    client_name = models.CharField(max_length=200)
    client_phone_number = models.CharField(max_length=100)
    client_products = models.TextField()
    client_products_images = models.CharField(max_length=150, null=True, blank=True)
    client_products_wrapping_type = models.CharField(max_length=250, null=True, blank=True)
    client_wrapped_products_images = models.CharField(max_length=150, null=True, blank=True)
    client_products_price = models.CharField(max_length=400)
    client_products_payment_status = models.CharField(max_length=100, null=True, blank=True)
    client_social_network = models.CharField(max_length=150)
    employee = models.CharField(max_length=100)
    delivery_date = models.CharField(max_length=200)
    location = models.TextField(null=True, blank=True)
    delivery_type = models.CharField(max_length=300, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    is_sent = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.client_name

    class Meta:
        db_table = "orders"


class Chats(models.Model):
    CHANNEL = "channel"
    TASHKENT_GROUP = "tashkent_group"
    REGIONS_GROUP = "regions_group"

    CHAT_TYPES = (
        (CHANNEL, "Kanal"),
        (TASHKENT_GROUP, "Toshkent uchun guruh"),
        (REGIONS_GROUP, "Viloyatlar uchun guruh"),
    )

    chat_id = models.BigIntegerField()
    type = models.CharField(max_length=100, choices=CHAT_TYPES)

    def __str__(self):
        return f"{self.chat_id}"

    class Meta:
        db_table = "chats"
