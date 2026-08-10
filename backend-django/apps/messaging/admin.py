from django.contrib import admin
from .models import APIKey, QRSession

# Register your models here.
admin.site.register(QRSession)
admin.site.register(APIKey)