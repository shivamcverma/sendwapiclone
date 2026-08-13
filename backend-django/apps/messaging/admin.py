from django.contrib import admin
from .models import APIKey, Message_record, QRSession

# Register your models here.
admin.site.register(QRSession)
admin.site.register(APIKey)
admin.site.register(Message_record)