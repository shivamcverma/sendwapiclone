from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from apps.accounts.models import User
from apps.messaging.models import Message_record
from django.db.models import Count, Q

def is_super_admin(user):

    return (
        user.is_authenticated
        and user.role == "admin"
    )


@user_passes_test(is_super_admin)
def dashboard(request):

    # =========================================
    # TOTAL USERS
    # =========================================

    total_users = User.objects.filter(
        role="user"
    ).count()

    sent_messages = Message_record.objects.filter(
        status="sent"
    ).count()

    total_messages = Message_record.objects.count()

    recent_users = (
        User.objects
        .filter(
            role="user"
        )
        .order_by(
            "-created_at"
        )[:10]
    )

    recent_activities = []

    # Recent messages
    recent_messages = (
        Message_record.objects
        .filter(status="sent")
        .order_by("-sent_at")[:5]
    )

    for message in recent_messages:

        recent_activities.append({
            "timestamp": message.sent_at,
            "message": (
                f"Message sent to "
                f"{message.receiver_number}"
            )
        })
        recent_registered_users = (
        User.objects
        .filter(role="user")
        .order_by("-created_at")[:5]
    )

    for user in recent_registered_users:

        recent_activities.append({
            "timestamp": user.created_at,
            "message": (
                f"New user registered: "
                f"{user.email}"
            )
        })
        recent_activities.sort(
        key=lambda x: x["timestamp"],
        reverse=True
    )

    # Only latest 10
    recent_activities = recent_activities[:10]

    context = {
        "total_users":
            total_users,
        "sent_messages":
            sent_messages,
        "recent_users":
            recent_users,
        "total_messages":
            total_messages,
        "recent_activities":
            recent_activities
    }
    return render(
        request,
        "admin/dashboard.html",
        context
    )

@user_passes_test(is_super_admin)
def users(request):
    total_users = (
        User.objects.filter(role="user").annotate(
            message_sent=Count(
                "message_records",
                filter=Q(
                    message_records__status="sent"
                )
            )
        )
        .order_by("-created_at")[:10]
    )
    for user in total_users:

        print("\n==============================")
        print("USER:", user.email)

        messages = user.message_records.all()

        print("TOTAL RECORDS:", messages.count())
        for user in total_users:
            print(
                "USER ID:", user.id,
                "| EMAIL:", user.email,
                "| MESSAGE COUNT:", user.message_records.count()
            )
    message_sent = Message_record.objects.count()
    context = {
        "total_users": total_users,
        "message_sent": message_sent
    }

    return render(
        request,
        "admin/users.html",
        context
    )


@user_passes_test(is_super_admin)
def user_detail(request, user_id):

    return render(
        request,
        "admin/user_detail.html"
    )


@user_passes_test(is_super_admin)
def subscriptions(request):

    return render(
        request,
        "admin/subscriptions.html"
    )


@user_passes_test(is_super_admin)
def history(request):

    return render(
        request,
        "admin/history.html"
    )