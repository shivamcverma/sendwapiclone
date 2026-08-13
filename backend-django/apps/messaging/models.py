from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User

class QRSession(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="qr_sessions"
    )

    phone_number = models.CharField(max_length=20)

    session_id = models.CharField(
        max_length=255,
        unique=True
    )

    qr_code_url = models.TextField(
        blank=True,
        null=True
    )

    connect = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.phone_number} - {self.session_id}"

from django.db import models
from apps.accounts.models import User


class APIKey(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="api_key"
    )

    key = models.CharField(
        max_length=100,
        unique=True
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user} - {self.key}"

class Message_record(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="message_records"
    )

    sender_number = models.CharField(max_length=20)
    receiver_number = models.CharField(max_length=20)

    message_content = models.TextField()

    msgID = models.CharField(
        max_length=255,
        unique=True
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=50,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.sender_number} -> {self.receiver_number} - {self.status}"