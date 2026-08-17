from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from apps.accounts.models import User
from apps.messaging.models import Message_record
from django.db.models import Count, Q
from .models import subscription , UserSubscription


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

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.accounts.models import User

from .models import subscription



@user_passes_test(is_super_admin)
def users(request):

    # ==========================================
    # ASSIGN PLAN
    # ==========================================

    if request.method == "POST":

        action = request.POST.get("action")
        user_id = request.POST.get("user_id")

        if not user_id:
            messages.error(request, "User not found.")
            return redirect("superadmin:users")

        try:
            user = User.objects.get(
                id=user_id,
                role="user"
            )

            # ==============================
            # UNASSIGN PLAN
            # ==============================

            if action == "unassign":

                try:
                    user_subscription = UserSubscription.objects.get(
                        user=user
                    )

                    user_subscription.delete()

                    messages.success(
                        request,
                        f"Plan unassigned from {user.email} successfully."
                    )

                except UserSubscription.DoesNotExist:

                    messages.warning(
                        request,
                        "This user does not have any subscription."
                    )

                return redirect("superadmin:users")


            # ==============================
            # ASSIGN PLAN
            # ==============================

            plan_id = request.POST.get("plan_id")

            if not plan_id:
                messages.error(
                    request,
                    "Please select a plan."
                )
                return redirect("superadmin:users")

            plan = subscription.objects.get(
                id=plan_id
            )

            assign_plan(user, plan)

            messages.success(
                request,
                f"{plan.plan_name} assigned to {user.email}."
            )

        except User.DoesNotExist:

            messages.error(
                request,
                "User not found."
            )

        except subscription.DoesNotExist:

            messages.error(
                request,
                "Selected plan not found."
            )

        return redirect("superadmin:users")


    # ==========================================
    # USERS
    # ==========================================

    now = timezone.now()

    total_users = (
        User.objects
        .filter(role="user")
        .select_related(
            "user_subscription",
            "user_subscription__plan"
        )
        .annotate(
            message_sent=Count(
                "message_records",
                filter=Q(
                    message_records__status="sent"
                )
            )
        )
        .order_by("-created_at")[:10]
    )

    plans = subscription.objects.all()

    message_sent = Message_record.objects.filter(
        status="sent"
    ).count()

    context = {
        "total_users": total_users,
        "message_sent": message_sent,
        "now": now,
        "plans": plans,
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
def history(request):

    return render(
        request,
        "admin/history.html"
    )

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from .models import subscription


@user_passes_test(is_super_admin)
def subscriptions(request):

    if request.method == "POST":

        plan_name = request.POST.get("plan_name")
        price = request.POST.get("price")
        messages_limit = request.POST.get("messages_limit")
        duration_days = request.POST.get("duration_days")

        trial_package = (
            request.POST.get("trial_package") == "on"
        )

        # Empty message limit = unlimited
        if messages_limit == "":
            messages_limit = None

        # If this is a trial/default plan,
        # remove default status from existing plans
        if trial_package:
            subscription.objects.filter(
                is_default=True
            ).update(
                is_default=False
            )

        # Create new plan
        plan = subscription.objects.create(
            user=request.user,
            plan_name=plan_name,
            price=price,
            messages_limit=messages_limit,
            duration_days=duration_days,
            trial_package=trial_package,
            is_default=trial_package
        )

        messages.success(
            request,
            "Subscription plan created successfully."
        )

        return redirect(
            "superadmin:subscriptions"
        )

    plans = subscription.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "admin/subscriptions.html",
        {
            "plans": plans
        }
    )

@user_passes_test(is_super_admin)
def edit_plan(request, plan_id):

    plan = get_object_or_404(
        subscription,
        id=plan_id
    )

    if request.method == "POST":

        plan.plan_name = request.POST.get(
            "plan_name"
        )

        plan.price = request.POST.get(
            "price"
        )

        messages_limit = request.POST.get(
            "messages_limit"
        )

        if messages_limit == "":
            messages_limit = None

        plan.messages_limit = messages_limit

        plan.duration_days = request.POST.get(
            "duration_days"
        )

        plan.trial_package = (
            request.POST.get("trial_package")
            == "on"
        )

        plan.save()

        messages.success(
            request,
            "Subscription plan updated successfully."
        )

        return redirect(
            "superadmin:subscriptions"
        )

    return render(
        request,
        "admin/edit_plan.html",
        {
            "plan": plan
        }
    )
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

@user_passes_test(is_super_admin)
def delete_plan(request, plan_id):

    plan = get_object_or_404(
        subscription,
        id=plan_id
    )

    if request.method == "POST":

        assigned_users = UserSubscription.objects.filter(
            plan=plan
        ).count()

        if assigned_users > 0:

            messages.error(
                request,
                f"Cannot delete '{plan.plan_name}'. "
                f"This plan is assigned to {assigned_users} user(s). "
                f"Unassign or change the plan first."
            )

            return redirect(
                "superadmin:subscriptions"
            )

        plan.delete()

        messages.success(
            request,
            "Subscription plan deleted successfully."
        )

        return redirect(
            "superadmin:subscriptions"
        )

    return render(
        request,
        "admin/subscription.html",
        {
            "plan": plan
        }
    )
from datetime import timedelta
from django.utils import timezone


from datetime import timedelta
from django.utils import timezone


def assign_plan(user, plan):

    start_date = timezone.now()

    end_date = (
        start_date +
        timedelta(days=plan.duration_days)
    )

    UserSubscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "start_date": start_date,
            "end_date": end_date,
            "messages_used": 0,
            "active": True,
        }
    )