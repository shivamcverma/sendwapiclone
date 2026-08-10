from django.urls import path
from .views import dashboard, generate_qr, send_message, update_qr_status

app_name = 'messaging'

urlpatterns = [


    path(
        "generate-qr/",
        generate_qr,
        name="generate_qr"
    ),
    path(
    "update-qr-status/",
    update_qr_status,
    name="update_qr_status"
),
   path(
        "send-message/",
        send_message,
        name="send_message"
    ),
]