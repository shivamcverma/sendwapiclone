from django.urls import path
from .views import create_api_key, dashboard, generate_qr, regenerate_api_key, send_message, update_qr_status ,qr_connect, messages_page

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
    path(
        "api-key/",
        create_api_key,
        name="create_api_key"
    ),

    path(
        "api-key/regenerate/",
        regenerate_api_key,
        name="regenerate_api_key"
    ),
    path("qr-connect/", qr_connect, name="qr_connect"),
    path("messages/", messages_page, name="messages"),
]