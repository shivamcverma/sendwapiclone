import json
import secrets
from time import timezone
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import QRSession, APIKey ,Message_record
from apps.superadmin.views import subscription
from apps.superadmin.models import UserSubscription

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
    sent_messages = Message_record.objects.filter(
        user=request.user,
        status="sent"
    ).count()
    total_msg = Message_record.objects.filter(
        user=request.user
    ).count()
    
    return render(
        request,
        "user/dashboard.html",
        {
            "qr_sessions": qr_sessions,
            "api_key_obj": api_key_obj,
            "sent_messages": sent_messages,
            "total_msg": total_msg
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


@login_required
def messages(request):

    records = (
        Message_record.objects
        .filter(user=request.user)
        .order_by("-sent_at")
    )

    message_list = []

    for record in records:

        message_list.append({
            "id": record.id,
            "sender": record.sender_number,
            "receiver": record.receiver_number,
            "message": record.message_content,
            "messageId": record.msgID,
            "status": record.status,
            "sentAt": record.sent_at,
        })

    return render(
        request,
        "user/message.html",
        {
            "messages": message_list
        }
    )

# =====================================================
# GENERATE QR
# =====================================================

@login_required
def generate_qr(request):

    print("========== CURRENT DJANGO USER ==========")
    print("USER:", request.user)
    print("USER ID:", request.user.id)
    print("EMAIL:", request.user.email)
    print("ROLE:", request.user.role)
    print("AUTHENTICATED:", request.user.is_authenticated)

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

    clean_phone = clean_number(phone_number)

    if len(clean_phone) != 10:
        return JsonResponse({
            "success": False,
            "message": "Enter a valid 10 digit WhatsApp number"
        }, status=400)

    whatsapp_phone = "91" + clean_phone

    print("========================================")
    print("GENERATE QR")
    print("USER ID:", request.user.id)
    print("PHONE:", whatsapp_phone)

    # =========================================================
    # STEP 1
    # EXISTING DJANGO SESSION CHECK
    # =========================================================

    existing_session = QRSession.objects.filter(
        user=request.user
    ).order_by("-updated_at").first()

    if existing_session:

        print("========================================")
        print("EXISTING DJANGO SESSION FOUND")
        print("SESSION ID:", existing_session.session_id)
        print("PHONE:", existing_session.phone_number)
        print("CONNECTED:", existing_session.connect)
        print("========================================")

        # -----------------------------------------------------
        # Agar same phone hai to SAME session reuse karo
        # -----------------------------------------------------

        if existing_session.phone_number == clean_phone:

            api_url = (
                f"{settings.QR_SERVICE_URL}"
                "/api/qr/start"
            )

            payload = {
                "userId": request.user.id,
                "phoneNumber": whatsapp_phone,
                "sessionId": existing_session.session_id
            }

            print("REUSING EXISTING SESSION")
            print("SESSION ID:", existing_session.session_id)
            print("PAYLOAD:", payload)

        else:

            # -------------------------------------------------
            # Phone number change hua hai.
            # Is case mein Node ko new session allow karenge.
            # -------------------------------------------------

            print("PHONE NUMBER CHANGED")
            print(
                "OLD PHONE:",
                existing_session.phone_number
            )
            print(
                "NEW PHONE:",
                clean_phone
            )

            api_url = (
                f"{settings.QR_SERVICE_URL}"
                "/api/qr/start"
            )

            payload = {
                "userId": request.user.id,
                "phoneNumber": whatsapp_phone
            }

    else:

        # =====================================================
        # STEP 2
        # USER KA KOI SESSION NAHI HAI
        # =====================================================

        print("NO EXISTING DJANGO SESSION")

        api_url = (
            f"{settings.QR_SERVICE_URL}"
            "/api/qr/start"
        )

        payload = {
            "userId": request.user.id,
            "phoneNumber": whatsapp_phone
        }

    print("========================================")
    print("QR SERVICE URL:", api_url)
    print("QR PAYLOAD:", payload)
    print("========================================")

    # =========================================================
    # STEP 3
    # CALL NODE
    # =========================================================

    try:

        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )

        print("QR SERVICE STATUS:", response.status_code)
        print("QR SERVICE RESPONSE:", response.text)

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        print("QR SERVICE ERROR:", e)

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

    # =========================================================
    # STEP 4
    # NODE RESPONSE CHECK
    # =========================================================

    if not data.get("success", True):

        return JsonResponse({

            "success": False,

            "message":
                data.get(
                    "message",
                    "QR generation failed"
                )

        }, status=400)

    session_id = data.get("sessionId")

    qr_code = data.get("qr")

    qr_image = data.get("qrImage")

    if not session_id:

        return JsonResponse({

            "success": False,

            "message":
                "Session ID missing from API response"

        }, status=400)

    # =========================================================
    # STEP 5
    # IMPORTANT:
    #
    # Same user ke old ACTIVE sessions inactive karo.
    #
    # Lekin current session ko destroy/delete mat karo.
    # =========================================================

    QRSession.objects.filter(
        user=request.user,
        connect=True
    ).exclude(
        session_id=session_id
    ).update(
        connect=False
    )

    # =========================================================
    # STEP 6
    # SAVE / UPDATE SAME SESSION
    # =========================================================

    qr_session, created = QRSession.objects.update_or_create(

        session_id=session_id,

        defaults={

            "user":
                request.user,

            "phone_number":
                clean_phone,

            "qr_code_url":
                qr_code or qr_image,

            "connect":
                data.get(
                    "connected",
                    False
                ),

        }
    )

    print("========================================")
    print("QR SESSION SAVED")
    print("CREATED:", created)
    print("DB ID:", qr_session.id)
    print("SESSION ID:", qr_session.session_id)
    print("CONNECTED:", qr_session.connect)
    print("========================================")

    # =========================================================
    # RESPONSE
    # =========================================================

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

        "qrImage":
            qr_image,

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

        if not connected:
            qr_session.qr_code_url = ""

        qr_session.save(
            update_fields=[
                "connect",
                "qr_code_url",
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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def update_qr_status_internal(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)


    # Node.js secret verify
    node_secret = request.headers.get(
        "X-Node-Secret"
    )
    print("EXPECTED NODE SECRET:", settings.NODE_SECRET)
    print(
        "RECEIVED NODE SECRET:",
        request.headers.get("X-Node-Secret")
    )
    print(
    "RECEIVED NODE SECRET:",
    node_secret
    )

    print(
        "RECEIVED SECRET LENGTH:",
        len(node_secret or "")
    )
    print("================================")

    if node_secret != settings.NODE_SECRET:

        return JsonResponse({
            "success": False,
            "message": "Unauthorized"
        }, status=401)


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
            "message": "Session ID is required"
        }, status=400)


    try:

        qr_session = QRSession.objects.get(
            session_id=session_id
        )

    except QRSession.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "QR session not found"
        }, status=404)


    print("\n========== UPDATE QR STATUS ==========")
    print("SESSION ID:", session_id)
    print("CONNECTED:", connected)
    print("OLD CONNECT:", qr_session.connect)

    qr_session.connect = connected

    qr_session.save(
        update_fields=[
            "connect",
            "updated_at"
        ]
    )

    print("NEW CONNECT:", qr_session.connect)
    print("======================================")

    return JsonResponse({
        "success": True,
        "connected": qr_session.connect,
        "sessionId": qr_session.session_id
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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import requests
from django.utils import timezone

@csrf_exempt
def send_message(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=405)


    # =================================================
    # READ REQUEST DATA
    # =================================================

    try:

        if request.content_type == "application/json":

            data = json.loads(request.body)

        else:

            data = request.POST.dict()

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return JsonResponse({

            "success": False,

            "message": "Invalid JSON"

        }, status=400)


    api_key = data.get("api_key")
    sender = data.get("sender")
    number = data.get("number")
    message = data.get("message")
    footer = data.get("footer", "")


    # =================================================
    # VALIDATION
    # =================================================

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


    # =================================================
    # CLEAN NUMBERS
    # =================================================

    clean_sender = clean_number(sender)

    clean_number_value = clean_number(number)


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

            "message": "Invalid API key"

        }, status=401)


    user = api_key_obj.user


    # =================================================
    # CHECK USER SUBSCRIPTION + MESSAGE LIMIT
    # =================================================

    now = timezone.now()

    user_subscription = (
        UserSubscription.objects
        .filter(
            user=user,
            active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        .select_related("plan")
        .first()
    )

    print("\n========== SUBSCRIPTION DEBUG ==========")
    print("USER ID:", user.id)
    print("CURRENT TIME:", now)
    print("SUBSCRIPTION:", user_subscription)

    if not user_subscription:

        print("❌ NO ACTIVE SUBSCRIPTION")

        return JsonResponse({
            "success": False,
            "message": "No active subscription found"
        }, status=403)


    plan = user_subscription.plan

    messages_used = user_subscription.messages_used

    messages_limit = plan.messages_limit


    print("\n========== SUBSCRIPTION CHECK ==========")

    print("USER:", user.id)

    print("PLAN:", plan.plan_name)

    print("MESSAGES USED:", messages_used)

    print("MESSAGE LIMIT:", messages_limit)


    # =================================================
    # CHECK MESSAGE LIMIT
    # =================================================

    # None = Unlimited
    if messages_limit is not None:

        if messages_used >= messages_limit:

            return JsonResponse({

                "success": False,

                "message":
                    "Message limit reached. Please upgrade your plan.",

                "plan":
                    plan.plan_name,

                "messages_used":
                    messages_used,

                "messages_limit":
                    messages_limit

            }, status=403)


    # =================================================
    # FIND CONNECTED WHATSAPP SESSION
    # =================================================

    qr_session = (
        QRSession.objects
        .filter(

            user=user,

            phone_number=clean_sender[-10:],

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
        # "https://sendwapiclone-2.onrender.com/api/whatsapp/send-message"
        "http://localhost:3001/api/whatsapp/send-message"
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

    message_id = result.get("messageId")


    if not message_id:

        return JsonResponse({

            "success": False,

            "message":
                "Message sent but messageId was not returned",

            "response":
                result

        }, status=500)


    # =================================================
    # SAVE MESSAGE HISTORY
    # =================================================

    Message_record.objects.create(

        user=user,

        sender_number=clean_sender,

        receiver_number=clean_number_value,

        message_content=message,

        msgID=message_id,

        status="sent"

    )


    # =================================================
    # INCREMENT MESSAGE USAGE
    # =================================================

    user_subscription.messages_used += 1

    user_subscription.save(
        update_fields=[
            "messages_used",
            "updated_at"
        ]
    )


    new_messages_used = (
        user_subscription.messages_used
    )


    print(
        "MESSAGE USAGE UPDATED:",
        new_messages_used
    )


    # =================================================
    # FINAL RESPONSE
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

        "messages_used":
            new_messages_used,

        "messages_limit":
            messages_limit,

        "remaining_messages":
            (
                None
                if messages_limit is None
                else messages_limit - new_messages_used
            ),

        "response":
            result

    })

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Message_record


@login_required
def message_history(request):

    if request.method != "GET":
        return JsonResponse({
            "success": False,
            "message": "GET request required"
        }, status=405)

    records = Message_record.objects.filter(
        user=request.user
    ).order_by("-sent_at")

    history = []

    for record in records:

        history.append({
            "id": record.id,
            "sender": record.sender_number,
            "receiver": record.receiver_number,
            "message": record.message_content,
            "messageId": record.msgID,
            "status": record.status,
            "sentAt": record.sent_at.isoformat()
        })

    return JsonResponse({
        "success": True,
        "messages": history
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
@login_required
def get_session_status(request, session_id):

    try:

        qr_session = QRSession.objects.get(
            session_id=session_id,
            user=request.user
        )

    except QRSession.DoesNotExist:

        return JsonResponse({

            "success": False,

            "message":
                "QR session not found"

        }, status=404)


    return JsonResponse({

        "success": True,

        "connected":
            qr_session.connect,

        "sessionId":
            qr_session.session_id,

        "phoneNumber":
            qr_session.phone_number,

        "qrImage":(
            qr_session.qr_code_url
            if qr_session.connect is False
            else None
        )
    })
@login_required
def subscription_plans(request):
    subscription_plans = subscription.objects.all().order_by("-created_at")
    
    context = {
        "subscription_plans": subscription_plans
    }
    return render(
        request,
        "user/subscription.html",
        context
    )