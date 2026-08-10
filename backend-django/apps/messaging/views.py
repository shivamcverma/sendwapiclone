import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import QRSession


@login_required
def dashboard(request):

    qr_sessions = QRSession.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "user/dashboard.html",
        {
            "qr_sessions": qr_sessions,
        }
    )


@login_required
def generate_qr(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)

    phone_number = request.POST.get("phone_number")

    if not phone_number:
        return JsonResponse({
            "success": False,
            "message": "Phone number is required"
        }, status=400)

    api_url = f"{settings.QR_SERVICE_URL}/api/qr/start"

    payload = {
        "userId": request.user.id,
        "phoneNumber": "91" + phone_number
    }

    try:

        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        return JsonResponse({
            "success": False,
            "message": "QR service unavailable",
            "error": str(e)
        }, status=500)

    # API response check
    if not data.get("success"):

        return JsonResponse({
            "success": False,
            "message": data.get(
                "message",
                "QR generation failed"
            )
        }, status=400)

    session_id = data.get("sessionId")
    qr_code = data.get("qr")

    if not session_id:

        return JsonResponse({
            "success": False,
            "message": "Session ID missing from API response"
        }, status=400)

    # Save / update QR session
    qr_session, created = QRSession.objects.update_or_create(

        session_id=session_id,

        defaults={
            "user": request.user,
            "phone_number": phone_number,
            "qr_code_url": qr_code,
            "connect": data.get(
                "connected",
                False
            ),
        }
    )

    return JsonResponse({

        "success": True,

        "id": qr_session.id,

        "userId": request.user.id,

        "phoneNumber":
            qr_session.phone_number,

        "sessionId":
            qr_session.session_id,

        "qr":
            qr_session.qr_code_url,

        "connected":
            qr_session.connect,
    })

@login_required
def update_qr_status(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)

    session_id = request.POST.get("session_id")
    connected = request.POST.get("connected") == "true"

    if not session_id:
        return JsonResponse({
            "success": False,
            "message": "Session ID is required"
        }, status=400)

    try:

        qr_session = QRSession.objects.get(
            session_id=session_id,
            user=request.user
        )

    except QRSession.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "QR session not found"
        }, status=404)

    qr_session.connect = connected
    qr_session.save(update_fields=[
        "connect",
        "updated_at"
    ])

    return JsonResponse({
        "success": True,
        "connected": qr_session.connect
    })

import requests

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.messaging.models import QRSession, APIKey


@csrf_exempt
def send_message(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)


    try:
        data = request.json
    except Exception:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON"
        }, status=400)


    api_key = data.get("api_key")
    sender = data.get("sender")
    number = data.get("number")
    message = data.get("message")
    footer = data.get("footer")


    # -----------------------------
    # VALIDATION
    # -----------------------------

    if not api_key:
        return JsonResponse({
            "success": False,
            "message": "API key is required"
        }, status=400)


    if not sender:
        return JsonResponse({
            "success": False,
            "message": "Sender number is required"
        }, status=400)


    if not number:
        return JsonResponse({
            "success": False,
            "message": "Receiver number is required"
        }, status=400)

    if not message:
        return JsonResponse({
            "success": False,
            "message": "Message is required"
        }, status=400)


    # -----------------------------
    # CHECK API KEY
    # -----------------------------

    try:

        api_key_obj = APIKey.objects.select_related(
            "user"
        ).get(
            key=api_key,
            active=True
        )

    except APIKey.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Invalid API key"
        }, status=401)


    user = api_key_obj.user


    # -----------------------------
    # CHECK WHATSAPP CONNECTION
    # -----------------------------

    qr_session = QRSession.objects.filter(
        user=user,
        phone_number=sender[-10:],
        connect=True
    ).first()


    if not qr_session:

        return JsonResponse({
            "success": False,
            "message": "Sender WhatsApp is not connected"
        }, status=400)


    # -----------------------------
    # SEND TO WHATSAPP SERVICE
    # -----------------------------

    whatsapp_api_url = (
        "https://sendwapiclone-2.onrender.com/api/whatsapp/send-message"
    )


  
    payload = {
        "sessionId": qr_session.session_id,
        "phoneNumber": number,
        "message": message,
        "footer": footer or ""
    }

    try:

        response = requests.post(
            whatsapp_api_url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

    except requests.RequestException as e:

        return JsonResponse({
            "success": False,
            "message": "WhatsApp service unavailable",
            "error": str(e)
        }, status=500)


    return JsonResponse({
        "success": True,
        "message": "Message sent successfully",
        "sender": sender,
        "to": to,
        "response": result
    })