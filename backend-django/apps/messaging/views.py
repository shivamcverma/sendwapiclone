import json
import secrets
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import QRSession, APIKey


# =====================================================
# HELPER
# =====================================================

def clean_number(number):
    return "".join(
        char for char in str(number or "")
        if char.isdigit()
    )


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard(request):

    qr_sessions = QRSession.objects.filter(
        user=request.user
    ).order_by("-created_at")

    api_key_obj = APIKey.objects.filter(
        user=request.user
    ).first()

    return render(
        request,
        "user/dashboard.html",
        {
            "qr_sessions": qr_sessions,
            "api_key_obj": api_key_obj,
        }
    )

@login_required
def qr_connect(request):

    qr_sessions = QRSession.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "user/qrconnect.html",
        {
            "qr_sessions": qr_sessions,
        }
    )


def messages_page(request):
    return render(request, "user/message.html")
# =====================================================
# GENERATE QR
# =====================================================

@login_required
def generate_qr(request):


    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)


    phone_number = request.POST.get(
        "phone_number"
    )


    if not phone_number:

        return JsonResponse({
            "success": False,
            "message": "Phone number is required"
        }, status=400)


    clean_phone = clean_number(
        phone_number
    )


    if len(clean_phone) != 10:

        return JsonResponse({
            "success": False,
            "message": "Enter a valid 10 digit WhatsApp number"
        }, status=400)


    whatsapp_phone ="91" + clean_phone


    api_url = (
        f"{settings.QR_SERVICE_URL}"
        "/api/qr/start"
    )


    payload = {

        "userId":
            request.user.id,

        "phoneNumber":
            whatsapp_phone

    }

    print("========== GENERATE QR ==========")
    print("USER ID:", request.user.id)
    print("PHONE:", whatsapp_phone)
    print("QR SERVICE URL:", api_url)
    print("QR PAYLOAD:", payload)

    try:

        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )


        print(
            "QR SERVICE URL:",
            api_url
        )

        print(
            "QR STATUS:",
            response.status_code
        )

        print(
            "QR RESPONSE:",
            response.text
        )
        print("QR SERVICE STATUS:", response.status_code)
        print("QR SERVICE RESPONSE:", response.text)

        response.raise_for_status()


        data = response.json()


    except requests.RequestException as e:

        return JsonResponse({

            "success": False,

            "message":
                "QR service unavailable",

            "error":
                str(e),

            "url":
                api_url

        }, status=500)


    except ValueError as e:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid response from QR service",

            "error":
                str(e),

            "raw_response":
                response.text

        }, status=500)


    if not data.get("success", True):

        return JsonResponse({

            "success": False,

            "message":
                data.get(
                    "message",
                    "QR generation failed"
                )

        }, status=400)


    session_id = data.get(
        "sessionId"
    )


    qr_code = data.get(
        "qr"
    )


    if not session_id:

        return JsonResponse({

            "success": False,

            "message":
                "Session ID missing from API response"

        }, status=400)


    # =================================================
    # IMPORTANT
    #
    # User ke purane sessions ko inactive karo.
    # =================================================

    QRSession.objects.filter(
        user=request.user,
        connect=True
    ).update(
        connect=False
    )


    # =================================================
    # SAVE NEW SESSION
    # =================================================

    qr_session, created = (
        QRSession.objects.update_or_create(

            session_id=session_id,

            defaults={

                "user":
                    request.user,

                "phone_number":
                    clean_phone,

                "qr_code_url":
                    qr_code,

                "connect":
                    data.get(
                        "connected",
                        False
                    ),

            }
        )
    )


    return JsonResponse({

        "success":
            True,

        "id":
            qr_session.id,

        "userId":
            request.user.id,

        "phoneNumber":
            qr_session.phone_number,

        "sessionId":
            qr_session.session_id,

        "qr":
            qr_session.qr_code_url,

        "connected":
            qr_session.connect

    })


# =====================================================
# UPDATE QR STATUS
# =====================================================

@login_required
def update_qr_status(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "POST request required"

        }, status=405)


    session_id = request.POST.get(
        "session_id"
    )


    connected = (
        request.POST.get("connected")
        == "true"
    )


    if not session_id:

        return JsonResponse({

            "success": False,

            "message":
                "Session ID is required"

        }, status=400)


    try:

        qr_session = QRSession.objects.get(

            session_id=
                session_id,

            user=
                request.user

        )

    except QRSession.DoesNotExist:

        return JsonResponse({

            "success": False,

            "message":
                "QR session not found"

        }, status=404)


    # =================================================
    # If this session connected,
    # disable other connected sessions.
    # =================================================

    if connected:

        QRSession.objects.filter(
            user=request.user,
            connect=True
        ).exclude(
            id=qr_session.id
        ).update(
            connect=False
        )


    qr_session.connect = connected


    qr_session.save(
        update_fields=[
            "connect",
            "updated_at"
        ]
    )


    return JsonResponse({

        "success":
            True,

        "connected":
            qr_session.connect,

        "sessionId":
            qr_session.session_id

    })


# =====================================================
# API KEY GENERATION
# =====================================================

def generate_api_key():

    return (
        "wa_live_" +
        secrets.token_hex(24)
    )


# =====================================================
# CREATE API KEY
# =====================================================

@login_required
@require_POST
def create_api_key(request):

    api_key_obj, created = (
        APIKey.objects.get_or_create(

            user=request.user,

            defaults={

                "key":
                    generate_api_key(),

                "active":
                    True,

            }
        )
    )


    return JsonResponse({

        "success":
            True,

        "api_key":
            api_key_obj.key

    })


# =====================================================
# REGENERATE API KEY
# =====================================================

@login_required
@require_POST
def regenerate_api_key(request):

    api_key_obj, created = (
        APIKey.objects.get_or_create(

            user=request.user,

            defaults={

                "key":
                    generate_api_key(),

                "active":
                    True,

            }
        )
    )


    if not created:

        api_key_obj.key = (
            generate_api_key()
        )

        api_key_obj.active = True

        api_key_obj.save()


    return JsonResponse({

        "success":
            True,

        "api_key":
            api_key_obj.key

    })


# =====================================================
# SEND MESSAGE
# =====================================================

@csrf_exempt
def send_message(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "POST request required"

        }, status=405)


    # =================================================
    # READ REQUEST DATA
    # =================================================

    try:

        if (
            request.content_type ==
            "application/json"
        ):

            data = json.loads(
                request.body
            )

        else:

            data = request.POST.dict()


    except (
        json.JSONDecodeError,
        TypeError
    ):

        return JsonResponse({

            "success": False,

            "message":
                "Invalid JSON"

        }, status=400)


    api_key = data.get(
        "api_key"
    )

    sender = data.get(
        "sender"
    )

    number = data.get(
        "number"
    )

    message = data.get(
        "message"
    )

    footer = data.get(
        "footer",
        ""
    )


    # =================================================
    # VALIDATION
    # =================================================

    if not api_key:

        return JsonResponse({

            "success": False,

            "message":
                "API key is required"

        }, status=400)


    if not sender:

        return JsonResponse({

            "success": False,

            "message":
                "Sender number is required"

        }, status=400)


    if not number:

        return JsonResponse({

            "success": False,

            "message":
                "Receiver number is required"

        }, status=400)


    if not message:

        return JsonResponse({

            "success": False,

            "message":
                "Message is required"

        }, status=400)


    # =================================================
    # CLEAN NUMBERS
    # =================================================

    clean_sender = clean_number(
        sender
    )

    clean_number_value = clean_number(
        number
    )


    # =================================================
    # CHECK API KEY
    # =================================================

    try:

        api_key_obj = (
            APIKey.objects
            .select_related("user")
            .get(
                key=api_key,
                active=True
            )
        )

    except APIKey.DoesNotExist:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid API key"

        }, status=401)


    user = api_key_obj.user


    # =================================================
    # FIND CONNECTED WHATSAPP SESSION
    # =================================================

    qr_session = (
        QRSession.objects
        .filter(

            user=user,

            phone_number=
                clean_sender[-10:],

            connect=True

        )
        .order_by(
            "-updated_at",
            "-created_at"
        )
        .first()
    )


    if not qr_session:

        return JsonResponse({

            "success": False,

            "message":
                "Sender WhatsApp is not connected"

        }, status=400)


    # =================================================
    # DEBUG
    # =================================================

    print(
        "MESSAGE REQUEST:"
    )

    print(
        "User:",
        user.id
    )

    print(
        "Sender:",
        clean_sender
    )

    print(
        "DB SESSION:",
        qr_session.session_id
    )

    print(
        "DB PHONE:",
        qr_session.phone_number
    )

    print(
        "CONNECTED:",
        qr_session.connect
    )


    # =================================================
    # SEND TO NODE WHATSAPP SERVICE
    # =================================================

    whatsapp_api_url = (
        "https://sendwapiclone-2.onrender.com/api/whatsapp/send-message"
    )


    payload = {

        "sessionId":
            qr_session.session_id,

        "phoneNumber":
            clean_number_value,

        "message":
            message,

        "footer":
            footer or ""

    }


    print(
        "NODE PAYLOAD:",
        payload
    )


    try:

        response = requests.post(

            whatsapp_api_url,

            json=payload,

            timeout=30

        )


        print(
            "NODE STATUS:",
            response.status_code
        )

        print(
            "NODE RESPONSE:",
            response.text
        )


        response.raise_for_status()


        result = response.json()


    except requests.RequestException as e:

        return JsonResponse({

            "success": False,

            "message":
                "WhatsApp service unavailable",

            "error":
                str(e)

        }, status=500)


    except ValueError:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid response from WhatsApp service",

            "raw_response":
                response.text

        }, status=500)


    # =================================================
    # SUCCESS
    # =================================================

    return JsonResponse({

        "success":
            True,

        "message":
            "Message sent successfully",

        "sender":
            clean_sender,

        "number":
            clean_number_value,

        "sessionId":
            qr_session.session_id,

        "response":
            result

    })
@login_required
def get_connected_sessions(request):

    sessions = QRSession.objects.filter(
        user=request.user,
        connect=True
    ).values(
        "session_id",
        "phone_number"
    )

    return JsonResponse({
        "success": True,
        "sessions": list(sessions)
    })
